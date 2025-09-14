"""
Unit tests for the ReAct agent system.

Tests the core functionality of the ReAct agent including reasoning,
tool execution, error handling, and session management.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.react_agent import (
    ReActAgent, 
    AgentState, 
    ReasoningStep, 
    ToolCall, 
    AgentSession
)
from app.services.agent_service import AgentService, AgentMonitor


class TestReActAgent:
    """Test cases for the ReAct agent."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock ReAct agent for testing."""
        with patch('app.services.react_agent.genai') as mock_genai:
            mock_genai.configure = Mock()
            mock_genai.GenerativeModel = Mock()
            
            agent = ReActAgent(max_iterations=3, temperature=0.3)
            agent.model = Mock()
            return agent
    
    def test_agent_initialization(self, mock_agent):
        """Test agent initialization."""
        assert mock_agent.max_iterations == 3
        assert mock_agent.temperature == 0.3
        assert mock_agent.available_tools is not None
        assert len(mock_agent.available_tools) > 0
    
    def test_build_system_prompt(self, mock_agent):
        """Test system prompt generation."""
        prompt = mock_agent._build_system_prompt()
        
        assert "ReAct" in prompt
        assert "Thought:" in prompt
        assert "Action:" in prompt
        assert "Observation:" in prompt
        assert "search_documents" in prompt
        assert "build_timeline" in prompt
    
    def test_parse_reasoning_response_thinking(self, mock_agent):
        """Test parsing a thinking response."""
        response_text = "Thought: I need to search for information about Roman legions."
        
        step = mock_agent._parse_reasoning_response(response_text, 1)
        
        assert step.step_number == 1
        assert step.state == AgentState.THINKING
        assert "Roman legions" in step.thought
        assert step.action is None
    
    def test_parse_reasoning_response_with_action(self, mock_agent):
        """Test parsing a response with action."""
        response_text = """Thought: I need to search for Roman military information.
Action: search_documents(query="Roman legions military organization")"""
        
        step = mock_agent._parse_reasoning_response(response_text, 1)
        
        assert step.step_number == 1
        assert step.state == AgentState.ACTING
        assert "Roman military" in step.thought
        assert "search_documents" in step.action
    
    def test_parse_reasoning_response_final_answer(self, mock_agent):
        """Test parsing a final answer response."""
        response_text = """Thought: Based on my research, I can now provide a complete answer.
Action: Final Answer
Observation: Roman legions were highly organized military units..."""
        
        step = mock_agent._parse_reasoning_response(response_text, 1)
        
        assert step.step_number == 1
        assert step.state == AgentState.COMPLETED
        assert "complete answer" in step.thought
        assert "Final Answer" in step.action
        assert "Roman legions" in step.observation
    
    def test_parse_tool_calls_simple(self, mock_agent):
        """Test parsing simple tool calls."""
        action = 'search_documents(query="Roman military")'
        
        tool_calls = mock_agent._parse_tool_calls(action)
        
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_name == "search_documents"
        assert tool_calls[0].arguments["query"] == "Roman military"
    
    def test_parse_tool_calls_multiple_params(self, mock_agent):
        """Test parsing tool calls with multiple parameters."""
        action = 'cross_reference_documents(topic="Roman tactics", document_ids=None)'
        
        tool_calls = mock_agent._parse_tool_calls(action)
        
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_name == "cross_reference_documents"
        assert tool_calls[0].arguments["topic"] == "Roman tactics"
        assert tool_calls[0].arguments["document_ids"] is None
    
    def test_format_tool_result_search(self, mock_agent):
        """Test formatting search tool results."""
        result = {
            "total_results": 2,
            "results": [
                {
                    "document_name": "Roman Military.pdf",
                    "page_number": 15,
                    "content": "Roman legions were organized into cohorts and centuries..."
                },
                {
                    "document_name": "Ancient Warfare.pdf", 
                    "page_number": 23,
                    "content": "The legion structure provided tactical flexibility..."
                }
            ]
        }
        
        formatted = mock_agent._format_tool_result("search_documents", result)
        
        assert "Found 2 results" in formatted
        assert "Roman Military.pdf" in formatted
        assert "p.15" in formatted
        assert "cohorts and centuries" in formatted
    
    def test_format_tool_result_timeline(self, mock_agent):
        """Test formatting timeline tool results."""
        result = {
            "total_events": 5,
            "timeline_summary": "Timeline covers Roman expansion from 264 BC to 146 BC.",
            "date_range": {"start": "264 BC", "end": "146 BC"}
        }
        
        formatted = mock_agent._format_tool_result("build_timeline", result)
        
        assert "5 events" in formatted
        assert "264 BC to 146 BC" in formatted
        assert "Roman expansion" in formatted
    
    def test_format_tool_result_error(self, mock_agent):
        """Test formatting tool results with errors."""
        result = {"error": "Database connection failed"}
        
        formatted = mock_agent._format_tool_result("search_documents", result)
        
        assert "failed" in formatted
        assert "Database connection failed" in formatted
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_success(self, mock_agent):
        """Test successful tool execution."""
        # Mock the tool function
        mock_result = {
            "total_results": 1,
            "results": [{"content": "Test result"}]
        }
        
        with patch('app.services.historical_tool_functions.search_documents', 
                  return_value=mock_result) as mock_tool:
            
            step = ReasoningStep(
                step_number=1,
                state=AgentState.ACTING,
                thought="Testing",
                action='search_documents(query="test")'
            )
            
            session = AgentSession(session_id="test", query="test")
            
            await mock_agent._execute_tool_calls(step, session)
            
            assert len(step.tool_calls) == 1
            assert step.tool_calls[0].success
            assert step.tool_calls[0].result == mock_result
            assert step.state == AgentState.OBSERVING
            assert "Test result" in step.observation
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_failure(self, mock_agent):
        """Test tool execution failure handling."""
        with patch('app.services.historical_tool_functions.search_documents', 
                  side_effect=Exception("Tool failed")) as mock_tool:
            
            step = ReasoningStep(
                step_number=1,
                state=AgentState.ACTING,
                thought="Testing",
                action='search_documents(query="test")'
            )
            
            session = AgentSession(session_id="test", query="test")
            
            await mock_agent._execute_tool_calls(step, session)
            
            assert len(step.tool_calls) == 1
            assert not step.tool_calls[0].success
            assert step.tool_calls[0].error == "Tool failed"
            assert "failed" in step.observation


