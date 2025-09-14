"""
Integration tests for the ReAct agent system.

Tests the complete ReAct agent workflow including API endpoints,
tool integration, and end-to-end functionality.
"""
import pytest
import asyncio
import json
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.services.agent_service import agent_service
from app.services.react_agent import AgentSession


class TestReActAgentIntegration:
    """Integration tests for the ReAct agent system."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Create an async test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.fixture
    def mock_gemini_response(self):
        """Mock Gemini API response."""
        mock_response = Mock()
        mock_response.text = """Thought: I need to search for information about Roman military organization.
Action: search_documents(query="Roman legion military organization")"""
        return mock_response
    
    @pytest.fixture
    def mock_tool_result(self):
        """Mock tool execution result."""
        return {
            "total_results": 2,
            "results": [
                {
                    "document_name": "Roman Military.pdf",
                    "page_number": 15,
                    "content": "Roman legions were organized into cohorts of 480 men each...",
                    "similarity_score": 0.85
                },
                {
                    "document_name": "Ancient Warfare.pdf",
                    "page_number": 23,
                    "content": "The legion structure provided tactical flexibility in battle...",
                    "similarity_score": 0.78
                }
            ],
            "enhanced_query": "Roman legion military organization structure cohorts centuries",
            "search_strategy": "historical_terminology_optimized"
        }
    
    def test_agent_health_endpoint(self, client):
        """Test the agent health endpoint."""
        response = client.get("/api/v1/agent/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "success_rate" in data
        assert "total_sessions" in data
        assert "timestamp" in data
    
    def test_list_available_tools_endpoint(self, client):
        """Test the list available tools endpoint."""
        response = client.get("/api/v1/agent/tools")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_tools" in data
        assert "tools" in data
        assert "categories" in data
        
        # Check that expected tools are present
        tools = data["tools"]
        assert "search_documents" in tools
        assert "build_timeline" in tools
        assert "extract_entities" in tools
        assert "cross_reference_documents" in tools
        assert "generate_citations" in tools
    
    @patch('app.services.react_agent.genai')
    @patch('app.services.historical_tool_functions.search_documents')
    def test_agent_query_endpoint(self, mock_search_tool, mock_genai, client, mock_gemini_response, mock_tool_result):
        """Test the agent query endpoint with mocked dependencies."""
        # Mock Gemini API
        mock_genai.configure = Mock()
        mock_model = Mock()
        mock_model.generate_content = Mock(return_value=mock_gemini_response)
        mock_genai.GenerativeModel = Mock(return_value=mock_model)
        
        # Mock tool execution
        mock_search_tool.return_value = mock_tool_result
        
        # Make request
        response = client.post("/api/v1/agent/query", json={
            "query": "What can you tell me about Roman military organization?",
            "session_id": "test_session"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == "test_session"
        assert data["query"] == "What can you tell me about Roman military organization?"
        assert "answer" in data
        assert "reasoning_steps" in data
        assert "tool_calls" in data
        assert "detailed_reasoning" in data
    
    def test_agent_query_endpoint_validation(self, client):
        """Test agent query endpoint input validation."""
        # Test empty query
        response = client.post("/api/v1/agent/query", json={
            "query": ""
        })
        assert response.status_code == 422  # Validation error
        
        # Test missing query
        response = client.post("/api/v1/agent/query", json={})
        assert response.status_code == 422  # Validation error
        
        # Test query too long
        long_query = "x" * 3000
        response = client.post("/api/v1/agent/query", json={
            "query": long_query
        })
        assert response.status_code == 422  # Validation error
    
    def test_session_management_endpoints(self, client):
        """Test session management endpoints."""
        # Initially no sessions
        response = client.get("/api/v1/agent/sessions")
        assert response.status_code == 200
        assert response.json() == []
        
        # Clear all sessions (should work even with no sessions)
        response = client.delete("/api/v1/agent/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions_cleared" in data
        
        # Try to get non-existent session
        response = client.get("/api/v1/agent/sessions/non_existent")
        assert response.status_code == 404
        
        # Try to clear non-existent session
        response = client.delete("/api/v1/agent/sessions/non_existent")
        assert response.status_code == 404
    
    def test_monitoring_endpoint(self, client):
        """Test the monitoring endpoint."""
        response = client.get("/api/v1/agent/monitoring")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "health" in data
        assert "statistics" in data
        assert "active_sessions" in data
        assert "agent_config" in data
        
        # Check health structure
        health = data["health"]
        assert "status" in health
        assert "success_rate" in health
        assert "total_sessions" in health
        
        # Check statistics structure
        stats = data["statistics"]
        assert "performance" in stats
        assert "tool_usage" in stats
        assert "errors" in stats
        
        # Check agent config
        config = data["agent_config"]
        assert "model" in config
        assert "available_tools" in config
    
    @pytest.mark.asyncio
    async def test_streaming_endpoint_format(self, async_client):
        """Test that streaming endpoint returns proper format."""
        with patch('app.services.agent_service.agent_service.process_query_streaming') as mock_stream:
            # Mock streaming updates
            async def mock_streaming_generator():
                yield {"type": "session_start", "session_id": "test", "query": "test"}
                yield {"type": "step_start", "step_number": 1, "state": "thinking"}
                yield {"type": "session_complete", "success": True, "final_answer": "Test answer"}
            
            mock_stream.return_value = mock_streaming_generator()
            
            response = await async_client.post("/api/v1/agent/query/stream", json={
                "query": "Test streaming query"
            })
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"
            
            # Check that response contains SSE format
            content = response.text
            assert "data: " in content
            assert "session_start" in content
            assert "session_complete" in content
    
    @pytest.mark.asyncio
    async def test_agent_service_integration(self):
        """Test agent service integration without HTTP layer."""
        with patch('app.services.react_agent.genai') as mock_genai:
            # Mock Gemini API
            mock_genai.configure = Mock()
            mock_response = Mock()
            mock_response.text = """Thought: I can provide information about Roman military organization.
