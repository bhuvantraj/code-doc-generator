"""
State Machine for the Agentic Code Documentation Generator.

Defines states and valid transitions for the agent workflow.
All transitions are logged as: previous_state → event → next_state
"""

from enum import Enum
from typing import Optional


class AgentState(Enum):
    """Enumeration of all possible agent states."""
    START = "START"
    READ_CODE = "READ_CODE"
    PARSE_CODE = "PARSE_CODE"
    GENERATE_DOCUMENTATION = "GENERATE_DOCUMENTATION"
    DISPLAY_RESULT = "DISPLAY_RESULT"
    END = "END"
    ERROR = "ERROR"


# Valid transitions: (current_state, event) → next_state
TRANSITIONS = {
    (AgentState.START, "begin"): AgentState.READ_CODE,
    (AgentState.READ_CODE, "code_read"): AgentState.PARSE_CODE,
    (AgentState.PARSE_CODE, "code_parsed"): AgentState.GENERATE_DOCUMENTATION,
    (AgentState.GENERATE_DOCUMENTATION, "docs_generated"): AgentState.DISPLAY_RESULT,
    (AgentState.DISPLAY_RESULT, "displayed"): AgentState.END,
    # Error transitions from any processing state
    (AgentState.READ_CODE, "error"): AgentState.ERROR,
    (AgentState.PARSE_CODE, "error"): AgentState.ERROR,
    (AgentState.GENERATE_DOCUMENTATION, "error"): AgentState.ERROR,
    (AgentState.DISPLAY_RESULT, "error"): AgentState.ERROR,
    # Recovery
    (AgentState.ERROR, "reset"): AgentState.START,
    (AgentState.END, "reset"): AgentState.START,
}


class StateMachine:
    """
    State machine that manages agent workflow transitions.
    
    Tracks current state and history of all transitions.
    Each transition is validated against allowed transitions.
    """

    def __init__(self, logger=None):
        self.current_state: AgentState = AgentState.START
        self.history: list[dict] = []
        self.logger = logger

    def transition(self, event: str) -> AgentState:
        """
        Attempt a state transition given an event.
        
        Args:
            event: The event triggering the transition.
            
        Returns:
            The new state after transition.
            
        Raises:
            ValueError: If the transition is not allowed.
        """
        key = (self.current_state, event)
        if key not in TRANSITIONS:
            raise ValueError(
                f"Invalid transition: {self.current_state.value} --[{event}]--> ???  "
                f"(no rule for this state+event)"
            )

        previous_state = self.current_state
        next_state = TRANSITIONS[key]
        self.current_state = next_state

        transition_record = {
            "previous_state": previous_state.value,
            "event": event,
            "next_state": next_state.value,
        }
        self.history.append(transition_record)

        # Log the transition
        if self.logger:
            self.logger.log_state_transition(
                previous_state=previous_state.value,
                event=event,
                next_state=next_state.value,
            )

        return next_state

    def reset(self):
        """Reset the state machine to START."""
        if self.current_state in (AgentState.END, AgentState.ERROR):
            self.transition("reset")
        else:
            self.current_state = AgentState.START
            self.history = []

    def get_current_state(self) -> str:
        """Return the current state as a string."""
        return self.current_state.value

    def get_history(self) -> list[dict]:
        """Return the full transition history."""
        return list(self.history)
