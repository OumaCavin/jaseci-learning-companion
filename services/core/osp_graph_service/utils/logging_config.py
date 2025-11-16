"""
Logging Configuration for OSP Graph Service

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/

Centralized logging configuration for the OSP Graph Service
in the Jaseci Learning Companion system.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime


def setup_logging(name: str = None) -> logging.Logger:
    """
    Setup logging configuration for the application
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)8s] %(name)s %(filename)s:%(lineno)d: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": sys.stdout
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "detailed",
                "filename": str(log_dir / "osp_graph_service.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "error_file": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "detailed",
                "filename": str(log_dir / "osp_graph_service_errors.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3,
                "encoding": "utf-8"
            },
            "json_file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": str(log_dir / "osp_graph_service_json.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"]
            },
            "osp_graph_service": {
                "level": "DEBUG",
                "handlers": ["console", "file", "json_file"],
                "propagate": False
            },
            "osp_graph_service.database": {
                "level": "DEBUG",
                "handlers": ["file", "json_file"],
                "propagate": False
            },
            "osp_graph_service.jaseci_parser": {
                "level": "DEBUG",
                "handlers": ["file", "json_file"],
                "propagate": False
            },
            "osp_graph_service.graph_analytics": {
                "level": "DEBUG",
                "handlers": ["file", "json_file"],
                "propagate": False
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"]
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Get logger
    logger = logging.getLogger(name)
    
    return logger


class OSPGraphLogger:
    """Specialized logger for OSP Graph Service operations"""
    
    def __init__(self, name: str = "osp_graph_service"):
        self.logger = logging.getLogger(name)
    
    def info_analysis_start(self, analysis_type: str, project_id: str):
        """Log analysis start"""
        self.logger.info(f"🔍 Starting {analysis_type} analysis for project {project_id}")
    
    def info_analysis_complete(self, analysis_type: str, project_id: str, execution_time: float):
        """Log analysis completion"""
        self.logger.info(f"✅ {analysis_type} analysis completed for project {project_id} in {execution_time:.2f}s")
    
    def info_node_creation(self, node_count: int, project_id: str):
        """Log node creation"""
        self.logger.info(f"📊 Created {node_count} OSP nodes for project {project_id}")
    
    def info_relationship_creation(self, relationship_count: int, project_id: str):
        """Log relationship creation"""
        self.logger.info(f"🔗 Created {relationship_count} OSP relationships for project {project_id}")
    
    def warning_circular_dependency(self, cycles: list):
        """Log circular dependency detection"""
        self.logger.warning(f"🔄 Detected circular dependencies: {len(cycles)} cycles found")
    
    def error_database_connection(self, error: Exception):
        """Log database connection error"""
        self.logger.error(f"❌ Database connection error: {str(error)}")
    
    def error_parsing_failure(self, error: Exception, filename: str = None):
        """Log parsing failure"""
        file_info = f" for {filename}" if filename else ""
        self.logger.error(f"❌ Parsing failure{file_info}: {str(error)}")
    
    def debug_jaseci_ast(self, node_type: str, node_name: str):
        """Debug Jaseci AST processing"""
        self.logger.debug(f"🧩 Processing Jaseci AST node: {node_type}:{node_name}")
    
    def debug_osp_conversion(self, jaseci_type: str, osp_type: str):
        """Debug OSP type conversion"""
        self.logger.debug(f"🔄 Converting Jaseci type '{jaseci_type}' to OSP type '{osp_type}'")
    
    def debug_query_execution(self, query_type: str, project_id: str):
        """Debug query execution"""
        self.logger.debug(f"🔎 Executing {query_type} query for project {project_id}")


class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self, name: str = "osp_graph_service.performance"):
        self.logger = logging.getLogger(name)
    
    def log_timing(self, operation: str, duration: float, additional_info: Dict[str, Any] = None):
        """Log operation timing"""
        info_str = ""
        if additional_info:
            info_str = f" - {json.dumps(additional_info, default=str)}"
        
        self.logger.info(f"⏱️ {operation} completed in {duration:.3f}s{info_str}")
    
    def log_memory_usage(self, operation: str, memory_mb: float):
        """Log memory usage"""
        self.logger.info(f"💾 {operation} used {memory_mb:.2f}MB of memory")
    
    def log_complexity_metrics(self, project_id: str, metrics: Dict[str, Any]):
        """Log complexity analysis metrics"""
        self.logger.info(f"📈 Complexity metrics for {project_id}: {json.dumps(metrics, default=str)}")


# Create global logger instances
osp_logger = OSPGraphLogger()
performance_logger = PerformanceLogger()


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a configured logger
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name or "osp_graph_service")


def configure_development_logging():
    """Configure logging for development environment"""
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "dev": {
                "format": "\033[92m%(asctime)s\033[0m [\033[94m%(levelname)8s\033[0m] \033[93m%(name)s\033[0m: \033[97m%(message)s\033[0m",
                "datefmt": "%H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "dev",
                "stream": sys.stdout
            }
        },
        "loggers": {
            "": {
                "level": "DEBUG",
                "handlers": ["console"]
            },
            "osp_graph_service": {
                "level": "DEBUG",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)


def configure_production_logging():
    """Configure logging for production environment"""
    # Production logging should be less verbose and more structured
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "prod": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "osp-graph-service", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%S"
            }
        },
        "handlers": {
            "file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "prod",
                "filename": str(log_dir / "osp_graph_service_production.log"),
                "maxBytes": 52428800,  # 50MB
                "backupCount": 10,
                "encoding": "utf-8"
            },
            "error_file": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "prod",
                "filename": str(log_dir / "osp_graph_service_errors_production.log"),
                "maxBytes": 52428800,  # 50MB
                "backupCount": 5,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "": {
                "level": "INFO",
                "handlers": ["file"]
            },
            "osp_graph_service": {
                "level": "INFO",
                "handlers": ["file", "error_file"],
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)


# Auto-configure based on environment
import os
if os.getenv("ENVIRONMENT") == "production":
    configure_production_logging()
else:
    configure_development_logging()