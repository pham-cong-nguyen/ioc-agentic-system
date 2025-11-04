"""
Data Analyzer - Analyze API results and generate insights
"""
import logging
from typing import List, Dict, Any, Optional
import statistics
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """Analyze data and generate insights"""
    
    async def analyze(
        self,
        data: List[Any],
        query_type: str,
        entities: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze data based on query type"""
        
        if not data:
            return {"error": "No data to analyze"}
        
        # Determine analysis method based on query type
        if query_type in ["comparison", "trend"]:
            return await self._analyze_trend(data, entities)
        elif query_type == "analytics":
            return await self._analyze_statistics(data, entities)
        elif query_type == "summary":
            return await self._analyze_summary(data, entities)
        else:
            return await self._analyze_basic(data, entities)
    
    async def _analyze_basic(
        self,
        data: List[Any],
        entities: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Basic data analysis"""
        
        result = {
            "data_count": len(data),
            "timestamp": datetime.utcnow().isoformat(),
            "raw_data": data
        }
        
        # Try to extract numeric values for basic stats
        numeric_values = self._extract_numeric_values(data)
        if numeric_values:
            result["statistics"] = {
                "count": len(numeric_values),
                "sum": sum(numeric_values),
                "mean": statistics.mean(numeric_values),
                "median": statistics.median(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values)
            }
            
            if len(numeric_values) > 1:
                result["statistics"]["stdev"] = statistics.stdev(numeric_values)
        
        return result
    
    async def _analyze_statistics(
        self,
        data: List[Any],
        entities: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Statistical analysis"""
        
        numeric_values = self._extract_numeric_values(data)
        
        if not numeric_values:
            return {"error": "No numeric data for statistical analysis"}
        
        result = {
            "count": len(numeric_values),
            "sum": sum(numeric_values),
            "mean": statistics.mean(numeric_values),
            "median": statistics.median(numeric_values),
            "mode": statistics.mode(numeric_values) if len(set(numeric_values)) < len(numeric_values) else None,
            "min": min(numeric_values),
            "max": max(numeric_values),
            "range": max(numeric_values) - min(numeric_values)
        }
        
        if len(numeric_values) > 1:
            result["variance"] = statistics.variance(numeric_values)
            result["stdev"] = statistics.stdev(numeric_values)
            
            # Coefficient of variation
            if result["mean"] != 0:
                result["coefficient_of_variation"] = result["stdev"] / result["mean"]
        
        # Quartiles
        if len(numeric_values) >= 4:
            sorted_values = sorted(numeric_values)
            result["quartiles"] = {
                "q1": np.percentile(sorted_values, 25),
                "q2": np.percentile(sorted_values, 50),
                "q3": np.percentile(sorted_values, 75)
            }
            result["iqr"] = result["quartiles"]["q3"] - result["quartiles"]["q1"]
        
        # Outlier detection (IQR method)
        if "iqr" in result:
            q1 = result["quartiles"]["q1"]
            q3 = result["quartiles"]["q3"]
            iqr = result["iqr"]
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [v for v in numeric_values if v < lower_bound or v > upper_bound]
            result["outliers"] = {
                "count": len(outliers),
                "values": outliers,
                "percentage": (len(outliers) / len(numeric_values)) * 100
            }
        
        return result
    
    async def _analyze_trend(
        self,
        data: List[Any],
        entities: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Trend analysis and comparison"""
        
        # Assume data is time-series or has comparison structure
        result = {
            "data_points": len(data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        numeric_values = self._extract_numeric_values(data)
        
        if numeric_values and len(numeric_values) >= 2:
            # Calculate trend
            result["trend"] = {
                "direction": "increasing" if numeric_values[-1] > numeric_values[0] else "decreasing",
                "change": numeric_values[-1] - numeric_values[0],
                "change_percentage": ((numeric_values[-1] - numeric_values[0]) / numeric_values[0] * 100) if numeric_values[0] != 0 else 0
            }
            
            # Moving average if enough data points
            if len(numeric_values) >= 5:
                window_size = min(5, len(numeric_values) // 2)
                moving_avg = []
                for i in range(len(numeric_values) - window_size + 1):
                    window = numeric_values[i:i + window_size]
                    moving_avg.append(sum(window) / window_size)
                result["moving_average"] = moving_avg
            
            # Simple linear regression for trend line
            if len(numeric_values) >= 3:
                x = list(range(len(numeric_values)))
                y = numeric_values
                
                n = len(x)
                x_mean = sum(x) / n
                y_mean = sum(y) / n
                
                numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
                denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
                
                if denominator != 0:
                    slope = numerator / denominator
                    intercept = y_mean - slope * x_mean
                    
                    result["linear_trend"] = {
                        "slope": slope,
                        "intercept": intercept,
                        "equation": f"y = {slope:.2f}x + {intercept:.2f}"
                    }
        
        # Comparison if entities contain comparison period
        if entities and entities.get("comparison_period"):
            result["comparison"] = {
                "period": entities["comparison_period"],
                "current_mean": statistics.mean(numeric_values) if numeric_values else None,
                "change_detected": True
            }
        
        return result
    
    async def _analyze_summary(
        self,
        data: List[Any],
        entities: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Summary analysis"""
        
        result = {
            "total_records": len(data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Group by categories if possible
        if isinstance(data[0], dict):
            # Try to find categorical fields
            categorical_fields = []
            for key in data[0].keys():
                values = [item.get(key) for item in data if isinstance(item, dict)]
                unique_values = set(values)
                if len(unique_values) < len(data) / 2:  # Less than 50% unique
                    categorical_fields.append(key)
            
            if categorical_fields:
                result["categories"] = {}
                for field in categorical_fields[:3]:  # Limit to 3 fields
                    value_counts = {}
                    for item in data:
                        if isinstance(item, dict):
                            value = item.get(field)
                            value_counts[str(value)] = value_counts.get(str(value), 0) + 1
                    result["categories"][field] = value_counts
        
        # Numeric summary
        numeric_values = self._extract_numeric_values(data)
        if numeric_values:
            result["numeric_summary"] = {
                "total": sum(numeric_values),
                "average": statistics.mean(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values)
            }
        
        return result
    
    def _extract_numeric_values(self, data: List[Any]) -> List[float]:
        """Extract numeric values from data"""
        numeric_values = []
        
        for item in data:
            if isinstance(item, (int, float)):
                numeric_values.append(float(item))
            elif isinstance(item, dict):
                # Try to find numeric fields
                for value in item.values():
                    if isinstance(value, (int, float)):
                        numeric_values.append(float(value))
            elif isinstance(item, list):
                # Recursively extract from lists
                numeric_values.extend(self._extract_numeric_values(item))
        
        return numeric_values
    
    async def generate_insights(
        self,
        data: Dict[str, Any],
        query_type: str
    ) -> List[str]:
        """Generate human-readable insights from analyzed data"""
        
        insights = []
        
        # Statistics-based insights
        if "statistics" in data:
            stats = data["statistics"]
            
            if "mean" in stats and "max" in stats:
                if stats["max"] > stats["mean"] * 1.5:
                    insights.append(f"Peak value ({stats['max']:.2f}) is significantly higher than average ({stats['mean']:.2f})")
            
            if "stdev" in stats and "mean" in stats:
                cv = stats["stdev"] / stats["mean"] if stats["mean"] != 0 else 0
                if cv > 0.5:
                    insights.append("High variability detected in the data")
                elif cv < 0.1:
                    insights.append("Data shows consistent values with low variability")
        
        # Trend-based insights
        if "trend" in data:
            trend = data["trend"]
            direction = trend.get("direction", "stable")
            change_pct = trend.get("change_percentage", 0)
            
            if abs(change_pct) > 20:
                insights.append(f"Significant {direction} trend detected: {abs(change_pct):.1f}% change")
            elif abs(change_pct) > 10:
                insights.append(f"Moderate {direction} trend: {abs(change_pct):.1f}% change")
            else:
                insights.append(f"Relatively stable with minor {direction} trend")
        
        # Outlier insights
        if "outliers" in data:
            outliers = data["outliers"]
            if outliers["count"] > 0:
                insights.append(f"Found {outliers['count']} outlier(s) ({outliers['percentage']:.1f}% of data)")
        
        # Linear trend insights
        if "linear_trend" in data:
            slope = data["linear_trend"]["slope"]
            if abs(slope) > 1:
                direction = "upward" if slope > 0 else "downward"
                insights.append(f"Strong {direction} linear trend detected (slope: {slope:.2f})")
        
        # Category insights
        if "categories" in data:
            for field, counts in data["categories"].items():
                if counts:
                    most_common = max(counts.items(), key=lambda x: x[1])
                    total = sum(counts.values())
                    percentage = (most_common[1] / total * 100) if total > 0 else 0
                    insights.append(f"Most common {field}: {most_common[0]} ({percentage:.1f}%)")
        
        # Comparison insights
        if "comparison" in data:
            comparison = data["comparison"]
            if comparison.get("change_detected"):
                insights.append(f"Changes detected compared to {comparison.get('period', 'previous period')}")
        
        if not insights:
            insights.append("Data analyzed successfully")
        
        return insights


# Global analyzer instance
analyzer = DataAnalyzer()
