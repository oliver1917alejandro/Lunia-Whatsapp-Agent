"""
Performance monitoring and metrics collection service
"""
import asyncio
import time
import psutil
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from src.core.logger import logger

@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass  
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    load_average: Optional[float] = None

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    uptime_seconds: float
    active_sessions: int
    total_conversations: int
    messages_processed: int
    errors_count: int
    avg_response_time: float
    service_status: Dict[str, bool]
    memory_usage_mb: float
    cpu_usage_percent: float

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics_history: Dict[str, list] = {}
        self.start_time = time.time()
        self.message_count = 0
        self.error_count = 0
        self.response_times = []
        self.is_monitoring = False
        
    async def start_monitoring(self, interval: int = 30):
        """Start continuous monitoring"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        logger.info(f"Starting performance monitoring with {interval}s interval")
        
        while self.is_monitoring:
            try:
                await self.collect_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.is_monitoring = False
        logger.info("Performance monitoring stopped")
    
    async def collect_metrics(self):
        """Collect all metrics"""
        try:
            system_metrics = self.get_system_metrics()
            app_metrics = await self.get_application_metrics()
            
            # Store metrics with timestamp
            timestamp = datetime.now()
            
            # System metrics
            self._store_metric("cpu_percent", system_metrics.cpu_percent, timestamp)
            self._store_metric("memory_percent", system_metrics.memory_percent, timestamp)
            self._store_metric("disk_percent", system_metrics.disk_percent, timestamp)
            
            # Application metrics
            self._store_metric("active_sessions", app_metrics.active_sessions, timestamp)
            self._store_metric("messages_processed", app_metrics.messages_processed, timestamp)
            self._store_metric("errors_count", app_metrics.errors_count, timestamp)
            self._store_metric("avg_response_time", app_metrics.avg_response_time, timestamp)
            
            # Clean old metrics (keep last 24 hours)
            self._cleanup_old_metrics()
            
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network (if available)
            network_bytes_sent = 0
            network_bytes_recv = 0
            try:
                network = psutil.net_io_counters()
                network_bytes_sent = network.bytes_sent
                network_bytes_recv = network.bytes_recv
            except:
                pass
            
            # Load average (Unix systems)
            load_avg = None
            try:
                load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
            except:
                pass
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_percent=(disk.used / disk.total) * 100,
                disk_used_gb=disk.used / (1024 * 1024 * 1024),
                disk_free_gb=disk.free / (1024 * 1024 * 1024),
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                load_average=load_avg
            )
            
        except Exception as e:
            logger.error(f"System metrics collection error: {e}")
            # Return default metrics
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0
            )
    
    async def get_application_metrics(self) -> ApplicationMetrics:
        """Get application-specific metrics"""
        try:
            from src.services.session_manager import session_manager
            from src.services.whatsapp_service import whatsapp_service
            from src.core.config import Config
            
            # Calculate uptime
            uptime = time.time() - self.start_time
            
            # Session metrics
            sessions = getattr(session_manager, '_sessions', {})
            active_sessions = len(sessions)
            total_conversations = sum(
                len(session.conversation_history) 
                for session in sessions.values()
            )
            
            # Service status
            service_status = {
                "whatsapp": whatsapp_service._validate_api_config(),
                "openai": bool(getattr(Config, 'OPENAI_API_KEY', None)),
                "email": bool(getattr(Config, 'GMAIL_USER', None)),
                "calendar": bool(getattr(Config, 'GOOGLE_CREDENTIALS_PATH', None)),
                "database": bool(getattr(Config, 'SUPABASE_URL', None))
            }
            
            # Response time average
            avg_response_time = (
                sum(self.response_times) / len(self.response_times) 
                if self.response_times else 0.0
            )
            
            # Process-specific metrics
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            return ApplicationMetrics(
                uptime_seconds=uptime,
                active_sessions=active_sessions,
                total_conversations=total_conversations,
                messages_processed=self.message_count,
                errors_count=self.error_count,
                avg_response_time=avg_response_time,
                service_status=service_status,
                memory_usage_mb=memory_info.rss / (1024 * 1024),
                cpu_usage_percent=cpu_percent
            )
            
        except Exception as e:
            logger.error(f"Application metrics collection error: {e}")
            return ApplicationMetrics(
                uptime_seconds=0.0,
                active_sessions=0,
                total_conversations=0,
                messages_processed=0,
                errors_count=0,
                avg_response_time=0.0,
                service_status={},
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0
            )
    
    def record_message_processed(self, processing_time: float):
        """Record message processing event"""
        self.message_count += 1
        self.response_times.append(processing_time)
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def record_error(self):
        """Record error occurrence"""
        self.error_count += 1
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        try:
            system_metrics = self.get_system_metrics()
            
            # Get recent metrics from history
            recent_metrics = {}
            for metric_name, values in self.metrics_history.items():
                if values:
                    recent_values = [v.value for v in values[-10:]]  # Last 10 points
                    recent_metrics[metric_name] = {
                        "current": recent_values[-1] if recent_values else 0,
                        "average": sum(recent_values) / len(recent_values) if recent_values else 0,
                        "min": min(recent_values) if recent_values else 0,
                        "max": max(recent_values) if recent_values else 0
                    }
            
            return {
                "system": {
                    "cpu_percent": system_metrics.cpu_percent,
                    "memory_percent": system_metrics.memory_percent,
                    "memory_used_mb": system_metrics.memory_used_mb,
                    "memory_available_mb": system_metrics.memory_available_mb,
                    "disk_percent": system_metrics.disk_percent,
                    "disk_used_gb": system_metrics.disk_used_gb,
                    "disk_free_gb": system_metrics.disk_free_gb,
                    "load_average": system_metrics.load_average
                },
                "application": {
                    "uptime_seconds": time.time() - self.start_time,
                    "messages_processed": self.message_count,
                    "errors_count": self.error_count,
                    "avg_response_time": (
                        sum(self.response_times) / len(self.response_times) 
                        if self.response_times else 0.0
                    )
                },
                "trends": recent_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Metrics summary error: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _store_metric(self, name: str, value: float, timestamp: datetime):
        """Store metric point in history"""
        if name not in self.metrics_history:
            self.metrics_history[name] = []
        
        self.metrics_history[name].append(MetricPoint(timestamp, value))
        
        # Keep only last 1000 points per metric
        if len(self.metrics_history[name]) > 1000:
            self.metrics_history[name] = self.metrics_history[name][-1000:]
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than 24 hours"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for metric_name in self.metrics_history:
            self.metrics_history[metric_name] = [
                point for point in self.metrics_history[metric_name]
                if point.timestamp > cutoff_time
            ]
    
    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        try:
            system_metrics = self.get_system_metrics()
            
            metrics_lines = [
                "# HELP lunia_cpu_percent CPU usage percentage",
                "# TYPE lunia_cpu_percent gauge",
                f"lunia_cpu_percent {system_metrics.cpu_percent}",
                "",
                "# HELP lunia_memory_percent Memory usage percentage", 
                "# TYPE lunia_memory_percent gauge",
                f"lunia_memory_percent {system_metrics.memory_percent}",
                "",
                "# HELP lunia_messages_total Total messages processed",
                "# TYPE lunia_messages_total counter", 
                f"lunia_messages_total {self.message_count}",
                "",
                "# HELP lunia_errors_total Total errors occurred",
                "# TYPE lunia_errors_total counter",
                f"lunia_errors_total {self.error_count}",
                "",
                "# HELP lunia_uptime_seconds Application uptime in seconds",
                "# TYPE lunia_uptime_seconds gauge",
                f"lunia_uptime_seconds {time.time() - self.start_time}",
                ""
            ]
            
            return "\n".join(metrics_lines)
            
        except Exception as e:
            logger.error(f"Prometheus metrics export error: {e}")
            return f"# Error exporting metrics: {e}\n"

# Global performance monitor instance
performance_monitor = PerformanceMonitor()