Action: Final Answer
Observation: Roman legions were highly organized military units consisting of approximately 5,000 soldiers."""
            
            mock_model = Mock()
            mock_model.generate_content = Mock(return_value=mock_response)
            mock_genai.GenerativeModel = Mock(return_value=mock_model)
            
            # Test direct service call
            result = await agent_service.process_query(
                "Tell me about Roman military organization",
                session_id="integration_test"
            )
            
            assert result["success"] is True
            assert result["session_id"] == "integration_test"
            assert "Roman legions" in result["answer"]
            assert result["reasoning_steps"] >= 1
    
    @pytest.mark.asyncio
    async def test_tool_integration_flow(self):
        """Test the complete tool integration flow."""
        with patch('app.services.react_agent.genai') as mock_genai, \
             patch('app.services.historical_tool_functions.search_documents') as mock_search:
            
            # Mock Gemini responses for multi-step reasoning
            responses = [
                # First response: decide to search
                Mock(text="""Thought: I need to search for information about Roman military tactics.
Action: search_documents(query="Roman military tactics legion formation")"""),
                
                # Second response: provide final answer
                Mock(text="""Thought: Based on the search results, I can now provide a comprehensive answer.
Action: Final Answer
Observation: Based on the historical documents, Roman military tactics were highly sophisticated...""")
            ]
            
            mock_genai.configure = Mock()
            mock_model = Mock()
            mock_model.generate_content = Mock(side_effect=responses)
            mock_genai.GenerativeModel = Mock(return_value=mock_model)
            
            # Mock tool result
            mock_search.return_value = {
                "total_results": 1,
                "results": [{
                    "document_name": "Roman Tactics.pdf",
                    "content": "Roman legions used flexible formations...",
                    "page_number": 42
                }],
                "enhanced_query": "Roman military tactics legion formation",
                "search_strategy": "historical_terminology_optimized"
            }
            
            # Process query
            result = await agent_service.process_query(
                "What were Roman military tactics like?",
                session_id="tool_integration_test"
            )
            
            assert result["success"] is True
            assert result["tool_calls"] >= 1
            assert len(result["detailed_reasoning"]) >= 2
            
            # Check that search tool was called
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert "Roman military tactics" in call_args[1]["query"]
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(self):
        """Test error recovery in the integration flow."""
        with patch('app.services.react_agent.genai') as mock_genai, \
             patch('app.services.historical_tool_functions.search_documents') as mock_search:
            
            # Mock Gemini API
            mock_genai.configure = Mock()
            mock_response = Mock()
            mock_response.text = """Thought: I'll search for information.
