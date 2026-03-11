"""
Main Pipeline -- Orchestrates the full agentic documentation generation workflow.

Flow: START -> READ_CODE -> PARSE_CODE -> GENERATE_DOCUMENTATION -> DISPLAY_RESULT -> END

Every step is logged, metrics are tracked, and the state machine enforces valid transitions.
"""

import asyncio
import os
import sys
import uuid

# Disable pydantic AI rich spinner completely globally to prevent terminal garbling
os.environ["PYDANTIC_AI_CLI_PROGRESS"] = "false"
os.environ["PYDANTIC_AI_NO_SPINNER"] = "1"

# Ensure project root is on the path so subpackage imports work
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from state_machine.states import StateMachine, AgentState  # noqa: E402
from agent_logging.logger import AgentLogger  # noqa: E402
from tools.parse_code import parse_code  # noqa: E402
from tools.generate_docs import generate_docs_from_parsed  # noqa: E402
from agents.doc_agent import generate_descriptions  # noqa: E402
from metrics.metrics import MetricsTracker  # noqa: E402


async def run_pipeline(
    source_code: str,
    language: str,
    seed: int = 42,
    run_id: str = None,
    logger: AgentLogger = None,
    metrics: MetricsTracker = None,
    on_state_change=None,
    on_tool_call=None,
    on_message=None,
) -> dict:
    """
    Execute the full documentation generation pipeline.

    Args:
        source_code: The source code to document.
        language: Programming language of the source code.
        seed: Seed for reproducibility.
        run_id: Optional run identifier.
        logger: Optional AgentLogger instance.
        metrics: Optional MetricsTracker instance.
        on_state_change: Optional callback(previous, event, next) for UI updates.
        on_tool_call: Optional callback(tool_name, input, output) for UI updates.
        on_message: Optional callback(message) for UI updates.

    Returns:
        Dictionary with keys: run_id, documentation, parsed_structure,
        descriptions, state_history, success, error.
    """
    # Initialize
    if run_id is None:
        run_id = str(uuid.uuid4())[:8]
    if logger is None:
        logger = AgentLogger()
    if metrics is None:
        metrics = MetricsTracker()

    sm = StateMachine(logger=logger)
    logger.log_run_start(run_id=run_id, seed=seed)
    metrics.start_run(run_id)
    metrics.start_timer()

    result = {
        "run_id": run_id,
        "documentation": "",
        "parsed_structure": {},
        "descriptions": {},
        "state_history": [],
        "success": False,
        "error": None,
    }

    def _notify_state(prev, event, next_s):
        if on_state_change:
            on_state_change(prev, event, next_s)

    def _notify_tool(name, inp, out):
        if on_tool_call:
            on_tool_call(name, inp, out)

    def _notify_msg(msg):
        if on_message:
            on_message(msg)
        logger.log_agent_message(msg, sm.get_current_state())

    try:
        # -- 1. READ_CODE ---------------------------------------------------
        _notify_msg("Starting documentation pipeline...")
        sm.transition("begin")
        _notify_state("START", "begin", "READ_CODE")
        _notify_msg(f"Reading {language} source code ({len(source_code)} chars)...")

        if not source_code.strip():
            _notify_msg("Warning: Source code is empty.")

        # -- 2. PARSE_CODE --------------------------------------------------
        sm.transition("code_read")
        _notify_state("READ_CODE", "code_read", "PARSE_CODE")
        _notify_msg("Calling parse_code tool...")

        parsed = parse_code(source_code, language)
        metrics.record_tool_call()

        code_preview = source_code[:200] + ("..." if len(source_code) > 200 else "")
        logger.log_tool_call(
            tool_name="parse_code",
            tool_input={"source_code": code_preview, "language": language},
            tool_output=parsed,
            state=sm.get_current_state(),
        )
        _notify_tool("parse_code", {"language": language, "code_length": len(source_code)}, parsed)
        _notify_msg(
            f"Parsed: {len(parsed.get('functions', []))} functions, "
            f"{len(parsed.get('classes', []))} classes"
        )

        result["parsed_structure"] = parsed

        # -- 3. GENERATE_DOCUMENTATION --------------------------------------
        sm.transition("code_parsed")
        _notify_state("PARSE_CODE", "code_parsed", "GENERATE_DOCUMENTATION")

        # Get LLM descriptions
        _notify_msg("Calling doc_agent for descriptions...")
        descriptions = await generate_descriptions(parsed, seed=seed)
        metrics.record_tool_call()

        logger.log_tool_call(
            tool_name="generate_descriptions",
            tool_input={"parsed_structure": parsed, "seed": seed},
            tool_output=descriptions,
            state=sm.get_current_state(),
        )
        _notify_tool(
            "generate_descriptions",
            {"parsed_keys": list(parsed.keys()), "seed": seed},
            descriptions,
        )
        result["descriptions"] = descriptions

        # Generate final documentation
        _notify_msg("Calling generate_docs tool...")
        documentation = generate_docs_from_parsed(parsed, descriptions)
        metrics.record_tool_call()

        logger.log_tool_call(
            tool_name="generate_docs",
            tool_input={
                "parsed_structure_keys": list(parsed.keys()),
                "descriptions_count": len(descriptions),
            },
            tool_output={"documentation_length": len(documentation)},
            state=sm.get_current_state(),
        )
        _notify_tool(
            "generate_docs",
            {"descriptions_count": len(descriptions)},
            {"doc_length": len(documentation)},
        )

        result["documentation"] = documentation
        _notify_msg(f"Documentation generated ({len(documentation)} chars)")

        # -- 4. DISPLAY_RESULT ----------------------------------------------
        sm.transition("docs_generated")
        _notify_state("GENERATE_DOCUMENTATION", "docs_generated", "DISPLAY_RESULT")
        _notify_msg("Documentation ready for display.")

        # -- 5. END ---------------------------------------------------------
        sm.transition("displayed")
        _notify_state("DISPLAY_RESULT", "displayed", "END")
        _notify_msg("Pipeline completed successfully.")

        result["success"] = True

    except Exception as e:
        result["error"] = str(e)
        _notify_msg(f"Error: {e}")
        try:
            sm.transition("error")
        except ValueError:
            pass
        _notify_state(sm.get_current_state(), "error", "ERROR")

    # Finalize
    metrics.stop_timer()
    metrics.record_run_result(result["success"])
    logger.log_run_end(success=result["success"], error=result.get("error"))
    result["state_history"] = sm.get_history()

    return result


def run_pipeline_sync(
    source_code: str,
    language: str,
    seed: int = 42,
    run_id: str = None,
    logger: AgentLogger = None,
    metrics: MetricsTracker = None,
) -> dict:
    """Synchronous wrapper for run_pipeline."""
    return asyncio.run(
        run_pipeline(
            source_code=source_code,
            language=language,
            seed=seed,
            run_id=run_id,
            logger=logger,
            metrics=metrics,
        )
    )


if __name__ == "__main__":
    # Quick test
    test_code = '''
def add(a, b):
    """Adds two numbers."""
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
'''
    result = run_pipeline_sync(test_code, "python", seed=42)
    print("=== State History ===")
    for t in result["state_history"]:
        print(f"  {t['previous_state']} -> {t['event']} -> {t['next_state']}")
    print(f"\n=== Success: {result['success']} ===")
    print(f"\n=== Documentation ===\n{result['documentation']}")
