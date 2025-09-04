from functools import wraps
import time
import logging
from typing import Dict, Any, Callable

# Simple metrics collection
metrics_data: Dict[str, Dict[str, Any]] = {
    "requests": {},
    "response_times": {},
    "errors": {}
}

def track_metrics(endpoint_name: str):
    """Decorator to track API endpoint metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Initialize metrics for this endpoint
            if endpoint_name not in metrics_data["requests"]:
                metrics_data["requests"][endpoint_name] = 0
                metrics_data["response_times"][endpoint_name] = []
                metrics_data["errors"][endpoint_name] = 0
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Track successful request
                metrics_data["requests"][endpoint_name] += 1
                response_time = time.time() - start_time
                metrics_data["response_times"][endpoint_name].append(response_time)
                
                # Keep only last 100 response times to prevent memory growth
                if len(metrics_data["response_times"][endpoint_name]) > 100:
                    metrics_data["response_times"][endpoint_name] = \
                        metrics_data["response_times"][endpoint_name][-100:]
                
                logging.info(f"Endpoint {endpoint_name} completed in {response_time:.3f}s")
                return result
                
            except Exception as e:
                # Track error
                metrics_data["errors"][endpoint_name] += 1
                response_time = time.time() - start_time
                logging.error(f"Endpoint {endpoint_name} failed after {response_time:.3f}s: {str(e)}")
                raise
                
        return wrapper
    return decorator

def get_metrics() -> Dict[str, Any]:
    """Get current metrics summary"""
    summary = {}
    
    for endpoint in metrics_data["requests"]:
        response_times = metrics_data["response_times"][endpoint]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        summary[endpoint] = {
            "total_requests": metrics_data["requests"][endpoint],
            "total_errors": metrics_data["errors"][endpoint],
            "avg_response_time": round(avg_response_time, 3),
            "error_rate": round(
                metrics_data["errors"][endpoint] / max(metrics_data["requests"][endpoint], 1) * 100, 2
            )
        }
    
    return summary

def reset_metrics():
    """Reset all metrics data"""
    global metrics_data
    metrics_data = {
        "requests": {},
        "response_times": {},
        "errors": {}
    }