"""
Enhanced Components for ReAct Agent
Implements critical improvements for production readiness
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


# =============================================================================
# PHASE 1: CRITICAL FIXES
# =============================================================================

class FunctionCall(BaseModel):
    """Structured function call with validation."""
    function_name: str = Field(..., description="Name of the function to call")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Function parameters")
    reasoning: str = Field(..., description="Why calling this function")
    
    @validator('function_name')
    def validate_function_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Function name cannot be empty")
        return v.strip()


class FunctionSchema(BaseModel):
    """Complete function schema."""
    function_id: str
    name: str
    description: str
    category: str
    parameters: Dict[str, Any]  # JSON Schema format
    returns: Dict[str, Any]
    examples: List[Dict[str, Any]] = []
    dependencies: List[str] = []
    rate_limit: Optional[str] = None
    error_handling: Optional[Dict[str, str]] = None


class EnhancedPromptBuilder:
    """Build detailed prompts with full function information."""
    
    @staticmethod
    def format_functions_detailed(functions: List[Dict[str, Any]]) -> str:
        """
        Format functions with COMPLETE information.
        
        Args:
            functions: List of function metadata from RAG
            
        Returns:
            Formatted string with all function details
        """
        if not functions:
            return "No functions available"
        
        formatted_parts = []
        
        for i, func in enumerate(functions, 1):
            # Basic info
            func_info = [
                f"\n{'='*60}",
                f"FUNCTION {i}: {func.get('name', 'Unknown')}",
                f"{'='*60}",
                f"ID: {func.get('function_id', 'N/A')}",
                f"Category: {func.get('category', 'general')}",
                f"\nDescription:",
                f"  {func.get('description', 'No description available')}",
            ]
            
            # Parameters section
            parameters = func.get('parameters', {})
            if parameters:
                func_info.append("\nPARAMETERS:")
                
                # Required parameters
                required = parameters.get('required', [])
                if required:
                    func_info.append("  Required:")
                    for param in required:
                        param_schema = parameters.get('properties', {}).get(param, {})
                        func_info.append(
                            f"    - {param} ({param_schema.get('type', 'any')}): "
                            f"{param_schema.get('description', 'No description')}"
                        )
                
                # Optional parameters
                all_params = parameters.get('properties', {})
                optional = [p for p in all_params if p not in required]
                if optional:
                    func_info.append("  Optional:")
                    for param in optional:
                        param_schema = all_params[param]
                        default = param_schema.get('default', 'N/A')
                        func_info.append(
                            f"    - {param} ({param_schema.get('type', 'any')}, "
                            f"default={default}): "
                            f"{param_schema.get('description', 'No description')}"
                        )
            else:
                func_info.append("\nPARAMETERS: None required")
            
            # Return type
            return_info = func.get('returns', {})
            if return_info:
                func_info.append(f"\nRETURNS: {return_info.get('type', 'object')}")
                if 'description' in return_info:
                    func_info.append(f"  {return_info['description']}")
            
            # Examples
            examples = func.get('examples', [])
            if examples:
                func_info.append("\nEXAMPLES:")
                for j, example in enumerate(examples[:2], 1):  # Show max 2 examples
                    func_info.append(f"  Example {j}:")
                    func_info.append(f"    Input: {example.get('input', {})}")
                    func_info.append(f"    Output: {example.get('output', 'N/A')}")
            
            # Dependencies
            deps = func.get('dependencies', [])
            if deps:
                func_info.append(f"\nDEPENDENCIES: {', '.join(deps)}")
                func_info.append("  (These functions should be called first)")
            
            # Rate limits
            rate_limit = func.get('rate_limit')
            if rate_limit:
                func_info.append(f"\nRATE LIMIT: {rate_limit}")
            
            formatted_parts.append("\n".join(func_info))
        
        return "\n\n".join(formatted_parts)


class ParameterValidator:
    """Validate function parameters against schema."""
    
    @staticmethod
    def validate_call(
        call: FunctionCall,
        function_schema: FunctionSchema
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a function call against its schema.
        
        Args:
            call: Function call to validate
            function_schema: Schema to validate against
            
        Returns:
            (is_valid, error_message)
        """
        params = call.parameters
        schema = function_schema.parameters
        
        # Check required parameters
        required = schema.get('required', [])
        for param in required:
            if param not in params:
                return False, f"Missing required parameter: {param}"
        
        # Check parameter types
        properties = schema.get('properties', {})
        for param, value in params.items():
            if param not in properties:
                return False, f"Unknown parameter: {param}"
            
            expected_type = properties[param].get('type')
            if not ParameterValidator._check_type(value, expected_type):
                return False, f"Invalid type for {param}: expected {expected_type}, got {type(value).__name__}"
            
            # Check constraints (min, max, pattern, etc.)
            if 'minimum' in properties[param] and value < properties[param]['minimum']:
                return False, f"{param} must be >= {properties[param]['minimum']}"
            
            if 'maximum' in properties[param] and value > properties[param]['maximum']:
                return False, f"{param} must be <= {properties[param]['maximum']}"
            
            if 'pattern' in properties[param]:
                import re
                if not re.match(properties[param]['pattern'], str(value)):
                    return False, f"{param} must match pattern {properties[param]['pattern']}"
        
        return True, None
    
    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_mapping = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict,
        }
        
        expected = type_mapping.get(expected_type)
        if not expected:
            return True  # Unknown type, skip validation
        
        return isinstance(value, expected)


