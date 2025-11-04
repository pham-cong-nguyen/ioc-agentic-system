"""
Test orchestrator functionality
"""
import pytest
from backend.orchestrator.state import AgentState, ExecutionPlan, FunctionCall


def test_agent_state_initialization():
    """Test AgentState initialization"""
    state = AgentState(
        query="Test query",
        language="vi"
    )
    
    assert state.query == "Test query"
    assert state.language == "vi"
    assert state.parsed_intent is None
    assert state.execution_results == []


def test_execution_plan_creation():
    """Test ExecutionPlan creation"""
    function_calls = [
        FunctionCall(
            function_id="func1",
            name="Function 1",
            parameters={"param1": "value1"},
            order=0
        ),
        FunctionCall(
            function_id="func2",
            name="Function 2",
            parameters={"param2": "value2"},
            order=1
        )
    ]
    
    plan = ExecutionPlan(
        function_calls=function_calls,
        execution_mode="sequential",
        reasoning="Test reasoning"
    )
    
    assert len(plan.function_calls) == 2
    assert plan.execution_mode == "sequential"
    assert plan.reasoning == "Test reasoning"


@pytest.mark.asyncio
async def test_query_parsing():
    """Test query parsing (requires LLM API key)"""
    # This test requires actual LLM API key
    # Skip if not available
    pytest.skip("Requires LLM API key")


@pytest.mark.asyncio
async def test_function_search():
    """Test function search in registry"""
    # This test requires database connection
    # Skip if not available
    pytest.skip("Requires database connection")


def test_function_call_with_dependencies():
    """Test function call with dependencies"""
    func_call = FunctionCall(
        function_id="func2",
        name="Function 2",
        parameters={"param": "value"},
        depends_on=["func1"],
        order=1
    )
    
    assert func_call.depends_on == ["func1"]
    assert func_call.order == 1