class TestAgentMonitor:
    """Test cases for the agent monitor."""
    
    @pytest.fixture
    def monitor(self):
        """Create an agent monitor for testing."""
        return AgentMonitor()
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor.performance_stats["total_sessions"] == 0
        assert monitor.performance_stats["successful_sessions"] == 0
        assert monitor.performance_stats["failed_sessions"] == 0
        assert len(monitor.recent_sessions) == 0
    
    def test_record_successful_session(self, monitor):
        """Test recording a successful session."""
        session = AgentSession(
            session_id="test_1",
            query="Test query",
            success=True,
            total_tool_calls=2
        )
        session.session_end = datetime.now()
        
        monitor.record_session(session)
        
        assert monitor.performance_stats["total_sessions"] == 1
        assert monitor.performance_stats["successful_sessions"] == 1
        assert monitor.performance_stats["failed_sessions"] == 0
        assert monitor.performance_stats["total_tool_calls"] == 2
        assert len(monitor.recent_sessions) == 1
    
    def test_record_failed_session(self, monitor):
        """Test recording a failed session."""
        session = AgentSession(
            session_id="test_2",
            query="Test query",
            success=False,
            error="Test error",
            total_tool_calls=0
        )
        session.session_end = datetime.now()
        
        monitor.record_session(session)
        
        assert monitor.performance_stats["total_sessions"] == 1
        assert monitor.performance_stats["successful_sessions"] == 0
        assert monitor.performance_stats["failed_sessions"] == 1
        assert monitor.error_stats["Test error"] == 1
    
    def test_get_health_status_healthy(self, monitor):
        """Test health status when system is healthy."""
        # Record several successful sessions
        for i in range(10):
            session = AgentSession(
                session_id=f"test_{i}",
                query="Test query",
                success=True,
                total_tool_calls=1
            )
            session.session_end = datetime.now()
            monitor.record_session(session)
        
        health = monitor.get_health_status()
        
        assert health["status"] == "healthy"
        assert health["success_rate"] == 1.0
        assert health["total_sessions"] == 10
        assert health["recent_errors"] == 0
    
    def test_get_health_status_degraded(self, monitor):
        """Test health status when system is degraded."""
        # Record mixed success/failure sessions
        for i in range(10):
            session = AgentSession(
                session_id=f"test_{i}",
                query="Test query",
                success=i < 8,  # 80% success rate
                total_tool_calls=1
            )
            session.session_end = datetime.now()
            monitor.record_session(session)
        
        health = monitor.get_health_status()
        
        assert health["status"] == "degraded"
        assert health["success_rate"] == 0.8
        assert health["total_sessions"] == 10
    
    def test_get_health_status_unhealthy(self, monitor):
        """Test health status when system is unhealthy."""
        # Record mostly failed sessions
        for i in range(10):
            session = AgentSession(
                session_id=f"test_{i}",
                query="Test query",
                success=i < 5,  # 50% success rate
                total_tool_calls=1
            )
            session.session_end = datetime.now()
            monitor.record_session(session)
        
        health = monitor.get_health_status()
        
        assert health["status"] == "unhealthy"
        assert health["success_rate"] == 0.5
        assert health["total_sessions"] == 10


