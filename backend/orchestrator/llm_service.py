"""
LLM Service for query parsing, planning, and response generation
"""
import logging
from typing import List, Dict, Any, Optional
import json

from config.settings import settings

# LLM imports based on provider
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QueryIntent(BaseModel):
    """Parsed query intent"""
    intent: str = Field(description="Main intent: data_query, analytics, comparison, trend, summary")
    entities: Dict[str, Any] = Field(description="Extracted entities (time, location, metrics, etc.)")
    query_type: str = Field(description="Specific query type")
    confidence: float = Field(description="Confidence score 0-1")


class FunctionSelection(BaseModel):
    """Selected functions for execution"""
    function_ids: List[str] = Field(description="List of function IDs to execute")
    parameters: Dict[str, Dict[str, Any]] = Field(description="Parameters for each function")
    execution_mode: str = Field(description="sequential or parallel")
    reasoning: str = Field(description="Reasoning for selection")


class LLMService:
    """Service for LLM operations"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.json_parser = JsonOutputParser()
    
    def _initialize_llm(self):
        """Initialize LLM based on provider"""
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "gemini":
            if not ChatGoogleGenerativeAI:
                raise ImportError("Install langchain-google-genai")
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not configured")
            return ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.1,
                max_output_tokens=2048
            )
        
        elif provider == "openai":
            if not ChatOpenAI:
                raise ImportError("Install langchain-openai")
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=0.1,
                max_tokens=2048
            )
        
        elif provider == "anthropic":
            if not ChatAnthropic:
                raise ImportError("Install langchain-anthropic")
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            return ChatAnthropic(
                model=settings.ANTHROPIC_MODEL,
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.1,
                max_tokens=2048
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    async def parse_query(
        self,
        query: str,
        language: str = "vi",
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> QueryIntent:
        """Parse user query and extract intent and entities"""
        
        context_str = ""
        if conversation_context:
            context_str = f"\n\nConversation context:\n{json.dumps(conversation_context, ensure_ascii=False, indent=2)}"
        
        system_prompt = f"""You are an intelligent query parser for an IOC (Intelligent Operations Center) system.
Parse the user's query and extract:
1. Main intent (data_query, analytics, comparison, trend, summary)
2. Entities (time periods, locations, metrics, thresholds, etc.)
3. Query type (specific classification)
4. Confidence score

The system manages: energy, traffic, environment, health, security domains.

Respond in JSON format:
{{
    "intent": "data_query|analytics|comparison|trend|summary",
    "entities": {{
        "time_range": "last_hour|today|last_week|custom",
        "start_date": "YYYY-MM-DD or null",
        "end_date": "YYYY-MM-DD or null",
        "location": "location name or null",
        "metric": "metric name or null",
        "threshold": number or null,
        "comparison_period": "previous_day|previous_week|previous_month or null",
        "domain": "energy|traffic|environment|health|security or null"
    }},
    "query_type": "specific classification",
    "confidence": 0.0-1.0
}}

Examples:
- "Mức tiêu thụ điện hôm nay" → {{"intent": "data_query", "entities": {{"time_range": "today", "domain": "energy"}}, "query_type": "power_consumption", "confidence": 0.95}}
- "So sánh lưu lượng giao thông tuần này với tuần trước" → {{"intent": "comparison", "entities": {{"time_range": "this_week", "comparison_period": "previous_week", "domain": "traffic"}}, "query_type": "traffic_comparison", "confidence": 0.92}}
{context_str}
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Query: {query}\nLanguage: {language}")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            result = json.loads(response.content)
            return QueryIntent(**result)
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            # Fallback to basic intent
            return QueryIntent(
                intent="data_query",
                entities={"domain": None},
                query_type="unknown",
                confidence=0.3
            )
    
    async def select_functions(
        self,
        query: str,
        intent: QueryIntent,
        available_functions: List[Dict[str, Any]],
        language: str = "vi"
    ) -> FunctionSelection:
        """Select appropriate functions to execute based on query intent"""
        
        # Format available functions for LLM
        functions_str = json.dumps(available_functions, ensure_ascii=False, indent=2)
        
        system_prompt = f"""You are an intelligent function selector for an IOC system.
Given a user query, intent, and available API functions, select the most appropriate functions to execute.

Consider:
1. Query intent and entities
2. Function descriptions and parameters
3. Data dependencies between functions
4. Execution efficiency

Respond in JSON format:
{{
    "function_ids": ["func1", "func2"],
    "parameters": {{
        "func1": {{"param1": "value1"}},
        "func2": {{"param1": "value1"}}
    }},
    "execution_mode": "sequential|parallel",
    "reasoning": "Explanation of selection"
}}

Available functions:
{functions_str}

Intent: {intent.intent}
Entities: {json.dumps(intent.entities, ensure_ascii=False)}
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Select functions for: {query}")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            result = json.loads(response.content)
            return FunctionSelection(**result)
        except Exception as e:
            logger.error(f"Error selecting functions: {e}")
            # Fallback to first relevant function
            if available_functions:
                func = available_functions[0]
                return FunctionSelection(
                    function_ids=[func['function_id']],
                    parameters={func['function_id']: {}},
                    execution_mode="sequential",
                    reasoning="Fallback to first available function"
                )
            else:
                return FunctionSelection(
                    function_ids=[],
                    parameters={},
                    execution_mode="sequential",
                    reasoning="No functions available"
                )
    
    async def generate_response(
        self,
        query: str,
        execution_results: List[Dict[str, Any]],
        insights: Optional[List[str]] = None,
        language: str = "vi"
    ) -> str:
        """Generate natural language response from execution results"""
        
        results_str = json.dumps(execution_results, ensure_ascii=False, indent=2)
        insights_str = "\n".join(insights) if insights else "None"
        
        lang_instruction = "in Vietnamese" if language == "vi" else "in English"
        
        system_prompt = f"""You are an intelligent assistant for an IOC system.
Generate a clear, concise, and informative response {lang_instruction} based on:
1. User's original query
2. Execution results from API calls
3. Analytical insights

Guidelines:
- Use natural, conversational language
- Highlight key findings and important metrics
- Include specific numbers and dates
- Mention any anomalies or concerns
- Suggest follow-up actions if relevant
- Be accurate and factual

Execution Results:
{results_str}

Insights:
{insights_str}
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User query: {query}\n\nGenerate response based on the results above.")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Unable to generate response. Executed {len(execution_results)} function(s) successfully."
    
    async def suggest_visualization(
        self,
        data: Dict[str, Any],
        query_type: str
    ) -> Optional[Dict[str, Any]]:
        """Suggest appropriate visualization for data"""
        
        data_summary = {
            "query_type": query_type,
            "data_keys": list(data.keys()) if isinstance(data, dict) else "non-dict",
            "data_length": len(data) if isinstance(data, (list, dict)) else 0
        }
        
        system_prompt = f"""Suggest the best visualization type for this data.

Query type: {query_type}
Data summary: {json.dumps(data_summary, ensure_ascii=False)}

Respond in JSON:
{{
    "chart_type": "line|bar|pie|heatmap|scatter|table",
    "x_axis": "field name",
    "y_axis": "field name",
    "title": "Chart title",
    "description": "Brief description"
}}

If no visualization is appropriate, return null.
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Suggest visualization")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            result = json.loads(response.content)
            return result
        except Exception as e:
            logger.error(f"Error suggesting visualization: {e}")
            return None


# Global LLM service instance
llm_service = LLMService()
