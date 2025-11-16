#!/usr/bin/env python3
"""
Jaseci Learning Companion - OSP Graph Service Client
Client for OSP Graph Service integration

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/
"""

import os
import logging
from typing import Dict, Any, List, Optional
import aiohttp
import json

logger = logging.getLogger(__name__)

class OSPGraphServiceClient:
    """Client for OSP Graph Service"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_jaseci_code(self, code: str, project_id: str) -> Dict[str, Any]:
        """Analyze Jaseci code and generate OSP graph"""
        try:
            payload = {
                "code": code,
                "project_id": project_id,
                "analysis_type": "full"
            }
            
            async with self.session.post(
                f"{self.base_url}/analyze/jaseci",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"OSP analysis error: {response.status} - {error_text}")
                    return {"error": f"Analysis failed: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {"error": f"Analysis service error: {str(e)}"}
    
    async def get_graph_visualization(self, project_id: str) -> Dict[str, Any]:
        """Get graph visualization data"""
        try:
            async with self.session.get(
                f"{self.base_url}/graph/visualization/{project_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Graph visualization error: {response.status} - {error_text}")
                    return {"error": f"Visualization failed: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error getting graph visualization: {e}")
            return {"error": f"Visualization service error: {str(e)}"}
    
    async def get_complexity_metrics(self, project_id: str) -> Dict[str, Any]:
        """Get complexity metrics for project"""
        try:
            async with self.session.get(
                f"{self.base_url}/analytics/metrics/{project_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Metrics error: {response.status} - {error_text}")
                    return {"error": f"Metrics failed: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {"error": f"Metrics service error: {str(e)}"}
    
    async def get_patterns_detected(self, project_id: str) -> Dict[str, Any]:
        """Get detected design patterns"""
        try:
            async with self.session.get(
                f"{self.base_url}/analytics/patterns/{project_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Pattern detection error: {response.status} - {error_text}")
                    return {"error": f"Pattern detection failed: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error getting patterns: {e}")
            return {"error": f"Pattern detection service error: {str(e)}"}
    
    async def get_anti_patterns_detected(self, project_id: str) -> Dict[str, Any]:
        """Get detected anti-patterns"""
        try:
            async with self.session.get(
                f"{self.base_url}/analytics/anti-patterns/{project_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Anti-pattern detection error: {response.status} - {error_text}")
                    return {"error": f"Anti-pattern detection failed: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error getting anti-patterns: {e}")
            return {"error": f"Anti-pattern detection service error: {str(e)}"}
    
    async def search_graph_nodes(self, project_id: str, query: str) -> Dict[str, Any]:
        """Search graph nodes"""
        try:
            params = {"query": query}
            async with self.session.get(
                f"{self.base_url}/graph/search/{project_id}",
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Graph search error: {response.status} - {error_text}")
                    return {"error": f"Search failed: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error searching graph: {e}")
            return {"error": f"Search service error: {str(e)}"}
    
    async def export_graph_data(self, project_id: str, format: str = "json") -> Dict[str, Any]:
        """Export graph data"""
        try:
            params = {"format": format}
            async with self.session.get(
                f"{self.base_url}/graph/export/{project_id}",
                params=params
            ) as response:
                if response.status == 200:
                    if format == "json":
                        return await response.json()
                    else:
                        return {"data": await response.read(), "format": format}
                else:
                    error_text = await response.text()
                    logger.error(f"Graph export error: {response.status} - {error_text}")
                    return {"error": f"Export failed: {error_text}"}
                    
        except Exception as e:
            logger.error(f"Error exporting graph: {e}")
            return {"error": f"Export service error: {str(e)}"}
    
    async def health_check(self) -> bool:
        """Check OSP service health"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"OSP service health check failed: {e}")
            return False
    
    async def close(self):
        """Close client session"""
        if self.session:
            await self.session.close()
