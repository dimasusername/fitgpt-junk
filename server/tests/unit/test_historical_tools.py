"""
Unit tests for historical document analysis tools.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.historical_tools import (
    HistoricalDocumentSearchTool,
    TimelineBuilderTool,
    EntityExtractorTool,
    CrossReferenceTool,
    CitationGeneratorTool,
    HistoricalAnalysisToolkit,
    TimelineEvent,
    HistoricalEntity,
    CrossReference,
    Citation
)


class TestHistoricalDocumentSearchTool:
    """Test cases for the historical document search tool."""
    
    @pytest.fixture
    def search_tool(self):
        """Create a search tool instance for testing."""
        return HistoricalDocumentSearchTool()
    
    @pytest.mark.asyncio
    async def test_search_basic_functionality(self, search_tool):
        """Test basic search functionality."""
        # Mock the vector search service
        with patch('app.services.historical_tools.vector_search_service') as mock_search:
            mock_result = Mock()
            mock_result.chunk_id = "test-chunk-1"
            mock_result.content = "The Roman legion was a military unit consisting of approximately 5,000 soldiers."
            mock_result.similarity_score = 0.85
            mock_result.relevance_score = 0.90
            mock_result.page_number = 15
            mock_result.source_attribution = "Roman Military History, p. 15"
            mock_result.document_original_name = "Roman Military History"
            
            mock_search.search.return_value = [mock_result]
            
            # Mock the AI enhancement
            with patch('google.generativeai.generate_text') as mock_ai:
                mock_ai.return_value.result = "Roman legion military unit soldiers formation"
                
                result = await search_tool.search("Roman legion")
                
                assert result["query"] == "Roman legion"
                assert result["total_results"] == 1
                assert result["search_strategy"] == "historical_terminology_optimized"
                assert len(result["results"]) == 1
                
                # Check result structure
                search_result = result["results"][0]
                assert search_result["chunk_id"] == "test-chunk-1"
                assert "Roman legion" in search_result["content"]
                assert search_result["similarity_score"] == 0.85
    
    def test_calculate_historical_relevance(self, search_tool):
        """Test historical relevance scoring."""
        content = "The Roman legion consisted of hastati, principes, and triarii in 146 BC."
        query = "Roman military structure"
        
        score = search_tool._calculate_historical_relevance(content, query)
        
        # Should have high score due to historical terms and date
        assert score > 0.5
        assert isinstance(score, float)
        assert 0 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_extract_quick_entities(self, search_tool):
        """Test quick entity extraction."""
        text = "Marcus Aurelius led the Roman forces at the Battle of Cannae in 216 BC."
        
        entities = await search_tool._extract_quick_entities(text)
        
        assert "Marcus Aurelius" in entities
        assert "Battle of Cannae" in entities
        assert len(entities) >= 2


class TestTimelineBuilderTool:
    """Test cases for the timeline builder tool."""
    
    @pytest.fixture
    def timeline_tool(self):
        """Create a timeline tool instance for testing."""
        return TimelineBuilderTool()
    
    def test_calculate_date_confidence(self, timeline_tool):
        """Test date confidence calculation."""
        # Test exact date
        confidence = timeline_tool._calculate_date_confidence("146 BC", "exact")
        assert confidence >= 0.9
        
        # Test approximate date
        confidence = timeline_tool._calculate_date_confidence("around 150 BC", "approximate")
        assert 0.5 <= confidence < 0.9
        
        # Test century reference
        confidence = timeline_tool._calculate_date_confidence("2nd century BC", "century")
        assert 0.6 <= confidence < 0.9
    
    def test_sort_events_chronologically(self, timeline_tool):
        """Test chronological sorting of events."""
        events = [
            TimelineEvent("146 BC", "Destruction of Carthage", "Doc1", 1, 0.9, "exact"),
            TimelineEvent("264 BC", "First Punic War begins", "Doc1", 2, 0.9, "exact"),
            TimelineEvent("218 BC", "Hannibal crosses Alps", "Doc1", 3, 0.9, "exact")
        ]
        
        sorted_events = timeline_tool._sort_events_chronologically(events)
        
        # Should be sorted from earliest to latest (most negative BC to least negative)
        assert "264 BC" in sorted_events[0].date  # Earliest
        assert "146 BC" in sorted_events[-1].date  # Latest
    
    def test_determine_historical_period(self, timeline_tool):
        """Test historical period determination."""
        # Test Roman Republic period
        period = timeline_tool._determine_historical_period("146 BC")
        assert "Roman Republic" in period
        
        # Test Roman Empire period
        period = timeline_tool._determine_historical_period("50 AD")
        assert "Roman Empire" in period
        
        # Test Hellenistic period
        period = timeline_tool._determine_historical_period("250 BC")
        assert "Hellenistic" in period
    
    def test_event_to_dict(self, timeline_tool):
        """Test event serialization."""
        event = TimelineEvent(
            date="146 BC",
            event="Destruction of Carthage",
            source_document="Roman History",
            page_number=25,
            confidence=0.9,
            date_type="exact"
        )
        
        event_dict = timeline_tool._event_to_dict(event)
        
        assert event_dict["date"] == "146 BC"
        assert event_dict["event"] == "Destruction of Carthage"
        assert event_dict["source_document"] == "Roman History"
        assert event_dict["page_number"] == 25
        assert event_dict["confidence"] == 0.9
        assert event_dict["date_type"] == "exact"


class TestEntityExtractorTool:
    """Test cases for the entity extractor tool."""
    
    @pytest.fixture
    def entity_tool(self):
        """Create an entity extractor instance for testing."""
        return EntityExtractorTool()
    
    def test_entities_similar(self, entity_tool):
        """Test entity similarity detection."""
        entity1 = HistoricalEntity("Marcus Aurelius", "person", "context", "doc", 1, 1, [])
        entity2 = HistoricalEntity("Marcus Aurelius", "person", "different context", "doc", 1, 1, [])
        entity3 = HistoricalEntity("Julius Caesar", "person", "context", "doc", 1, 1, [])
        
        # Same entities should be similar
        assert entity_tool._entities_similar(entity1, entity2)
        
        # Different entities should not be similar
        assert not entity_tool._entities_similar(entity1, entity3)
        
        # Test partial matches
        entity4 = HistoricalEntity("Aurelius", "person", "context", "doc", 1, 1, [])
        assert entity_tool._entities_similar(entity1, entity4)
    
    def test_entity_to_dict(self, entity_tool):
        """Test entity serialization."""
        entity = HistoricalEntity(
            name="Julius Caesar",
            entity_type="person",
            context="Roman general and statesman",
            source_document="Roman History",
            page_number=10,
            mentions=5,
            related_entities=["Pompey", "Crassus"]
        )
        
        entity_dict = entity_tool._entity_to_dict(entity)
        
        assert entity_dict["name"] == "Julius Caesar"
        assert entity_dict["entity_type"] == "person"
        assert entity_dict["context"] == "Roman general and statesman"
        assert entity_dict["source_document"] == "Roman History"
        assert entity_dict["page_number"] == 10
        assert entity_dict["mentions"] == 5
        assert entity_dict["related_entities"] == ["Pompey", "Crassus"]


class TestCrossReferenceTool:
    """Test cases for the cross-reference tool."""
    
    @pytest.fixture
    def cross_ref_tool(self):
        """Create a cross-reference tool instance for testing."""
        return CrossReferenceTool()
    
    def test_group_results_by_document(self, cross_ref_tool):
        """Test grouping search results by document."""
        results = [
            {"document_name": "Doc1", "content": "Content 1"},
            {"document_name": "Doc2", "content": "Content 2"},
            {"document_name": "Doc1", "content": "Content 3"}
        ]
        
        grouped = cross_ref_tool._group_results_by_document(results)
        
        assert len(grouped) == 2
        assert len(grouped["Doc1"]) == 2
        assert len(grouped["Doc2"]) == 1
    
    def test_find_common_entities(self, cross_ref_tool):
        """Test finding common entities between documents."""
        doc1_results = [
            {"historical_entities": ["Caesar", "Pompey", "Rome"]},
            {"historical_entities": ["Crassus", "Senate"]}
        ]
        
        doc2_results = [
            {"historical_entities": ["Caesar", "Cleopatra", "Egypt"]},
            {"historical_entities": ["Rome", "Alexandria"]}
        ]
        
        common = cross_ref_tool._find_common_entities(doc1_results, doc2_results)
        
        assert "Caesar" in common
        assert "Rome" in common
        assert "Pompey" not in common
        assert "Cleopatra" not in common
    
    def test_cross_ref_to_dict(self, cross_ref_tool):
        """Test cross-reference serialization."""
        cross_ref = CrossReference(
            topic="Roman Civil War",
            document1="Doc1",
            document2="Doc2",
            similarity_score=0.75,
            common_entities=["Caesar", "Pompey"],
            contradictions=["Different casualty numbers"],
            supporting_evidence=["Both mention Pharsalus"]
        )
        
        cross_ref_dict = cross_ref_tool._cross_ref_to_dict(cross_ref)
        
        assert cross_ref_dict["topic"] == "Roman Civil War"
        assert cross_ref_dict["document1"] == "Doc1"
        assert cross_ref_dict["document2"] == "Doc2"
        assert cross_ref_dict["similarity_score"] == 0.75
        assert cross_ref_dict["common_entities"] == ["Caesar", "Pompey"]
        assert cross_ref_dict["contradictions"] == ["Different casualty numbers"]
        assert cross_ref_dict["supporting_evidence"] == ["Both mention Pharsalus"]


class TestCitationGeneratorTool:
    """Test cases for the citation generator tool."""
    
    @pytest.fixture
    def citation_tool(self):
        """Create a citation generator instance for testing."""
        return CitationGeneratorTool()
    
    def test_format_chicago_citation(self, citation_tool):
        """Test Chicago style citation formatting."""
        citation = Citation(
            document_name="Roman Military History",
            page_number=25,
            quote="The legion was the backbone of Roman military power.",
            citation_format="chicago",
            context="Military organization"
        )
        
        formatted = citation_tool._format_chicago_citation(citation)
        
        assert "Roman Military History" in formatted
        assert "25" in formatted
        assert formatted.endswith(".")
    
    def test_format_mla_citation(self, citation_tool):
        """Test MLA style citation formatting."""
        citation = Citation(
            document_name="Roman Military History",
            page_number=25,
            quote="The legion was the backbone of Roman military power.",
            citation_format="mla",
            context="Military organization"
        )
        
        formatted = citation_tool._format_mla_citation(citation)
        
        assert formatted.startswith("(")
        assert formatted.endswith(")")
        assert "Roman Military History" in formatted
        assert "25" in formatted
    
    def test_format_academic_citation(self, citation_tool):
        """Test academic style citation formatting."""
        citation = Citation(
            document_name="Roman Military History",
            page_number=25,
            quote="The legion was the backbone of Roman military power.",
            citation_format="academic",
            context="Military organization"
        )
        
        formatted = citation_tool._format_academic_citation(citation)
        
        assert formatted.startswith("[")
        assert formatted.endswith("]")
        assert "Roman Military History" in formatted
        assert "p. 25" in formatted
    
    def test_create_bibliography_entry(self, citation_tool):
        """Test bibliography entry creation."""
        citation = Citation(
            document_name="Roman Military History",
            page_number=25,
            quote="Test quote",
            citation_format="chicago",
            context="Test context"
        )
        
        bib_entry = citation_tool._create_bibliography_entry(citation, "chicago")
        
        assert "Roman Military History" in bib_entry
        assert "Historical Document" in bib_entry


class TestHistoricalAnalysisToolkit:
    """Test cases for the main historical analysis toolkit."""
    
    @pytest.fixture
    def toolkit(self):
        """Create a toolkit instance for testing."""
        return HistoricalAnalysisToolkit()
    
    def test_get_available_tools(self, toolkit):
        """Test getting available tools information."""
        tools = toolkit.get_available_tools()
        
        assert "document_search" in tools
        assert "timeline_builder" in tools
        assert "entity_extractor" in tools
        assert "cross_reference" in tools
        assert "citation_generator" in tools
        
        # Check tool structure
        search_tool = tools["document_search"]
        assert "name" in search_tool
        assert "description" in search_tool
        assert "parameters" in search_tool
        assert "use_cases" in search_tool
    
    @pytest.mark.asyncio
    async def test_execute_tool_invalid_tool(self, toolkit):
        """Test executing an invalid tool name."""
        with pytest.raises(Exception):  # Should raise HTTPException
            await toolkit.execute_tool("invalid_tool")
    
    @pytest.mark.asyncio
    async def test_execute_tool_valid_tool(self, toolkit):
        """Test executing a valid tool."""
        # Mock the document search
        with patch.object(toolkit, 'search_documents') as mock_search:
            mock_search.return_value = {"results": [], "total_results": 0}
            
            result = await toolkit.execute_tool("document_search", query="test")
            
            assert result["tool_name"] == "document_search"
            assert result["execution_status"] == "success"
            assert "result" in result
            assert "timestamp" in result
            
            mock_search.assert_called_once_with(query="test")


# Integration test fixtures
@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = Mock()
    mock_table = Mock()
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.in_.return_value = mock_table
    mock_table.execute.return_value.data = []
    return mock_client


@pytest.fixture
def mock_document_chunks():
    """Mock document chunks for testing."""
    return [
        {
            "id": "chunk-1",
            "content": "The Roman legion was organized into cohorts and centuries in 146 BC.",
            "page_number": 15,
            "chunk_index": 0,
            "documents": {
                "id": "doc-1",
                "filename": "roman_history.pdf",
                "original_name": "Roman Military History"
            }
        },
        {
            "id": "chunk-2", 
            "content": "Julius Caesar led his forces across the Rubicon River in 49 BC.",
            "page_number": 23,
            "chunk_index": 1,
            "documents": {
                "id": "doc-1",
                "filename": "roman_history.pdf",
                "original_name": "Roman Military History"
            }
        }
    ]


class TestHistoricalToolsIntegration:
    """Integration tests for historical tools."""
    
    @pytest.mark.asyncio
    async def test_timeline_extraction_integration(self, mock_document_chunks):
        """Test timeline extraction with mock data."""
        timeline_tool = TimelineBuilderTool()
        
        with patch.object(timeline_tool, '_get_document_chunks') as mock_get_chunks:
            mock_get_chunks.return_value = mock_document_chunks
            
            with patch('google.generativeai.generate_text') as mock_ai:
                mock_ai.return_value.result = "146 BC | Destruction of Carthage | high\n49 BC | Caesar crosses Rubicon | high"
                
                result = await timeline_tool.extract_timeline()
                
                assert result["total_events"] >= 2
                assert "timeline_events" in result
                assert "grouped_by_period" in result
                assert "timeline_summary" in result
    
    @pytest.mark.asyncio
    async def test_entity_extraction_integration(self, mock_document_chunks):
        """Test entity extraction with mock data."""
        entity_tool = EntityExtractorTool()
        
        with patch.object(entity_tool, '_get_document_chunks') as mock_get_chunks:
            mock_get_chunks.return_value = mock_document_chunks
            
            with patch('google.generativeai.generate_text') as mock_ai:
                mock_ai.return_value.result = "PERSON | Julius Caesar | Roman general\nPLACE | Rubicon River | River in Italy"
                
                result = await entity_tool.extract_entities()
                
                assert result["total_entities"] >= 1
                assert "entities_by_type" in result
                assert "entity_summary" in result