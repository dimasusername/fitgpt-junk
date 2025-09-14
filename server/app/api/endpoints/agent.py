"""
Agent API endpoints for ReAct agent interactions.

This module provides REST API endpoints for interacting with the ReAct agent system,
including query processing, session management, and monitoring.
"""
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from app.services.agent_service import agent_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class AgentQueryRequest(BaseModel):
    """Request model for agent queries."""
    query: str = Field(..., description="The user's query", min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context information")
    stream: bool = Field(False, description="Whether to stream the response")


class AgentQueryResponse(BaseModel):
    """Response model for agent queries."""
    session_id: str
    query: str
    answer: Optional[str]
    success: bool
    error: Optional[str]
    reasoning_steps: int
    tool_calls: int
    session_duration: float
    detailed_reasoning: List[Dict[str, Any]]
    timestamp: str


class SessionSummary(BaseModel):
    """Summary model for active sessions."""
    session_id: str
    query: str
    success: bool
    tool_calls: int
    session_start: str
    last_activity: str


class MonitoringStats(BaseModel):
    """Model for monitoring statistics."""
    health: Dict[str, Any]
    statistics: Dict[str, Any]
    active_sessions: int
    agent_config: Dict[str, Any]


@router.post("/query", response_model=AgentQueryResponse)
async def process_agent_query(
    request: AgentQueryRequest,
    background_tasks: BackgroundTasks
) -> AgentQueryResponse:
    """
    Process a query using the ReAct agent.
    
    This endpoint processes user queries through the ReAct agent system,
    which can reason about problems and use tools to provide comprehensive answers.
    """
    try:
        logger.info(f"Received agent query: {request.query[:100]}...")
        
        if request.stream:
            raise HTTPException(
                status_code=400,
                detail="Use /query/stream endpoint for streaming responses"
            )
        
        # Process the query
        result = await agent_service.process_query(
            query=request.query,
            session_id=request.session_id,
            context=request.context
        )
        
        return AgentQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Agent query processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent query processing failed: {str(e)}"
        )


@router.post("/query/stream")
async def process_agent_query_streaming(request: AgentQueryRequest):
    """
    Process a query using the ReAct agent with streaming responses.
    
    This endpoint provides real-time updates as the agent reasons through
    the problem and executes tools.
    """
    try:
        logger.info(f"Received streaming agent query: {request.query[:100]}...")
        
        async def generate_stream():
            """Generate streaming response."""
            try:
                async for update in agent_service.process_query_streaming(
                    query=request.query,
                    session_id=request.session_id,
                    context=request.context
                ):
                    # Format as Server-Sent Events
                    data = json.dumps(update)
                    yield f"data: {data}\n\n"
                
                # Send completion signal
                yield "data: {\"type\": \"stream_complete\"}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                error_data = json.dumps({
                    "type": "error",
                    "error": str(e)
                })
                yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming agent query failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Streaming agent query failed: {str(e)}"
        )


@router.get("/sessions", response_model=List[SessionSummary])
async def list_active_sessions() -> List[SessionSummary]:
    """
    List all active agent sessions.
    
    Returns a list of currently active agent sessions with basic information.
    """
    try:
        sessions = await agent_service.list_active_sessions()
        return [SessionSummary(**session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Failed to list active sessions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list active sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}")
async def get_session_details(session_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific agent session.
    
    Returns complete session details including reasoning steps and tool usage.
    """
    try:
        session = await agent_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session details: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str) -> Dict[str, Any]:
    """
    Clear a specific agent session from memory.
    
    Removes the session and its associated data from active memory.
    """
    try:
        success = await agent_service.clear_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        return {
            "message": f"Session {session_id} cleared successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear session: {str(e)}"
        )


@router.delete("/sessions")
async def clear_all_sessions() -> Dict[str, Any]:
    """
    Clear all active agent sessions from memory.
    
    Removes all sessions and their associated data from active memory.
    """
    try:
        count = await agent_service.clear_all_sessions()
        
        return {
            "message": f"Cleared {count} active sessions",
            "sessions_cleared": count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear all sessions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear all sessions: {str(e)}"
        )


@router.get("/monitoring", response_model=MonitoringStats)
async def get_monitoring_stats() -> MonitoringStats:
    """
    Get agent monitoring statistics and health information.
    
    Returns performance metrics, usage statistics, and health status.
    """
    try:
        stats = await agent_service.get_monitoring_stats()
        return MonitoringStats(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get monitoring stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monitoring stats: {str(e)}"
        )


@router.get("/health")
async def get_agent_health() -> Dict[str, Any]:
    """
    Get agent health status.
    
    Returns basic health information for monitoring and alerting.
    """
    try:
        stats = await agent_service.get_monitoring_stats()
        health = stats.get("health", {})
        
        return {
            "status": health.get("status", "unknown"),
            "success_rate": health.get("success_rate", 0.0),
            "total_sessions": health.get("total_sessions", 0),
            "recent_errors": health.get("recent_errors", 0),
            "average_response_time": health.get("average_response_time", 0.0),
            "active_sessions": stats.get("active_sessions", 0),
            "timestamp": health.get("timestamp", ""),
            "model": stats.get("agent_config", {}).get("model", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent health: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": ""
        }


@router.get("/tools")
async def list_available_tools() -> Dict[str, Any]:
    """
    List all available tools that the agent can use.
    
    Returns information about available tools and their capabilities.
    """
    try:
        from app.services.historical_tool_functions import list_available_tools
        
        tools = list_available_tools()
        
        return {
            "total_tools": len(tools),
            "tools": tools,
            "categories": {
                "search": ["search_documents"],
                "analysis": ["build_timeline", "extract_entities", "cross_reference_documents"],
                "formatting": ["generate_citations"]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list available tools: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list available tools: {str(e)}"
        )


# Add router tags and metadata
router.tags = ["Agent"]