Action: search_documents(query="test query")"""
            
            mock_model = Mock()
            mock_model.generate_content = Mock(return_value=mock_response)
            mock_genai.GenerativeModel = Mock(return_value=mock_model)
            
            # Mock tool failure
            mock_search.side_effect = Exception("Database connection failed")
            
            # Process query
            result = await agent_service.process_query(
                "Test error recovery",
                session_id="error_recovery_test"
            )
            
            # Should handle error gracefully
            assert result["session_id"] == "error_recovery_test"
            # May succeed or fail depending on error recovery, but shouldn't crash
            assert "reasoning_steps" in result
    
    @pytest.mark.asyncio
    async def test_session_lifecycle_integration(self):
        """Test complete session lifecycle."""
        # Create session
        with patch('app.services.react_agent.genai') as mock_genai:
            mock_genai.configure = Mock()
            mock_response = Mock()
            mock_response.text = """Thought: I can answer this directly.
Action: Final Answer
Observation: This is a test answer."""
            
            mock_model = Mock()
            mock_model.generate_content = Mock(return_value=mock_response)
            mock_genai.GenerativeModel = Mock(return_value=mock_model)
            
            # Process query to create session
            result = await agent_service.process_query(
                "Test session lifecycle",
                session_id="lifecycle_test"
            )
            
            session_id = result["session_id"]
            assert session_id == "lifecycle_test"
            
            # Check session exists
            sessions = await agent_service.list_active_sessions()
            session_ids = [s["session_id"] for s in sessions]
            assert session_id in session_ids
            
            # Get session details
            session_details = await agent_service.get_session(session_id)
            assert session_details is not None
            assert session_details["session_id"] == session_id
            assert session_details["query"] == "Test session lifecycle"
            
            # Clear session
            success = await agent_service.clear_session(session_id)
            assert success is True
            
            # Verify session is gone
            sessions = await agent_service.list_active_sessions()
            session_ids = [s["session_id"] for s in sessions]
            assert session_id not in session_ids
    
    @pytest.mark.asyncio
    async def test_monitoring_integration(self):
        """Test monitoring integration with real session data."""
        with patch('app.services.react_agent.genai') as mock_genai:
            mock_genai.configure = Mock()
            mock_response = Mock()
            mock_response.text = """Thought: Test response.
Action: Final Answer
Observation: Test answer."""
            
            mock_model = Mock()
            mock_model.generate_content = Mock(return_value=mock_response)
            mock_genai.GenerativeModel = Mock(return_value=mock_model)
            
            # Process several queries to generate monitoring data
            for i in range(3):
                await agent_service.process_query(
                    f"Test query {i}",
                    session_id=f"monitoring_test_{i}"
                )
            
            # Get monitoring stats
            stats = await agent_service.get_monitoring_stats()
            
            assert stats["statistics"]["performance"]["total_sessions"] >= 3
            assert stats["statistics"]["performance"]["successful_sessions"] >= 0
            assert stats["health"]["total_sessions"] >= 3
            assert stats["active_sessions"] >= 0  # May be 0 if sessions expired


if __name__ == "__main__":
    pytest.main([__file__])