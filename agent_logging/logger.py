"""
JSONL Logger for the Agentic Code Documentation Generator.

Logs all agent activity, state transitions, tool calls, and run metadata
to a JSONL file for full observability and reproducibility.
"""

import json
import os
import uuid
from datetime import datetime, timezone


class AgentLogger:
    """
    Logger that writes structured JSONL entries for every agent action.
    
    Each entry includes: run_id, agent_name, state, tool info,
    state transitions, and timestamps.
    """

    def __init__(self, log_file: str = None):
        if log_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(base_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            self.log_file = os.path.join(log_dir, "logs.jsonl")
        else:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            self.log_file = log_file

        self.run_id: str = ""
        self.agent_name: str = "doc_agent"
        self._entries: list[dict] = []

    def _timestamp(self) -> str:
        """Return current UTC timestamp as ISO string."""
        return datetime.now(timezone.utc).isoformat()

    def _write_entry(self, entry: dict):
        """Write a single entry to the JSONL file and in-memory list."""
        entry["timestamp"] = self._timestamp()
        entry["run_id"] = self.run_id
        entry["agent_name"] = self.agent_name
        self._entries.append(entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def log_run_start(self, run_id: str = None, seed: int = None):
        """Log the start of a new pipeline run."""
        self.run_id = run_id or str(uuid.uuid4())[:8]
        self._entries = []
        self._write_entry({
            "event_type": "run_start",
            "state": "START",
            "seed": seed,
        })

    def log_run_end(self, success: bool, error: str = None):
        """Log the end of a pipeline run."""
        self._write_entry({
            "event_type": "run_end",
            "state": "END" if success else "ERROR",
            "success": success,
            "error": error,
        })

    def log_state_transition(self, previous_state: str, event: str, next_state: str):
        """Log a state machine transition."""
        self._write_entry({
            "event_type": "state_transition",
            "state": next_state,
            "transition": f"{previous_state} → {event} → {next_state}",
            "previous_state": previous_state,
            "next_state": next_state,
            "trigger_event": event,
        })

    def log_tool_call(self, tool_name: str, tool_input: dict, tool_output: dict, state: str):
        """Log a tool invocation with its input and output."""
        self._write_entry({
            "event_type": "tool_call",
            "state": state,
            "tool": tool_name,
            "input": tool_input,
            "output": tool_output,
        })

    def log_agent_message(self, message: str, state: str):
        """Log an agent message or decision."""
        self._write_entry({
            "event_type": "agent_message",
            "state": state,
            "message": message,
        })

    def get_entries(self) -> list[dict]:
        """Return all log entries for the current run."""
        return list(self._entries)

    def get_entries_by_type(self, event_type: str) -> list[dict]:
        """Return log entries filtered by event type."""
        return [e for e in self._entries if e.get("event_type") == event_type]
