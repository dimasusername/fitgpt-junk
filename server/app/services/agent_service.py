"""
Agent service for managing ReAct agent interactions and monitoring.

This module provides a high-level interface for the ReAct agent system,
including session management, monitoring, and error recovery.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
from collections import defaultdict
import json

from app.services.react_agent import ReActAgent, AgentSession, AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentMonitor:
    """Monitor agent performance and usage statistics."""
    
    def __init__(self):
        """Initialize the agent monitor."""
        self.session_stats = defaultdict(int)
        self.tool_usage_stats = defaultdict(int)
        self.error_stats = defaultdict(int)
        self.performance_stats = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "average_session_time": 0.0,
            "average_tool_calls_per_session": 0.0,
            "total_tool_calls": 0
        }
        self.recent_sessions = []  # Keep last 100 sessions for analysis
        self.max_recent_sessions = 100
    
    def record_session(self, session: AgentSession):
        """Record a completed session for monitoring."""
        try:
            # Update basic stats
            self.performance_stats["total_sessions"] += 1
            
            if session.success:
                self.performance_stats["successful_sessions"] += 1
            else:
                self.performance_stats["failed_sessions"] += 1
                if session.error:
                    self.error_stats[session.error] += 1
            
            # Calculate session duration
            if session.session_end and session.session_start:
                duration = (session.session_end - session.session_start).total_seconds()
                
                # Update average session time
                total_sessions = self.performance_stats["total_sessions"]
                current_avg = self.performance_stats["average_session_time"]
                self.performance_stats["average_session_time"] = (
                    (current_avg * (total_sessions - 1) + duration) / total_sessions
                )
            
            # Update tool usage stats
            self.performance_stats["total_tool_calls"] += session.total_tool_calls
            
            # Update average tool calls per session
            total_sessions = self.performance_stats["total_sessions"]
            total_tool_calls = self.performance_stats["total_tool_calls"]
            self.performance_stats["average_tool_calls_per_session"] = (
                total_tool_calls / total_sessions if total_sessions > 0 else 0
            )
            
            # Record tool usage by type
            for step in session.reasoning_steps:
                for tool_call in step.tool_calls:
                    if tool_call.success:
                        self.tool_usage_stats[tool_call.tool_name] += 1
                    else:
                        self.error_stats[f"tool_{tool_call.tool_name}_error"] += 1
            
            # Keep recent sessions for analysis
            self.recent_sessions.append({
                "session_id": session.session_id,
                "query": session.query[:100] + "..." if len(session.query) > 100 else session.query,
                "success": session.success,
                "tool_calls": session.total_tool_calls,
                "duration": (session.session_end - session.session_start).total_seconds() if session.session_end else 0,
                "timestamp": session.session_start.isoformat(),
                "error": session.error
            })
            
            # Trim recent sessions if needed
            if len(self.recent_sessions) > self.max_recent_sessions:
                self.recent_sessions = self.recent_sessions[-self.max_recent_sessions:]
            
            logger.info(f"Recorded session {session.session_id}: success={session.success}, tools={session.total_tool_calls}")
            
        except Exception as e:
            logger.error(f"Failed to record session stats: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics."""
        return {
            "performance": dict(self.performance_stats),
            "tool_usage": dict(self.tool_usage_stats),
            "errors": dict(self.error_stats),
            "recent_sessions": self.recent_sessions[-10:],  # Last 10 sessions
            "timestamp": datetime.now().isoformat()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status."""
        total_sessions = self.performance_stats["total_sessions"]
        successful_sessions = self.performance_stats["successful_sessions"]
        
        if total_sessions == 0:
            success_rate = 1.0
            status = "healthy"
        else:
            success_rate = successful_sessions / total_sessions
            if success_rate >= 0.9:
                status = "healthy"
            elif success_rate >= 0.7:
                status = "degraded"
            else:
                status = "unhealthy"
        
        # Check recent error patterns
        recent_errors = sum(1 for session in self.recent_sessions[-10:] if not session["success"])
        if recent_errors >= 5:
            status = "unhealthy"
        elif recent_errors >= 3:
            status = "degraded"
        
        return {
            "status": status,
            "success_rate": success_rate,
            "total_sessions": total_sessions,
            "recent_errors": recent_errors,
            "average_response_time": self.performance_stats["average_session_time"],
            "timestamp": datetime.now().isoformat()
        }


class AgentService:
    """
    High-level service for managing ReAct agent interactions.
    
    Provides session management, monitoring, error recovery, and
    a simplified interface for agent interactions.
    """
    
    def __init__(self):
        """Initialize the agent service."""
        self.agent = ReActAgent(
            max_iterations=settings.GEMINI_MODEL.endswith("flash") and 5 or 3,  # More iterations for flash models
            temperature=0.3
        )
        self.monitor = AgentMonitor()
        self.active_sessions = {}  # Track active sessions
        self.session_timeout = timedelta(minutes=30)  # Session timeout
    
    async def process_query(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a query using the ReAct agent.
        
        Args:
            query: The user's query
            session_id: Optional session ID for tracking
            context: Optional context information
            
        Returns:
            Dictionary with agent response and metadata
        """
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Clean up expired sessions
            await self._cleanup_expired_sessions()
            
            # Process the query
            session = await self.agent.process_query(query, session_id)
            
            # Record session for monitoring
            self.monitor.record_session(session)
            
            # Store active session
            if session.session_id:
                self.active_sessions[session.session_id] = {
                    "session": session,
                    "last_activity": datetime.now()
                }
            
            # Format response
            response = {
                "session_id": session.session_id,
                "query": session.query,
                "answer": session.final_answer,
                "success": session.success,
                "error": session.error,
                "reasoning_steps": len(session.reasoning_steps),
                "tool_calls": session.total_tool_calls,
                "session_duration": (
                    (session.session_end - session.session_start).total_seconds()
                    if session.session_end else 0
                ),
                "detailed_reasoning": [
                    {
                        "step": step.step_number,
                        "thought": step.thought,
                        "action": step.action,
                        "observation": step.observation,
                        "tools_used": [tc.tool_name for tc in step.tool_calls if tc.success]
                    }
                    for step in session.reasoning_steps
                ],
                "timestamp": session.session_start.isoformat()
            }
            
            logger.info(f"Query processed successfully: {session.session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}")
            
            # Record error for monitoring
            error_session = AgentSession(
                session_id=session_id or f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                query=query,
                error=str(e),
                success=False
            )
            error_session.session_end = datetime.now()
            self.monitor.record_session(error_session)
            
            return {
                "session_id": error_session.session_id,
                "query": query,
                "answer": None,
                "success": False,
                "error": str(e),
                "reasoning_steps": 0,
                "tool_calls": 0,
                "session_duration": 0,
                "detailed_reasoning": [],
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_query_streaming(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a query with streaming updates.
        
        Args:
            query: The user's query
            session_id: Optional session ID for tracking
            context: Optional context information
            
        Yields:
            Dictionary updates with reasoning progress
        """
        try:
            logger.info(f"Processing streaming query: {query[:100]}...")
            
            # Clean up expired sessions
            await self._cleanup_expired_sessions()
            
            # Process with streaming
            session = None
            async for update in self.agent.process_query_streaming(query, session_id):
                # Store session reference when available
                if update.get("type") == "session_complete":
                    session = AgentSession(
                        session_id=update["session"]["session_id"],
                        query=update["session"]["query"],
                        final_answer=update["session"]["final_answer"],
                        success=update["session"]["success"],
                        error=update["session"]["error"],
                        total_tool_calls=update["session"]["total_tool_calls"]
                    )
                    session.session_start = datetime.fromisoformat(update["session"]["session_start"])
                    if update["session"]["session_end"]:
                        session.session_end = datetime.fromisoformat(update["session"]["session_end"])
                
                yield update
            
            # Record session for monitoring if available
            if session:
                self.monitor.record_session(session)
                
                # Store active session
                self.active_sessions[session.session_id] = {
                    "session": session,
                    "last_activity": datetime.now()
                }
            
        except Exception as e:
            logger.error(f"Failed to process streaming query: {str(e)}")
            
            # Yield error update
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific session.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            Session details or None if not found
        """
        try:
            session_data = self.active_sessions.get(session_id)
            if not session_data:
                return None
            
            session = session_data["session"]
            return {
                "session_id": session.session_id,
                "query": session.query,
                "answer": session.final_answer,
                "success": session.success,
                "error": session.error,
                "reasoning_steps": [
                    {
                        "step": step.step_number,
                        "state": step.state.value,
                        "thought": step.thought,
                        "action": step.action,
                        "observation": step.observation,
                        "tool_calls": [
                            {
                                "tool": tc.tool_name,
                                "arguments": tc.arguments,
                                "success": tc.success,
                                "execution_time": tc.execution_time,
                                "error": tc.error
                            }
                            for tc in step.tool_calls
                        ]
                    }
                    for step in session.reasoning_steps
                ],
                "total_tool_calls": session.total_tool_calls,
                "session_start": session.session_start.isoformat(),
                "session_end": session.session_end.isoformat() if session.session_end else None,
                "last_activity": session_data["last_activity"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {str(e)}")
            return None
    
    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active sessions.
        
        Returns:
            List of active session summaries
        """
        try:
            await self._cleanup_expired_sessions()
            
            sessions = []
            for session_id, session_data in self.active_sessions.items():
                session = session_data["session"]
                sessions.append({
                    "session_id": session_id,
                    "query": session.query[:100] + "..." if len(session.query) > 100 else session.query,
                    "success": session.success,
                    "tool_calls": session.total_tool_calls,
                    "session_start": session.session_start.isoformat(),
                    "last_activity": session_data["last_activity"].isoformat()
                })
            
            return sorted(sessions, key=lambda x: x["last_activity"], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list active sessions: {str(e)}")
            return []
    
    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """
        Get agent monitoring statistics.
        
        Returns:
            Dictionary with performance and usage statistics
        """
        try:
            stats = self.monitor.get_stats()
            health = self.monitor.get_health_status()
            
            return {
                "health": health,
                "statistics": stats,
                "active_sessions": len(self.active_sessions),
                "agent_config": {
                    "model": settings.GEMINI_MODEL,
                    "max_iterations": self.agent.max_iterations,
                    "temperature": self.agent.temperature,
                    "available_tools": list(self.agent.available_tools.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get monitoring stats: {str(e)}")
            return {
                "health": {"status": "error", "error": str(e)},
                "statistics": {},
                "active_sessions": 0,
                "agent_config": {}
            }
    
    async def clear_session(self, session_id: str) -> bool:
        """
        Clear a specific session from memory.
        
        Args:
            session_id: The session ID to clear
            
        Returns:
            True if session was cleared, False if not found
        """
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Cleared session: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to clear session {session_id}: {str(e)}")
            return False
    
    async def clear_all_sessions(self) -> int:
        """
        Clear all active sessions from memory.
        
        Returns:
            Number of sessions cleared
        """
        try:
            count = len(self.active_sessions)
            self.active_sessions.clear()
            logger.info(f"Cleared {count} active sessions")
            return count
            
        except Exception as e:
            logger.error(f"Failed to clear all sessions: {str(e)}")
            return 0
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions from memory."""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session_data in self.active_sessions.items():
                if current_time - session_data["last_activity"] > self.session_timeout:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}")


# Global agent service instance
agent_service = AgentService()