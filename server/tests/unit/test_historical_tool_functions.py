"""
Unit tests for historical document analysis tool functions.

These tests verify the function-based tools that are designed for agent SDK integration.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from app.services.historical_tool_functions import (
    search_documents,
    build_timeline,
    extract_entities,
    cross_reference_documents,
    generate_citations,
    get_tool_function,
    get_tool_schema,
    list_available_tools,
    DocumentSearchInput,
    DocumentSearchOutput,
    TimelineBuilderInput,
    TimelineBuilderOutput,
    EntityExtractorInput,
    EntityExtractorOutput,
    CrossReferenceInput,
    CrossReferenceOutput,
    CitationGeneratorInput,
    CitationGeneratorOutput,
    HISTORICAL_TOOL_FUNCTIONS
)


class TestDocumentSearchFunction:
    """Test cases for the document search function."""
    
    @pytest.mark.asyncio
    async def test_search_documents_success(self):
        """Test successful document search."""
        # Mock the historical search tool
        with patch('app.services.historical_tool_functions.historical_search_tool') as mock_tool:
            mock_result = {
                "query": "Roman legion",
                "enhanced_query": "Roman legion military unit soldiers formation",
                "results": [
                    {
                        "chunk_id": "test-chunk-1",
                        "content": "The Roman legion was a military unit.",
                        "similarity_score": 0.85,
                        "relevance_score": 0.90,
                        "source_attribution": "Roman History, p. 15"
                    }
                ],
                "total_results": 1,
                "search_strategy": "historical_terminology_optimized"
            }
            
            mock_tool.search = AsyncMock(return_value=mock_result)
            
            result = await search_documents("Roman legion")
            
            assert result["query"] == "Roman legion"
            assert result["total_results"] == 1
            assert result["search_strategy"] == "historical_terminology_optimized"
            assert len(result["results"]) == 1
            
            # Verify the tool was called correctly
            mock_tool.search.assert_called_once_with(query="Roman legion", document_ids=None)
    
    @pytest.mark.asyncio
    async def test_search_documents_with_document_ids(self):
        """Test document search with specific document IDs."""
        with patch('app.services.historical_tool_functions.historical_search_tool') as mock_tool:
            mock_result = {
                "query": "Roman legion",
                "enhanced_query": "Roman legion",
                "results": [],
                "total_results": 0,
                "search_strategy": "historical_terminology_optimized"
            }
            
            mock_tool.search = AsyncMock(return_value=mock_result)
            
            document_ids = ["doc-1", "doc-2"]
            result = await search_documents("Roman legion", document_ids)
            
            assert result["query"] == "Roman legion"
            assert result["total_results"] == 0
            
            # Verify the tool was called with document IDs
            mock_tool.search.assert_called_once_with(query="Roman legion", document_ids=document_ids)
    
    @pytest.mark.asyncio
    async def test_search_documents_error_handling(self):
        """Test error handling in document search."""
        with patch('app.services.historical_tool_functions.historical_search_tool') as mock_tool:
            mock_tool.search = AsyncMock(side_effect=Exception("Search failed"))
            
            result = await search_documents("Roman legion")
            
            assert result["query"] == "Roman legion"
            assert result["total_results"] == 0
            assert result["search_strategy"] == "error"
            assert "error" in result
            assert "Search failed" in result["error"]
    
    def test_document_search_input_validation(self):
        """Test input validation for document search."""
        # Valid input
        valid_input = DocumentSearchInput(query="Roman legion", document_ids=["doc-1"])
        assert valid_input.query == "Roman legion"
        assert valid_input.document_ids == ["doc-1"]
        
        # Invalid input - empty query
        with pytest.raises(ValueError):
            DocumentSearchInput(query="", document_ids=None)
        
        # Invalid input - query too long
        with pytest.raises(ValueError):
            DocumentSearchInput(query="x" * 1001, document_ids=None)


class TestTimelineBuilderFunction:
    """Test cases for the timeline builder function."""
    
    @pytest.mark.asyncio
    async def test_build_timeline_success(self):
        """Test successful timeline building."""
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
                "timeline_summary": "Timeline covers major Roman conflicts.",
                "date_range": {"start": "264 BC", "end": "146 BC"}
            }
            
            mock_tool.extract_timeline = AsyncMock(return_value=mock_result)
            
            result = await build_timeline()
            
            assert result["total_events"] == 3
            assert len(result["timeline_events"]) == 1
            assert "Roman Republic" in result["grouped_by_period"]
            assert result["date_range"]["start"] == "264 BC"
            
            # Verify the tool was called correctly
            mock_tool.extract_timeline.assert_called_once_with(document_ids=None)
    
    @pytest.mark.asyncio
    async def test_build_timeline_with_document_ids(self):
        """Test timeline building with specific document IDs."""
        with patch('app.services.historical_tool_functions.timeline_builder_tool') as mock_tool:
            mock_result = {
                "total_events": 0,
                "timeline_events": [],
                "grouped_by_period": {},
                "timeline_summary": "No events found.",
                "date_range": {"start": "Unknown", "end": "Unknown"}
            }
            
            mock_tool.extract_timeline = AsyncMock(return_value=mock_result)
            
            document_ids = ["doc-1"]
            result = await build_timeline(document_ids)
            
            assert result["total_events"] == 0
            
            # Verify the tool was called with document IDs
            mock_tool.extract_timeline.assert_called_once_with(document_ids=document_ids)
    
    @pytest.mark.asyncio
    async def test_build_timeline_error_handling(self):
        """Test error handling in timeline building."""
        with patch('app.services.historical_tool_functions.timeline_builder_tool') as mock_tool:
            mock_tool.extract_timeline = AsyncMock(side_effect=Exception("Timeline extraction failed"))
            
            result = await build_timeline()
            
            assert result["total_events"] == 0
            assert result["timeline_events"] == []
            assert "Timeline extraction failed" in result["timeline_summary"]
            assert "error" in result


class TestEntityExtractorFunction:
    """Test cases for the entity extractor function."""
    
    @pytest.mark.asyncio
    async def test_extract_entities_success(self):
        """Test successful entity extraction."""
        with patch('app.services.historical_tool_functions.entity_extractor_tool') as mock_tool:
            mock_result = {
                "total_entities": 5,
                "entities_by_type": {
                    "person": [
                        {
                            "name": "Julius Caesar",
                            "entity_type": "person",
                            "context": "Roman general",
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
                            "related_entities": ["Italy", "Mediterranean"]
                        }
                    ]
                },
                "entity_relationships": {
                    "Julius Caesar": ["Pompey", "Crassus"],
                    "Rome": ["Italy"]
                },
                "entity_summary": "Extracted 5 historical entities including 1 person and 1 place.",
                "extraction_method": "hybrid_pattern_ai"
            }
            
            mock_tool.extract_entities = AsyncMock(return_value=mock_result)
            
            result = await extract_entities()
            
            assert result["total_entities"] == 5
            assert "person" in result["entities_by_type"]
            assert "place" in result["entities_by_type"]
            assert len(result["entities_by_type"]["person"]) == 1
            assert result["entities_by_type"]["person"][0]["name"] == "Julius Caesar"
            assert "Julius Caesar" in result["entity_relationships"]
            
            # Verify the tool was called correctly
            mock_tool.extract_entities.assert_called_once_with(document_ids=None)
    
    @pytest.mark.asyncio
    async def test_extract_entities_error_handling(self):
        """Test error handling in entity extraction."""
        with patch('app.services.historical_tool_functions.entity_extractor_tool') as mock_tool:
            mock_tool.extract_entities = AsyncMock(side_effect=Exception("Entity extraction failed"))
            
            result = await extract_entities()
            
            assert result["total_entities"] == 0
            assert result["entities_by_type"] == {}
            assert result["extraction_method"] == "error"
            assert "error" in result


class TestCrossReferenceFunction:
    """Test cases for the cross-reference function."""
    
    @pytest.mark.asyncio
    async def test_cross_reference_documents_success(self):
        """Test successful cross-reference analysis."""
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
            
            result = await cross_reference_documents("Roman Civil War")
            
            assert result["topic"] == "Roman Civil War"
            assert result["documents_analyzed"] == 2
            assert len(result["cross_references"]) == 1
            assert result["cross_references"][0]["similarity_score"] == 0.75
            assert "Caesar" in result["cross_references"][0]["common_entities"]
            
            # Verify the tool was called correctly
            mock_tool.cross_reference_documents.assert_called_once_with(
                topic="Roman Civil War", document_ids=None
            )
    
    @pytest.mark.asyncio
    async def test_cross_reference_documents_error_handling(self):
        """Test error handling in cross-reference analysis."""
        with patch('app.services.historical_tool_functions.cross_reference_tool') as mock_tool:
            mock_tool.cross_reference_documents = AsyncMock(side_effect=Exception("Cross-reference failed"))
            
            result = await cross_reference_documents("Roman Civil War")
            
            assert result["topic"] == "Roman Civil War"
            assert result["documents_analyzed"] == 0
            assert result["cross_references"] == []
            assert "Cross-reference analysis failed" in result["summary"]
            assert "error" in result
    
    def test_cross_reference_input_validation(self):
        """Test input validation for cross-reference."""
        # Valid input
        valid_input = CrossReferenceInput(topic="Roman Civil War", document_ids=["doc-1"])
        assert valid_input.topic == "Roman Civil War"
        
        # Invalid input - empty topic
        with pytest.raises(ValueError):
            CrossReferenceInput(topic="", document_ids=None)
        
        # Invalid input - topic too long
        with pytest.raises(ValueError):
            CrossReferenceInput(topic="x" * 501, document_ids=None)


class TestCitationGeneratorFunction:
    """Test cases for the citation generator function."""
    
    @pytest.mark.asyncio
    async def test_generate_citations_success(self):
        """Test successful citation generation."""
        with patch('app.services.historical_tool_functions.citation_generator_tool') as mock_tool:
            mock_result = {
                "total_citations": 2,
                "citations": [
                    {
                        "document_name": "Roman History",
                        "page_number": 15,
                        "quote": "The legion was the backbone of Roman power.",
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
                    "content": "The legion was the backbone of Roman power.",
                    "source_attribution": "Roman History, p. 15",
                    "document_name": "Roman History",
                    "page_number": 15
                }
            ]
            
            result = await generate_citations(search_results, "academic")
            
            assert result["total_citations"] == 2
            assert len(result["citations"]) == 1
            assert result["citations"][0]["document_name"] == "Roman History"
            assert result["citation_style"] == "academic"
            assert len(result["bibliography"]) == 1
            
            # Verify the tool was called correctly
            mock_tool.generate_citations.assert_called_once_with(
                search_results=search_results, style="academic"
            )
    
    @pytest.mark.asyncio
    async def test_generate_citations_error_handling(self):
        """Test error handling in citation generation."""
        with patch('app.services.historical_tool_functions.citation_generator_tool') as mock_tool:
            mock_tool.generate_citations = AsyncMock(side_effect=Exception("Citation generation failed"))
            
            result = await generate_citations([], "academic")
            
            assert result["total_citations"] == 0
            assert result["citations"] == []
            assert result["bibliography"] == []
            assert result["citation_style"] == "academic"
            assert "error" in result


class TestToolRegistryFunctions:
    """Test cases for tool registry and utility functions."""
    
    def test_get_tool_function(self):
        """Test getting tool functions by name."""
        # Valid tool name
        search_func = get_tool_function("search_documents")
        assert search_func == search_documents
        
        timeline_func = get_tool_function("build_timeline")
        assert timeline_func == build_timeline
        
        # Invalid tool name
        invalid_func = get_tool_function("invalid_tool")
        assert invalid_func is None
    
    def test_get_tool_schema(self):
        """Test getting tool schemas."""
        # Valid tool name
        search_schema = get_tool_schema("search_documents")
        assert search_schema is not None
        assert search_schema["input_schema"] == DocumentSearchInput
        assert search_schema["output_schema"] == DocumentSearchOutput
        assert "description" in search_schema
        assert "parameters" in search_schema
        
        # Invalid tool name
        invalid_schema = get_tool_schema("invalid_tool")
        assert invalid_schema is None
    
    def test_list_available_tools(self):
        """Test listing all available tools."""
        tools = list_available_tools()
        
        assert len(tools) == 5
        assert "search_documents" in tools
        assert "build_timeline" in tools
        assert "extract_entities" in tools
        assert "cross_reference_documents" in tools
        assert "generate_citations" in tools
        
        # Check tool structure
        search_tool = tools["search_documents"]
        assert "description" in search_tool
        assert "parameters" in search_tool
        assert "input_schema" in search_tool
        assert "output_schema" in search_tool
    
    def test_historical_tool_functions_registry(self):
        """Test the tool functions registry structure."""
        assert len(HISTORICAL_TOOL_FUNCTIONS) == 5
        
        for tool_name, tool_info in HISTORICAL_TOOL_FUNCTIONS.items():
            assert "function" in tool_info
            assert "input_schema" in tool_info
            assert "output_schema" in tool_info
            assert "description" in tool_info
            assert "parameters" in tool_info
            
            # Verify function is callable
            assert callable(tool_info["function"])
            
            # Verify schemas are Pydantic models
            assert hasattr(tool_info["input_schema"], "schema")
            assert hasattr(tool_info["output_schema"], "schema")


class TestPydanticSchemas:
    """Test cases for Pydantic input/output schemas."""
    
    def test_document_search_schemas(self):
        """Test document search input/output schemas."""
        # Test input schema
        input_data = DocumentSearchInput(query="Roman legion", document_ids=["doc-1"])
        assert input_data.query == "Roman legion"
        assert input_data.document_ids == ["doc-1"]
        
        # Test output schema
        output_data = DocumentSearchOutput(
            query="Roman legion",
            enhanced_query="Roman legion military",
            results=[],
            total_results=0,
            search_strategy="test"
        )
        assert output_data.query == "Roman legion"
        assert output_data.total_results == 0
    
    def test_timeline_builder_schemas(self):
        """Test timeline builder input/output schemas."""
        # Test input schema
        input_data = TimelineBuilderInput(document_ids=["doc-1"])
        assert input_data.document_ids == ["doc-1"]
        
        # Test output schema
        output_data = TimelineBuilderOutput(
            total_events=1,
            timeline_events=[],
            grouped_by_period={},
            timeline_summary="Test summary",
            date_range={"start": "100 BC", "end": "50 BC"}
        )
        assert output_data.total_events == 1
        assert output_data.timeline_summary == "Test summary"
    
    def test_entity_extractor_schemas(self):
        """Test entity extractor input/output schemas."""
        # Test input schema
        input_data = EntityExtractorInput(document_ids=None)
        assert input_data.document_ids is None
        
        # Test output schema
        output_data = EntityExtractorOutput(
            total_entities=2,
            entities_by_type={"person": []},
            entity_relationships={},
            entity_summary="Test summary",
            extraction_method="test"
        )
        assert output_data.total_entities == 2
        assert output_data.extraction_method == "test"
    
    def test_cross_reference_schemas(self):
        """Test cross-reference input/output schemas."""
        # Test input schema
        input_data = CrossReferenceInput(topic="Roman Civil War", document_ids=["doc-1"])
        assert input_data.topic == "Roman Civil War"
        
        # Test output schema
        output_data = CrossReferenceOutput(
            topic="Roman Civil War",
            documents_analyzed=2,
            cross_references=[],
            analysis={},
            summary="Test summary"
        )
        assert output_data.topic == "Roman Civil War"
        assert output_data.documents_analyzed == 2
    
    def test_citation_generator_schemas(self):
        """Test citation generator input/output schemas."""
        # Test input schema
        input_data = CitationGeneratorInput(search_results=[], style="academic")
        assert input_data.search_results == []
        assert input_data.style == "academic"
        
        # Test output schema
        output_data = CitationGeneratorOutput(
            total_citations=1,
            citations=[],
            bibliography=[],
            citation_style="academic"
        )
        assert output_data.total_citations == 1
        assert output_data.citation_style == "academic"