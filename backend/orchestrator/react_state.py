"""ReAct Agent State Management."""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field


@dataclass
class AgentThought:
    """Represents a thought in the ReAct loop."""
    step: int
    content: str
    timestamp: float = field(default_factory=lambda: __import__('time').time())


@dataclass
class AgentAction:
    """Represents an action to be executed."""
    step: int
    function_id: str
    function_name: str
    parameters: Dict[str, Any]
    reasoning: str


@dataclass
class AgentObservation:
    """Represents the result of an action."""
    step: int
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


@dataclass
class AgentReflection:
    """Represents reflection on the current state."""
    step: int
    content: str
    quality_score: float  # 0.0 to 1.0
    should_continue: bool
    needs_clarification: bool = False


class ReactAgentState(TypedDict, total=False):
    """State for ReAct Agent with memory."""
    
    # User context
    user_id: str
    conversation_id: Optional[str]
    
    # Current query
    query: str
    
    # ReAct loop components
    thoughts: List[AgentThought]
    actions: List[AgentAction]
    observations: List[AgentObservation]
    reflections: List[AgentReflection]
    
    # Current iteration
    current_step: int
    max_steps: int
    
    # RAG context
    retrieved_functions: List[Dict[str, Any]]
    
    # Memory context
    user_profile: Dict[str, Any]
    conversation_history: List[Dict[str, str]]
    
    # Final output
    final_answer: Optional[str]
    requires_clarification: bool
    clarification_question: Optional[str]
    
    # Metadata
    total_execution_time_ms: float
    tokens_used: int
    api_calls_made: int
    
    # Status
    status: Literal["thinking", "acting", "observing", "reflecting", "completed", "failed"]
    error: Optional[str]


def create_initial_state(
    user_id: str,
    query: str,
    conversation_id: Optional[str] = None,
    max_steps: int = 5
) -> ReactAgentState:
    """Create initial ReAct agent state."""
    return ReactAgentState(
        user_id=user_id,
        conversation_id=conversation_id,
        query=query,
        thoughts=[],
        actions=[],
        observations=[],
        reflections=[],
        current_step=0,
        max_steps=max_steps,
        retrieved_functions=[],
        user_profile={},
        conversation_history=[],
        final_answer=None,
        requires_clarification=False,
        clarification_question=None,
        total_execution_time_ms=0.0,
        tokens_used=0,
        api_calls_made=0,
        status="thinking",
        error=None
    )
