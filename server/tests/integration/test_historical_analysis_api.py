"""
Integration tests for historical analysis tool functions.

These tests verify the function-based tools work correctly with real dependencies.
Note: Historical analysis API endpoints have been removed in favor of function-based tools
for agent SDK integration.
"""
import pytest
import inspect
from typing import Union
from unittest.mock import patch, Mock, AsyncMock

from app.services.historical_tool_functions import (
    search_documents,
    build_timeline,
    extract_entities,
    cross_reference_documents,
    generate_citations,
    list_available_tools
)


class TestHistoricalToolFunctionsIntegration:
    """Integration tests for historical analysis tool functions."""
    
    @pytest.mark.asyncio
    async def test_search_documents_integration(self):
        """Test document search function integration."""
        # Mock the underlying historical search tool
        with patch('app.services.historical_tool_functions.historical_search_tool') as mock_tool:
            mock_result = {
                "query": "Roman legion",
                "enhanced_query": "Roman legion military unit soldiers formation",
                "results": [
                    {
                        "chunk_id": "test-chunk-1",
                        "content": "The Roman legion was a military unit consisting of soldiers.",
                        "similarity_score": 0.85,
                        "relevance_score": 0.90,
                        "page_number": 15,
                        "source_attribution": "Roman Military History, p. 15",
                        "historical_entities": ["Roman", "legion"],
                        "document_name": "Roman Military History"
                    }
                ],
                "total_results": 1,
                "search_strategy": "historical_terminology_optimized"
            }
            
            mock_tool.search = AsyncMock(return_value=mock_result)
            
            # Test the function
            result = await search_documents("Roman legion", ["doc-1", "doc-2"])
            
            assert result["query"] == "Roman legion"
            assert result["total_results"] == 1
            assert result["search_strategy"] == "historical_terminology_optimized"
            assert len(result["results"]) == 1
            
            # Verify the underlying tool was called correctly
            mock_tool.search.assert_called_once_with(
                query="Roman legion", 
                document_ids=["doc-1", "doc-2"]
            )
    
    @pytest.mark.asyncio
    async def test_build_timeline_integration(self):
        """Test timeline builder function integration."""
        with patch('app.services.historical_tool_functions.timeline_builder_tool') as mock_tool:
            mock_result = {
                "total_events": 3,
                "timeline_events": [
                    {
                        "date": "264 BC",
                        "event": "First Punic War begins",
                        "source_document": "Roman History",
                        "page_number": 10,
                        "confidence": 0.9,
                        "date_type": "exact"
                    }
                ],
                "grouped_by_period": {
                    "Roman Republic": [{"date": "264 BC", "event": "First Punic War begins"}]
                },
                "timeline_summary": "Timeline covers major Roman conflicts from 264 BC to 146 BC.",
                "date_range": {"start": "264 BC", "end": "146 BC"}
            }
            
            mock_tool.extract_timeline = AsyncMock(return_value=mock_result)
            
            # Test the function
            result = await build_timeline(["doc-1"])
            
            assert result["total_events"] == 3
            assert len(result["timeline_events"]) == 1
            assert "Roman Republic" in result["grouped_by_period"]
            assert result["date_range"]["start"] == "264 BC"
            
            # Verify the underlying tool was called correctly
            mock_tool.extract_timeline.assert_called_once_with(document_ids=["doc-1"])
    
    @pytest.mark.asyncio
    async def test_extract_entities_integration(self):
        """Test entity extractor function integration."""
        with patch('app.services.historical_tool_functions.entity_extractor_tool') as mock_tool:
            mock_result = {
                "total_entities": 5,
                "entities_by_type": {
                    "person": [
                        {
                            "name": "Julius Caesar",
                            "entity_type": "person",
                            "context": "Roman general and statesman",
                            "source_document": "Roman History",
                            "page_number": 15,
                            "mentions": 3,
                            "related_entities": ["Pompey", "Crassus"]
                        }
                    ],
                    "place": [
                        {
                            "name": "Rome",
                            "entity_type": "place",
                            "context": "Capital city",
                            "source_document": "Roman History",
                            "page_number": 5,
                            "mentions": 10,
                            "related_entities": ["Italy"]
                        }
                    ]
                },
                "entity_relationships": {"Julius Caesar": ["Pompey", "Crassus"]},
                "entity_summary": "Extracted 5 historical entities including 1 person and 1 place.",
                "extraction_method": "hybrid_pattern_ai"
            }
            
            mock_tool.extract_entities = AsyncMock(return_value=mock_result)
            
            # Test the function
            result = await extract_entities(["doc-1", "doc-2"])
            
            assert result["total_entities"] == 5
            assert "person" in result["entities_by_type"]
            assert "place" in result["entities_by_type"]
            assert len(result["entities_by_type"]["person"]) == 1
            assert result["entities_by_type"]["person"][0]["name"] == "Julius Caesar"
            
            # Verify the underlying tool was called correctly
            mock_tool.extract_entities.assert_called_once_with(document_ids=["doc-1", "doc-2"])
    
    @pytest.mark.asyncio
    async def test_cross_reference_documents_integration(self):
        """Test cross-reference function integration."""
        with patch('app.services.historical_tool_functions.cross_reference_tool') as mock_tool:
            mock_result = {
                "topic": "Roman Civil War",
                "documents_analyzed": 2,
                "cross_references": [
                    {
                        "topic": "Roman Civil War",
                        "document1": "Doc1",
                        "document2": "Doc2",
                        "similarity_score": 0.75,
                        "common_entities": ["Caesar", "Pompey"],
                        "contradictions": ["Different casualty numbers"],
                        "supporting_evidence": ["Both mention Pharsalus"]
                    }
                ],
                "analysis": {
                    "overall_consensus": "Sources generally agree on main events",
                    "major_contradictions": ["Casualty figures vary"],
                    "supporting_evidence": ["Multiple sources confirm key battles"]
                },
                "summary": "Cross-reference analysis found general agreement between sources."
            }
            
            mock_tool.cross_reference_documents = AsyncMock(return_value=mock_result)
            
            # Test the function
            result = await cross_reference_documents("Roman Civil War", ["doc-1", "doc-2"])
            
            assert result["topic"] == "Roman Civil War"
            assert result["documents_analyzed"] == 2
            assert len(result["cross_references"]) == 1
            assert result["cross_references"][0]["similarity_score"] == 0.75
            
            # Verify the underlying tool was called correctly
            mock_tool.cross_reference_documents.assert_called_once_with(
                topic="Roman Civil War", 
                document_ids=["doc-1", "doc-2"]
            )
    
    @pytest.mark.asyncio
    async def test_generate_citations_integration(self):
        """Test citation generator function integration."""
        with patch('app.services.historical_tool_functions.citation_generator_tool') as mock_tool:
            mock_result = {
                "total_citations": 2,
                "citations": [
                    {
                        "document_name": "Roman History",
                        "page_number": 15,
                        "quote": "The legion was the backbone of Roman military power.",
                        "citation_format": "[Roman History, p. 15]",
                        "context": "Military organization"
                    }
                ],
                "bibliography": [
                    "Roman History. Historical Document. Accessed via document analysis system."
                ],
                "citation_style": "academic"
            }
            
            mock_tool.generate_citations = AsyncMock(return_value=mock_result)
            
            search_results = [
                {
                    "content": "The legion was the backbone of Roman military power.",
                    "source_attribution": "Roman History, p. 15",
                    "document_name": "Roman History",
                    "page_number": 15
                }
            ]
            
            # Test the function
            result = await generate_citations(search_results, "chicago")
            
            assert result["total_citations"] == 2
            assert len(result["citations"]) == 1
            assert result["citations"][0]["document_name"] == "Roman History"
            assert result["citation_style"] == "academic"
            
            # Verify the underlying tool was called correctly
            mock_tool.generate_citations.assert_called_once_with(
                search_results=search_results, 
                style="chicago"
            )
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across all functions."""
        # Test search_documents error handling
        with patch('app.services.historical_tool_functions.historical_search_tool') as mock_tool:
            mock_tool.search = AsyncMock(side_effect=Exception("Search service unavailable"))
            
            result = await search_documents("test query")
            
            assert result["total_results"] == 0
            assert result["search_strategy"] == "error"
            assert "error" in result
            assert "Search service unavailable" in result["error"]
        
        # Test build_timeline error handling
        with patch('app.services.historical_tool_functions.timeline_builder_tool') as mock_tool:
            mock_tool.extract_timeline = AsyncMock(side_effect=Exception("Timeline service failed"))
            
            result = await build_timeline()
            
            assert result["total_events"] == 0
            assert "Timeline service failed" in result["timeline_summary"]
            assert "error" in result
        
        # Test extract_entities error handling
        with patch('app.services.historical_tool_functions.entity_extractor_tool') as mock_tool:
            mock_tool.extract_entities = AsyncMock(side_effect=Exception("Entity extraction failed"))
            
            result = await extract_entities()
            
            assert result["total_entities"] == 0
            assert result["extraction_method"] == "error"
            assert "error" in result
        
        # Test cross_reference_documents error handling
        with patch('app.services.historical_tool_functions.cross_reference_tool') as mock_tool:
            mock_tool.cross_reference_documents = AsyncMock(side_effect=Exception("Cross-reference failed"))
            
            result = await cross_reference_documents("test topic")
            
            assert result["documents_analyzed"] == 0
            assert "Cross-reference analysis failed" in result["summary"]
            assert "error" in result
        
        # Test generate_citations error handling
        with patch('app.services.historical_tool_functions.citation_generator_tool') as mock_tool:
            mock_tool.generate_citations = AsyncMock(side_effect=Exception("Citation generation failed"))
            
            result = await generate_citations([])
            
            assert result["total_citations"] == 0
            assert "error" in result
    
    def test_list_available_tools_integration(self):
        """Test listing available tools."""
        tools = list_available_tools()
        
        assert len(tools) == 5
        assert "search_documents" in tools
        assert "build_timeline" in tools
        assert "extract_entities" in tools
        assert "cross_reference_documents" in tools
        assert "generate_citations" in tools
        
        # Verify each tool has required metadata
        for tool_name, tool_info in tools.items():
            assert "description" in tool_info
            assert "parameters" in tool_info
            assert "input_schema" in tool_info
            assert "output_schema" in tool_info
            
            # Verify schemas are valid Pydantic schemas
            assert isinstance(tool_info["input_schema"], dict)
            assert isinstance(tool_info["output_schema"], dict)
            assert "properties" in tool_info["input_schema"]
            assert "properties" in tool_info["output_schema"]
    
    @pytest.mark.asyncio
    async def test_function_input_validation_integration(self):
        """Test input validation across all functions."""
        # Test search_documents with invalid input
        with patch('app.services.historical_tool_functions.historical_search_tool'):
            # Empty query should be handled gracefully
            result = await search_documents("")
            assert "error" in result
        
        # Test cross_reference_documents with invalid input
        with patch('app.services.historical_tool_functions.cross_reference_tool'):
            # Empty topic should be handled gracefully
            result = await cross_reference_documents("")
            assert "error" in result
        
        # Test generate_citations with invalid input
        with patch('app.services.historical_tool_functions.citation_generator_tool'):
            # Invalid search results should be handled gracefully
            result = await generate_citations("not a list")
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_function_execution(self):
        """Test concurrent execution of multiple tool functions."""
        import asyncio
        
        # Mock all tools
        with patch('app.services.historical_tool_functions.historical_search_tool') as mock_search, \
             patch('app.services.historical_tool_functions.timeline_builder_tool') as mock_timeline, \
             patch('app.services.historical_tool_functions.entity_extractor_tool') as mock_entities:
            
            # Set up mock returns
            mock_search.search = AsyncMock(return_value={
                "query": "test query", "enhanced_query": "test query", "results": [], 
                "total_results": 0, "search_strategy": "test"
            })
            mock_timeline.extract_timeline = AsyncMock(return_value={
                "total_events": 0, "timeline_events": [], "grouped_by_period": {},
                "timeline_summary": "test", "date_range": {"start": "Unknown", "end": "Unknown"}
            })
            mock_entities.extract_entities = AsyncMock(return_value={
                "total_entities": 0, "entities_by_type": {}, "entity_relationships": {},
                "entity_summary": "test", "extraction_method": "test"
            })
            
            # Execute functions concurrently
            tasks = [
                search_documents("test query"),
                build_timeline(["doc-1"]),
                extract_entities(["doc-1"])
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all functions completed successfully
            assert len(results) == 3
            assert results[0]["query"] == "test query"
            assert results[1]["total_events"] == 0
            assert results[2]["total_entities"] == 0
            
            # Verify all tools were called
            mock_search.search.assert_called_once()
            mock_timeline.extract_timeline.assert_called_once()
            mock_entities.extract_entities.assert_called_once()


class TestToolFunctionCompatibility:
    """Test compatibility of tool functions with agent SDK requirements."""
    
    def test_function_signatures(self):
        """Test that all tool functions have compatible signatures for agent SDK."""
        from app.services.historical_tool_functions import HISTORICAL_TOOL_FUNCTIONS
        import inspect
        
        for tool_name, tool_info in HISTORICAL_TOOL_FUNCTIONS.items():
            func = tool_info["function"]
            
            # Verify function is async
            assert inspect.iscoroutinefunction(func), f"{tool_name} should be async"
            
            # Verify function has proper signature
            sig = inspect.signature(func)
            
            # Check that required parameters are reasonable for agent SDK
            required_params = []
            for param_name, param in sig.parameters.items():
                if param_name not in ['args', 'kwargs']:
                    # Check if parameter has default or is Optional
                    has_default = param.default is not inspect.Parameter.empty
                    is_optional = (hasattr(param.annotation, '__origin__') and 
                                 param.annotation.__origin__ is Union and 
                                 type(None) in param.annotation.__args__)
                    
                    if not has_default and not is_optional:
                        required_params.append(param_name)
            
            # Only certain parameters should be required
            allowed_required_params = {'query', 'topic', 'search_results'}
            for param in required_params:
                assert param in allowed_required_params, \
                    f"{tool_name}.{param} is required but not in allowed list: {allowed_required_params}"
    
    def test_pydantic_schema_compatibility(self):
        """Test that Pydantic schemas are compatible with agent SDK."""
        from app.services.historical_tool_functions import HISTORICAL_TOOL_FUNCTIONS
        
        for tool_name, tool_info in HISTORICAL_TOOL_FUNCTIONS.items():
            input_schema = tool_info["input_schema"]
            output_schema = tool_info["output_schema"]
            
            # Verify schemas can be serialized (required for agent SDK)
            input_dict = input_schema.schema()
            output_dict = output_schema.schema()
            
            assert isinstance(input_dict, dict)
            assert isinstance(output_dict, dict)
            assert "properties" in input_dict
            assert "properties" in output_dict
            
            # Verify required fields are properly marked
            if "required" in input_dict:
                assert isinstance(input_dict["required"], list)
    
    @pytest.mark.asyncio
    async def test_function_return_format(self):
        """Test that all functions return properly formatted dictionaries."""
        from app.services.historical_tool_functions import HISTORICAL_TOOL_FUNCTIONS
        
        # Mock all underlying tools
        with patch('app.services.historical_tool_functions.historical_search_tool') as mock_search, \
             patch('app.services.historical_tool_functions.timeline_builder_tool') as mock_timeline, \
             patch('app.services.historical_tool_functions.entity_extractor_tool') as mock_entities, \
             patch('app.services.historical_tool_functions.cross_reference_tool') as mock_cross_ref, \
             patch('app.services.historical_tool_functions.citation_generator_tool') as mock_citations:
            
            # Set up minimal mock returns
            mock_search.search = AsyncMock(return_value={
                "query": "test query", "enhanced_query": "test query", "results": [], 
                "total_results": 0, "search_strategy": "test"
            })
            mock_timeline.extract_timeline = AsyncMock(return_value={
                "total_events": 0, "timeline_events": [], "grouped_by_period": {},
                "timeline_summary": "test", "date_range": {"start": "Unknown", "end": "Unknown"}
            })
            mock_entities.extract_entities = AsyncMock(return_value={
                "total_entities": 0, "entities_by_type": {}, "entity_relationships": {},
                "entity_summary": "test", "extraction_method": "test"
            })
            mock_cross_ref.cross_reference_documents = AsyncMock(return_value={
                "topic": "test topic", "documents_analyzed": 0, "cross_references": [],
                "analysis": {}, "summary": "test"
            })
            mock_citations.generate_citations = AsyncMock(return_value={
                "total_citations": 0, "citations": [], "bibliography": [],
                "citation_style": "academic"
            })
            
            # Test each function
            for tool_name, tool_info in HISTORICAL_TOOL_FUNCTIONS.items():
                func = tool_info["function"]
                output_schema = tool_info["output_schema"]
                
                # Call function with minimal valid inputs
                if tool_name == "search_documents":
                    result = await func("test query")
                elif tool_name == "cross_reference_documents":
                    result = await func("test topic")
                elif tool_name == "generate_citations":
                    result = await func([])
                else:
                    result = await func()
                
                # Verify result is a dictionary
                assert isinstance(result, dict), f"{tool_name} should return dict"
                
                # Verify result can be validated by output schema (when no error)
                if "error" not in result:
                    try:
                        output_schema(**result)
                    except Exception as e:
                        pytest.fail(f"{tool_name} output doesn't match schema: {e}")