class TestAgentService:
    """Test cases for the agent service."""
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock agent service for testing."""
        with patch('app.services.agent_service.ReActAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            service = AgentService()
            service.agent = mock_agent
            return service, mock_agent
    
    @pytest.mark.asyncio
    async def test_process_query_success(self, mock_service):
        """Test successful query processing."""
        service, mock_agent = mock_service
        
        # Mock successful session
        mock_session = AgentSession(
            session_id="test_session",
            query="Test query",
            final_answer="Test answer",
            success=True,
            total_tool_calls=1
        )
        mock_session.session_end = datetime.now()
        
        mock_agent.process_query = AsyncMock(return_value=mock_session)
        
        result = await service.process_query("Test query")
        
        assert result["success"] is True
        assert result["answer"] == "Test answer"
        assert result["session_id"] == "test_session"
        assert result["tool_calls"] == 1
    
    @pytest.mark.asyncio
    async def test_process_query_failure(self, mock_service):
        """Test query processing failure handling."""
        service, mock_agent = mock_service
        
        mock_agent.process_query = AsyncMock(side_effect=Exception("Processing failed"))
        
        result = await service.process_query("Test query")
        
        assert result["success"] is False
        assert "Processing failed" in result["error"]
        assert result["answer"] is None
    
    @pytest.mark.asyncio
    async def test_get_monitoring_stats(self, mock_service):
        """Test getting monitoring statistics."""
        service, mock_agent = mock_service
        
        # Add some test data to monitor
        test_session = AgentSession(
            session_id="test",
            query="Test",
            success=True,
            total_tool_calls=2
        )
        test_session.session_end = datetime.now()
        service.monitor.record_session(test_session)
        
        stats = await service.get_monitoring_stats()
        
        assert "health" in stats
        assert "statistics" in stats
        assert "active_sessions" in stats
        assert "agent_config" in stats
        assert stats["statistics"]["performance"]["total_sessions"] == 1
    
    @pytest.mark.asyncio
    async def test_session_management(self, mock_service):
        """Test session management operations."""
        service, mock_agent = mock_service
        
        # Create a test session
        test_session = AgentSession(
            session_id="test_session",
            query="Test query",
            success=True
        )
        
        service.active_sessions["test_session"] = {
            "session": test_session,
            "last_activity": datetime.now()
        }
        
        # Test getting session
        session_details = await service.get_session("test_session")
        assert session_details is not None
        assert session_details["session_id"] == "test_session"
        
        # Test listing sessions
        sessions = await service.list_active_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "test_session"
        
        # Test clearing session
        success = await service.clear_session("test_session")
        assert success is True
        assert "test_session" not in service.active_sessions
        
        # Test clearing non-existent session
        success = await service.clear_session("non_existent")
        assert success is False


if __name__ == "__main__":
    pytest.main([__file__])