class RetryExecutor:
    """Execute functions with retry logic and error handling."""
    
    def __init__(
        self,
        executor_service,
        max_retries: int = 3,
        retry_delays: List[float] = None
    ):
        self.executor = executor_service
        self.max_retries = max_retries
        self.retry_delays = retry_delays or [1, 2, 5]  # Exponential backoff
    
    async def execute_with_retry(
        self,
        function_id: str,
        parameters: Dict[str, Any],
        registry_service = None
    ) -> Dict[str, Any]:
        """
        Execute function with retry logic.
        
        Args:
            function_id: Function to execute
            parameters: Function parameters
            registry_service: Registry service
            
        Returns:
            Execution result
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Executing {function_id} (attempt {attempt + 1}/{self.max_retries})")
                
                result = await self.executor.execute_function(
                    function_id=function_id,
                    parameters=parameters,
                    registry_service=registry_service
                )
                
                # Success!
                return {
                    "success": True,
                    "data": result,
                    "attempts": attempt + 1
                }
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                
                logger.warning(f"Attempt {attempt + 1} failed: {error_type} - {str(e)}")
                
                # Check if we should retry
                if not self._should_retry(e):
                    logger.error(f"Non-retryable error: {error_type}")
                    break
                
                # Wait before retry (except last attempt)
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.info(f"Waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
        
        # All retries failed
        return {
            "success": False,
            "error": str(last_error),
            "error_type": type(last_error).__name__,
            "attempts": self.max_retries,
            "retry_suggested": self._should_retry(last_error)
        }
    
    @staticmethod
    def _should_retry(error: Exception) -> bool:
        """Determine if error is retryable."""
        # Retryable errors
        retryable = [
            'TimeoutError',
            'ConnectionError',
            'RateLimitError',
            'ServiceUnavailableError',
        ]
        
        # Non-retryable errors
        non_retryable = [
            'ValidationError',
            'AuthenticationError',
            'PermissionError',
            'ValueError',
            'KeyError',
        ]
        
        error_type = type(error).__name__
        
        if error_type in non_retryable:
            return False
        
        if error_type in retryable:
            return True
        
        # Default: retry unknown errors
        return True


# =============================================================================
# PHASE 2: ADVANCED FEATURES
# =============================================================================

@dataclass
class ExecutionStep:
    """Single step in execution plan."""
    id: str
    function_id: str
    function_name: str
    parameters: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    can_parallel_with: List[str] = field(default_factory=list)
    timeout: float = 30.0


class ExecutionPlan(BaseModel):
    """Multi-step execution plan."""
    steps: List[ExecutionStep]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_next_steps(self, completed: List[str]) -> List[ExecutionStep]:
        """
        Get next executable steps based on dependencies.
        
        Args:
            completed: List of completed step IDs
            
        Returns:
            List of steps that can be executed now
        """
        next_steps = []
        
        for step in self.steps:
            # Skip if already completed
            if step.id in completed:
                continue
            
            # Check if all dependencies are satisfied
            if all(dep in completed for dep in step.depends_on):
                next_steps.append(step)
        
        return next_steps
    
    def has_pending_steps(self, completed: List[str]) -> bool:
        """Check if there are pending steps."""
        return len(completed) < len(self.steps)
    
    def can_execute_parallel(self, steps: List[ExecutionStep]) -> bool:
        """Check if steps can be executed in parallel."""
        if len(steps) <= 1:
            return False
        
        # Check if any step lists others as parallel-safe
        step_ids = {s.id for s in steps}
        return any(
            step_ids.intersection(step.can_parallel_with)
            for step in steps
        )


class ExecutionPlanner:
    """Create execution plans for multi-step queries."""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
    
    async def create_plan(
        self,
        query: str,
        functions: List[FunctionSchema],
        context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Create execution plan using LLM.
        
        Args:
            query: User query
            functions: Available functions with full schema
            context: Additional context
            
        Returns:
            Execution plan
        """
        prompt = self._build_planning_prompt(query, functions, context)
        
        # Get structured plan from LLM
        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=1000
        )
        
        # Parse plan
        plan = self._parse_plan(response, functions)
        
        return plan
    
    def _build_planning_prompt(
        self,
        query: str,
        functions: List[FunctionSchema],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for plan generation."""
        
        functions_info = "\n\n".join([
            f"Function: {f.name}\n"
            f"Description: {f.description}\n"
            f"Parameters: {f.parameters}\n"
            f"Dependencies: {f.dependencies}\n"
            f"Returns: {f.returns}"
            for f in functions
        ])
        
        return f"""Create a step-by-step execution plan to answer this query.

Query: {query}

Available Functions:
{functions_info}

Consider:
1. Which functions are needed?
2. What order should they execute in?
3. How does data flow between steps?
4. Can any steps run in parallel?

Output a JSON plan with this structure:
{{
    "steps": [
        {{
            "id": "step1",
            "function_name": "function_name",
            "parameters": {{"param": "value"}},
            "depends_on": [],
            "reasoning": "why this step"
        }},
        {{
            "id": "step2",
            "function_name": "another_function",
            "parameters": {{"data": "$step1"}},
            "depends_on": ["step1"],
            "can_parallel_with": [],
            "reasoning": "why this step"
        }}
    ]
}}

Use "$stepX" syntax to reference results from previous steps.

Plan:"""
    
    def _parse_plan(
        self,
        response: str,
        functions: List[FunctionSchema]
    ) -> ExecutionPlan:
        """Parse LLM response into ExecutionPlan."""
        import json
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            plan_json = json.loads(response[json_start:json_end])
            
            # Convert to ExecutionStep objects
            steps = []
            func_map = {f.name: f.function_id for f in functions}
            
            for step_data in plan_json['steps']:
                step = ExecutionStep(
                    id=step_data['id'],
                    function_id=func_map.get(step_data['function_name'], 'unknown'),
                    function_name=step_data['function_name'],
                    parameters=step_data.get('parameters', {}),
                    depends_on=step_data.get('depends_on', []),
                    can_parallel_with=step_data.get('can_parallel_with', [])
                )
                steps.append(step)
            
            return ExecutionPlan(
                steps=steps,
                metadata={'raw_response': response}
            )
            
        except Exception as e:
            logger.error(f"Failed to parse plan: {e}")
            # Return empty plan
            return ExecutionPlan(steps=[])


class DataContextManager:
    """Manage data flow between function calls."""
    
    def __init__(self):
        self.data_store: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
    
    def store_result(
        self,
        step_id: str,
        result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store result from a step.
        
        Args:
            step_id: Step identifier
            result: Result data
            metadata: Optional metadata (execution time, etc.)
        """
        self.data_store[step_id] = result
        if metadata:
            self.metadata[step_id] = metadata
        
        logger.debug(f"Stored result for {step_id}")
    
    def get_result(self, step_id: str) -> Optional[Any]:
        """Get result from a previous step."""
        return self.data_store.get(step_id)
    
    def resolve_parameters(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve parameter references to actual data.
        
        Converts "$stepX" references to actual results.
        
        Args:
            parameters: Parameters with possible references
            
        Returns:
            Parameters with resolved values
        """
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('$'):
                # Reference to previous result
                step_id = value[1:]  # Remove '$'
                resolved_value = self.get_result(step_id)
                
                if resolved_value is None:
                    logger.warning(f"Could not resolve reference: {value}")
                    resolved[key] = value  # Keep original
                else:
                    resolved[key] = resolved_value
            elif isinstance(value, dict):
                # Recursively resolve nested dicts
                resolved[key] = self.resolve_parameters(value)
            elif isinstance(value, list):
                # Resolve list items
                resolved[key] = [
                    self.resolve_parameters({'_': item})['_']
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                resolved[key] = value
        
        return resolved
    
    def clear(self):
        """Clear all stored data."""
        self.data_store.clear()
        self.metadata.clear()


@dataclass
class QualityScore:
    """Quality assessment result."""
    overall: float  # 0.0 - 1.0
    completeness: float
    coverage: float
    reliability: float
    format_valid: float
    details: Dict[str, Any] = field(default_factory=dict)


class QualityValidator:
    """Objective quality validation."""
    
    def __init__(self):
        self.weights = {
            'completeness': 0.3,
            'coverage': 0.3,
            'reliability': 0.25,
            'format_valid': 0.15
        }
    
    def validate_completion(
        self,
        query: str,
        state: Dict[str, Any],
        plan: Optional[ExecutionPlan] = None
    ) -> QualityScore:
        """
        Calculate objective quality score.
        
        Args:
            query: Original query
            state: Agent state with observations
            plan: Optional execution plan
            
        Returns:
            Quality score with breakdown
        """
        # 1. Completeness: Did we get all needed data?
        completeness = self._check_completeness(query, state, plan)
        
        # 2. Coverage: Did we call all needed functions?
        coverage = self._check_function_coverage(state, plan)
        
        # 3. Reliability: Were executions successful?
        reliability = self._check_reliability(state)
        
        # 4. Format: Is output properly formatted?
        format_valid = self._check_output_format(state)
        
        # Calculate weighted overall score
        overall = (
            completeness * self.weights['completeness'] +
            coverage * self.weights['coverage'] +
            reliability * self.weights['reliability'] +
            format_valid * self.weights['format_valid']
        )
        
        return QualityScore(
            overall=overall,
            completeness=completeness,
            coverage=coverage,
            reliability=reliability,
            format_valid=format_valid,
            details={
                'observations_count': len(state.get('observations', [])),
                'success_count': sum(
                    1 for obs in state.get('observations', [])
                    if obs.success
                ),
                'has_final_answer': bool(state.get('final_answer'))
            }
        )
    
    def _check_completeness(
        self,
        query: str,
        state: Dict[str, Any],
        plan: Optional[ExecutionPlan]
    ) -> float:
        """Check if we have all needed data."""
        if not plan:
            # Heuristic: Check if we have observations
            observations = state.get('observations', [])
            return min(len(observations) / 2.0, 1.0)  # Assume need ~2 observations
        
        # Check if all plan steps completed successfully
        completed = sum(
            1 for obs in state.get('observations', [])
            if obs.success
        )
        return min(completed / len(plan.steps), 1.0) if plan.steps else 0.0
    
    def _check_function_coverage(
        self,
        state: Dict[str, Any],
        plan: Optional[ExecutionPlan]
    ) -> float:
        """Check if all needed functions were called."""
        if not plan:
            # Heuristic: Any actions taken?
            actions = state.get('actions', [])
            return 1.0 if actions else 0.0
        
        # Check if all planned functions were executed
        executed = len(state.get('actions', []))
        needed = len(plan.steps)
        return min(executed / needed, 1.0) if needed > 0 else 0.0
    
    def _check_reliability(self, state: Dict[str, Any]) -> float:
        """Check success rate of executions."""
        observations = state.get('observations', [])
        if not observations:
            return 0.0
        
        success_count = sum(1 for obs in observations if obs.success)
        return success_count / len(observations)
    
    def _check_output_format(self, state: Dict[str, Any]) -> float:
        """Check if output is properly formatted."""
        final_answer = state.get('final_answer')
        
        if not final_answer:
            return 0.0
        
        # Check basic formatting
        score = 0.0
        
        # Has content
        if len(final_answer) > 20:
            score += 0.4
        
        # Not just error message
        if 'error' not in final_answer.lower() or len(final_answer) > 100:
            score += 0.3
        
        # Has structure (paragraphs, lists, etc.)
        if '\n' in final_answer or any(marker in final_answer for marker in ['1.', '2.', '-', '*']):
            score += 0.3
        
        return min(score, 1.0)


# =============================================================================
# PHASE 3: MONITORING
# =============================================================================

class AgentMetrics:
    """Comprehensive metrics tracking."""
    
    def __init__(self):
        self.metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_quality': 0.0,
            'total_iterations': 0,
            'function_usage': defaultdict(int),
            'error_types': defaultdict(int),
            'latencies': [],
        }
        self.start_time = time.time()
    
    def record_execution(self, state: Dict[str, Any], quality_score: Optional[QualityScore] = None):
        """Record execution metrics."""
        self.metrics['total_calls'] += 1
        
        if state.get('status') == 'completed':
            self.metrics['successful_calls'] += 1
        else:
            self.metrics['failed_calls'] += 1
            error = state.get('error', 'unknown')
            self.metrics['error_types'][error] += 1
        
        # Quality score
        if quality_score:
            self.metrics['total_quality'] += quality_score.overall
        
        # Iterations
        self.metrics['total_iterations'] += state.get('current_step', 0)
        
        # Function usage
        for action in state.get('actions', []):
            self.metrics['function_usage'][action.function_name] += 1
        
        # Latency
        latency = state.get('total_execution_time_ms', 0)
        self.metrics['latencies'].append(latency)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        total = self.metrics['total_calls']
        if total == 0:
            return {'status': 'no_data'}
        
        latencies = sorted(self.metrics['latencies'])
        
        return {
            'total_calls': total,
            'success_rate': self.metrics['successful_calls'] / total,
            'failure_rate': self.metrics['failed_calls'] / total,
            'avg_quality': self.metrics['total_quality'] / self.metrics['successful_calls']
                if self.metrics['successful_calls'] > 0 else 0,
            'avg_iterations': self.metrics['total_iterations'] / total,
            'latency_p50': latencies[len(latencies) // 2] if latencies else 0,
            'latency_p95': latencies[int(len(latencies) * 0.95)] if latencies else 0,
            'top_functions': dict(sorted(
                self.metrics['function_usage'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            'top_errors': dict(sorted(
                self.metrics['error_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            'uptime_seconds': time.time() - self.start_time
        }
