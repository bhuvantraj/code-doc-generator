"""
Pydantic AI Agent -- doc_agent

Drives the code documentation pipeline using Groq LLM (LLaMA model).
Registers parse_code and generate_docs as agent tools.
"""

import os
import json
import sys

from dotenv import load_dotenv
from pydantic_ai import Agent


# ── Load environment variables from .env ───────────────────────────────────
load_dotenv()

# Ensure GROQ_API_KEY is available
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found. Please set it in the .env file.")


# ── Model setup ────────────────────────────────────────────────────────────
# Use the model string format: "groq:model-name"
# pydantic-ai resolves the provider automatically
MODEL_NAME = "groq:llama-3.3-70b-versatile"


# ── Agent ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a code documentation agent. Your job is to analyze parsed code structures and generate clear, helpful descriptions for each function, class, and method.

When given a parsed code structure (JSON), produce a JSON object mapping each function/class/method name to a concise, helpful description.

Rules:
- For functions: describe what the function does based on its name, parameters, and any docstring.
- For classes: describe the purpose of the class.
- For methods: use the format "ClassName.method_name" as the key.
- For parameters: use the format "function_name.param_name" as the key.
- Keep descriptions concise (1-2 sentences).
- Return ONLY valid JSON, no markdown formatting.

Example input:
{
  "language": "python",
  "functions": [{"name": "add", "parameters": ["a", "b"]}],
  "classes": []
}

Example output:
{
  "add": "Adds two values together and returns the result.",
  "add.a": "The first value to add.",
  "add.b": "The second value to add."
}
"""


doc_agent = Agent(
    MODEL_NAME,
    system_prompt=SYSTEM_PROMPT,
)


async def generate_descriptions(parsed_structure: dict, seed: int = 42) -> dict:
    """
    Use the LLM agent to generate descriptions for parsed code elements.

    Args:
        parsed_structure: Output from parse_code tool.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary mapping names to descriptions.
    """

    prompt = (
        f"Generate descriptions for this parsed code structure. "
        f"Return ONLY a valid JSON object.\n\n"
        f"{json.dumps(parsed_structure, indent=2)}"
    )

    try:
        # Suppress Pydantic AI spinner on stderr
        original_stderr = sys.stderr
        with open(os.devnull, "w") as devnull:
            sys.stderr = devnull
            try:
                result = await doc_agent.run(
                    prompt,
                    model_settings={"seed": seed, "temperature": 0},
                )
            finally:
                sys.stderr = original_stderr

        # Parse the JSON response
        response_text = result.output.strip()

        # Clean possible markdown code fences
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            response_text = "\n".join(lines)

        descriptions = json.loads(response_text)
        return descriptions

    except json.JSONDecodeError:
        # If LLM response isn't valid JSON
        return {}

    except Exception as e:
        # Fallback in case of agent failure
        print(f"Agent error (will use template-only docs): {e}")
        return {}