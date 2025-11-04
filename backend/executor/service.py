"""
API Executor - Execute API calls with retry, timeout, and error handling
"""
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from backend.registry.service import FunctionRegistryService
from backend.utils.cache import cache
from config.settings import settings

logger = logging.getLogger(__name__)


class APIExecutor:
    """Execute API calls with advanced features"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            follow_redirects=True
        )
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    def _generate_cache_key(
        self,
        function_id: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Generate cache key for API call"""
        import hashlib
        import json
        
        params_str = json.dumps(parameters, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"api_result:{function_id}:{params_hash}"
    
    async def _get_cached_result(
        self,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached API result"""
        if not settings.CACHE_ENABLED:
            return None
        
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for key: {cache_key}")
            return cached
        
        return None
    
    async def _cache_result(
        self,
        cache_key: str,
        result: Dict[str, Any],
        ttl: int
    ):
        """Cache API result"""
        if settings.CACHE_ENABLED:
            await cache.set(cache_key, result, ttl=ttl)
    
    def _build_headers(
        self,
        auth_required: bool,
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"{settings.APP_NAME}/{settings.APP_VERSION}"
        }
        
        # Add authentication if required
        if auth_required and settings.IOC_API_KEY:
            headers["Authorization"] = f"Bearer {settings.IOC_API_KEY}"
        
        # Add additional headers
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def _execute_http_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> httpx.Response:
        """Execute HTTP request with retry"""
        try:
            if method.upper() == "GET":
                response = await self.client.get(
                    url,
                    headers=headers,
                    params=parameters,
                    timeout=timeout
                )
            elif method.upper() == "POST":
                response = await self.client.post(
                    url,
                    headers=headers,
                    json=parameters,
                    timeout=timeout
                )
            elif method.upper() == "PUT":
                response = await self.client.put(
                    url,
                    headers=headers,
                    json=parameters,
                    timeout=timeout
                )
            elif method.upper() == "DELETE":
                response = await self.client.delete(
                    url,
                    headers=headers,
                    params=parameters,
                    timeout=timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response
            
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout for {url}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            raise
    
    async def execute_function(
        self,
        function_id: str,
        parameters: Dict[str, Any],
        registry_service: FunctionRegistryService,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a single function call
        
        Args:
            function_id: Function identifier
            parameters: Function parameters
            registry_service: Registry service instance
            use_cache: Whether to use cache
            
        Returns:
            API response with metadata
        """
        start_time = datetime.utcnow()
        
        # Get function metadata
        function = await registry_service.get_function(function_id)
        if not function:
            raise ValueError(f"Function {function_id} not found in registry")
        
        if function.deprecated:
            logger.warning(f"Function {function_id} is deprecated")
        
        # Check cache
        cache_key = self._generate_cache_key(function_id, parameters)
        if use_cache:
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return {
                    "function_id": function_id,
                    "success": True,
                    "data": cached_result,
                    "cached": True,
                    "execution_time": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Build request
        headers = self._build_headers(function.auth_required)
        
        try:
            # Execute request
            response = await self._execute_http_request(
                method=function.method,
                url=function.endpoint,
                headers=headers,
                parameters=parameters,
                timeout=function.timeout
            )
            
            # Parse response
            result_data = response.json() if response.text else {}
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Cache result
            if use_cache:
                await self._cache_result(cache_key, result_data, function.cache_ttl)
            
            # Update usage stats
            await registry_service.update_usage_stats(
                function_id=function_id,
                response_time=execution_time * 1000,  # Convert to ms
                success=True
            )
            
            # Return result
            return {
                "function_id": function_id,
                "success": True,
                "data": result_data,
                "cached": False,
                "execution_time": execution_time,
                "status_code": response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update usage stats
            await registry_service.update_usage_stats(
                function_id=function_id,
                response_time=execution_time * 1000,
                success=False
            )
            
            # Return error
            logger.error(f"Failed to execute {function_id}: {e}")
            return {
                "function_id": function_id,
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def execute_parallel(
        self,
        function_calls: List[Dict[str, Any]],
        registry_service: FunctionRegistryService
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple function calls in parallel
        
        Args:
            function_calls: List of {function_id, parameters}
            registry_service: Registry service instance
            
        Returns:
            List of results
        """
        tasks = [
            self.execute_function(
                function_id=call["function_id"],
                parameters=call.get("parameters", {}),
                registry_service=registry_service
            )
            for call in function_calls
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "function_id": function_calls[i]["function_id"],
                    "success": False,
                    "error": str(result),
                    "error_type": type(result).__name__
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def execute_sequential(
        self,
        function_calls: List[Dict[str, Any]],
        registry_service: FunctionRegistryService
    ) -> List[Dict[str, Any]]:
        """
        Execute function calls sequentially (for dependent calls)
        
        Args:
            function_calls: List of {function_id, parameters}
            registry_service: Registry service instance
            
        Returns:
            List of results
        """
        results = []
        context = {}  # Store previous results for parameter substitution
        
        for call in function_calls:
            # Substitute parameters from previous results
            parameters = self._substitute_parameters(
                call.get("parameters", {}),
                context
            )
            
            # Execute call
            result = await self.execute_function(
                function_id=call["function_id"],
                parameters=parameters,
                registry_service=registry_service
            )
            
            # Store result in context
            context[call["function_id"]] = result.get("data", {})
            
            results.append(result)
            
            # Stop if call failed and stop_on_error is True
            if not result["success"] and call.get("stop_on_error", False):
                break
        
        return results
    
    def _substitute_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Substitute parameter values from context
        
        Example:
            parameters = {"value": "{{previous_call.result}}"}
            context = {"previous_call": {"result": 123}}
            returns: {"value": 123}
        """
        import re
        
        substituted = {}
        pattern = r'\{\{([^}]+)\}\}'
        
        for key, value in parameters.items():
            if isinstance(value, str):
                matches = re.findall(pattern, value)
                if matches:
                    # Extract value from context
                    path = matches[0].split('.')
                    result = context
                    for p in path:
                        result = result.get(p, {})
                    substituted[key] = result
                else:
                    substituted[key] = value
            else:
                substituted[key] = value
        
        return substituted


# Global executor instance
executor = APIExecutor()


async def close_executor():
    """Close executor"""
    await executor.close()
