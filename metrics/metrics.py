"""
Metrics Tracker for the Agentic Code Documentation Generator.

Tracks:
  1. Documentation generation time (seconds)
  2. Tool call count per run
  3. Successful run rate (successes / total)
"""

import time
from dataclasses import dataclass, field


@dataclass
class RunMetrics:
    """Metrics for a single run."""
    run_id: str = ""
    generation_time: float = 0.0
    tool_call_count: int = 0
    success: bool = False


class MetricsTracker:
    """
    Tracks and aggregates metrics across multiple pipeline runs.
    """

    def __init__(self):
        self.runs: list[RunMetrics] = []
        self._current_run: RunMetrics | None = None
        self._timer_start: float | None = None

    def start_run(self, run_id: str):
        """Begin tracking a new run."""
        self._current_run = RunMetrics(run_id=run_id)
        self._timer_start = None

    def start_timer(self):
        """Start the generation timer."""
        self._timer_start = time.time()

    def stop_timer(self):
        """Stop the generation timer and record elapsed time."""
        if self._timer_start and self._current_run:
            self._current_run.generation_time = round(time.time() - self._timer_start, 4)
            self._timer_start = None

    def record_tool_call(self):
        """Increment the tool call counter for the current run."""
        if self._current_run:
            self._current_run.tool_call_count += 1

    def record_run_result(self, success: bool):
        """Record whether the current run succeeded and finalize it."""
        if self._current_run:
            self._current_run.success = success
            self.runs.append(self._current_run)
            self._current_run = None

    def get_summary(self) -> dict:
        """
        Get aggregated metrics summary.
        
        Returns:
            Dictionary with avg_generation_time, total_tool_calls,
            avg_tool_calls, successful_runs, total_runs, success_rate.
        """
        if not self.runs:
            return {
                "avg_generation_time": 0.0,
                "total_tool_calls": 0,
                "avg_tool_calls": 0.0,
                "successful_runs": 0,
                "total_runs": 0,
                "success_rate": 0.0,
            }

        total = len(self.runs)
        successes = sum(1 for r in self.runs if r.success)
        total_time = sum(r.generation_time for r in self.runs)
        total_tools = sum(r.tool_call_count for r in self.runs)

        return {
            "avg_generation_time": round(total_time / total, 4),
            "total_tool_calls": total_tools,
            "avg_tool_calls": round(total_tools / total, 2),
            "successful_runs": successes,
            "total_runs": total,
            "success_rate": round(successes / total * 100, 2),
        }

    def get_run_history(self) -> list[dict]:
        """Return metrics for each individual run."""
        return [
            {
                "run_id": r.run_id,
                "generation_time": r.generation_time,
                "tool_call_count": r.tool_call_count,
                "success": r.success,
            }
            for r in self.runs
        ]
