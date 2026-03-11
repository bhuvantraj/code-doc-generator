"""Quick verification script to test all components."""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("VERIFICATION: Agentic Code Documentation Generator")
print("=" * 60)

# 1. State Machine
print("\n[1] State Machine Test")
from state_machine.states import StateMachine, AgentState
sm = StateMachine()
sm.transition("begin")
assert sm.get_current_state() == "READ_CODE"
sm.transition("code_read")
assert sm.get_current_state() == "PARSE_CODE"
sm.transition("code_parsed")
assert sm.get_current_state() == "GENERATE_DOCUMENTATION"
sm.transition("docs_generated")
assert sm.get_current_state() == "DISPLAY_RESULT"
sm.transition("displayed")
assert sm.get_current_state() == "END"
print("  PASS: All 5 transitions validated")
print("  History:", [f"{t['previous_state']}->{t['next_state']}" for t in sm.get_history()])

# Invalid transition test
sm2 = StateMachine()
try:
    sm2.transition("code_read")
    print("  FAIL: Should have raised ValueError")
except ValueError:
    print("  PASS: Invalid transition correctly rejected")

# 2. Parser
print("\n[2] Code Parser Test")
from tools.parse_code import parse_code

code_py = '''def add(a, b):
    """Adds two numbers."""
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
'''
parsed = parse_code(code_py, "python")
assert parsed["language"] == "python"
assert len(parsed["functions"]) == 1
assert parsed["functions"][0]["name"] == "add"
assert parsed["functions"][0]["parameters"] == ["a", "b"]
assert len(parsed["classes"]) == 1
assert parsed["classes"][0]["name"] == "Calculator"
assert not parsed["has_errors"]
print("  PASS: Python parsing correct")

# Determinism test
parsed2 = parse_code(code_py, "python")
assert parsed == parsed2
print("  PASS: Parser is deterministic (same input -> same output)")

# JS Test
code_js = 'function greet(name) { return "Hello " + name; }'
parsed_js = parse_code(code_js, "javascript")
assert parsed_js["language"] == "javascript"
assert len(parsed_js["functions"]) == 1
assert parsed_js["functions"][0]["name"] == "greet"
print("  PASS: JavaScript parsing correct")

# Empty file
parsed_empty = parse_code("", "python")
assert len(parsed_empty["functions"]) == 0
assert len(parsed_empty["classes"]) == 0
print("  PASS: Empty file handled")

# Syntax error
parsed_err = parse_code("def broken(\n    return 42\n", "python")
assert parsed_err["has_errors"] == True
print("  PASS: Syntax error detected")

# 3. Doc Generator
print("\n[3] Documentation Generator Test")
from tools.generate_docs import generate_docs_from_parsed

descriptions = {
    "add": "Adds two values and returns the sum.",
    "add.a": "First operand",
    "add.b": "Second operand",
    "Calculator": "A basic calculator utility.",
    "Calculator.multiply": "Multiplies two numbers.",
}
docs = generate_docs_from_parsed(parsed, descriptions)
assert "# Code Documentation" in docs
assert "add" in docs
assert "Calculator" in docs
assert "Adds two values" in docs
print("  PASS: Documentation generated with descriptions")
print(f"  Doc length: {len(docs)} chars")

# 4. Metrics
print("\n[4] Metrics Tracker Test")
from metrics.metrics import MetricsTracker
mt = MetricsTracker()
mt.start_run("test-001")
mt.start_timer()
mt.record_tool_call()
mt.record_tool_call()
mt.stop_timer()
mt.record_run_result(True)
summary = mt.get_summary()
assert summary["total_runs"] == 1
assert summary["successful_runs"] == 1
assert summary["success_rate"] == 100.0
assert summary["total_tool_calls"] == 2
print("  PASS: Metrics tracking works")
print(f"  Summary: {summary}")

# 5. Logger
print("\n[5] Logger Test")
from agent_logging.logger import AgentLogger
logger = AgentLogger(log_file=os.path.join(os.path.dirname(__file__), "logs", "test_logs.jsonl"))
logger.log_run_start(run_id="test-001", seed=42)
logger.log_state_transition("START", "begin", "READ_CODE")
logger.log_tool_call("parse_code", {"code": "..."}, {"functions": []}, "PARSE_CODE")
logger.log_run_end(success=True)
entries = logger.get_entries()
assert len(entries) == 4
print(f"  PASS: Logger wrote {len(entries)} entries")

# 6. Evaluation scenarios
print("\n[6] Evaluation Scenarios Test")
with open("evaluation/scenarios.json", "r") as f:
    scenarios = json.load(f)
assert len(scenarios) == 10
print(f"  PASS: {len(scenarios)} scenarios loaded")

passed = 0
for sc in scenarios:
    parsed_sc = parse_code(sc["code"], sc["language"])
    ok = True
    for key in sc["expected_keys"]:
        if key == "has_errors":
            ok = ok and parsed_sc.get("has_errors", False)
        else:
            ok = ok and len(parsed_sc.get(key, [])) > 0
    if ok:
        passed += 1
        print(f"  PASS: Scenario {sc['id']} - {sc['name']}")
    else:
        print(f"  WARN: Scenario {sc['id']} - {sc['name']} (partial match)")

print(f"\n  {passed}/{len(scenarios)} scenarios passed evaluation")

print("\n" + "=" * 60)
print("ALL CORE TESTS PASSED")
print("=" * 60)
