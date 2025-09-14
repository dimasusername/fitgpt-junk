"""
Historical document analysis tool functions for agent SDK integration.

This module provides tool functions optimized for historical document analysis as
callable Python functions with proper Pydantic schemas for agent SDK integration.
All tools are designed to be called directly by agents without REST API overhead.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.services.historical_tools import (
    historical_search_tool,
    timeline_builder_tool,
    entity_extractor_tool,
    cross_reference_tool,
    citation_generator_tool
)

logger = logging.getLogger(__name__)


# Pydantic schemas for tool inputs and outputs
class DocumentSearchInput(BaseModel):
    """Input schema for document search tool."""
    query: str = Field(..., description="Search query with historical context", min_length=1, max_length=1000)
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to search within")


class DocumentSearchOutput(BaseModel):
    """Output schema for document search tool."""
    query: str
    enhanced_query: str
    results: List[Dict[str, Any]]
    total_results: int
    search_strategy: str


class TimelineBuilderInput(BaseModel):
    """Input schema for timeline builder tool."""
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to analyze")


class TimelineBuilderOutput(BaseModel):
    """Output schema for timeline builder tool."""
    total_events: int
    timeline_events: List[Dict[str, Any]]
    grouped_by_period: Dict[str, List[Dict[str, Any]]]
    timeline_summary: str
    date_range: Dict[str, str]


class EntityExtractorInput(BaseModel):
    """Input schema for entity extractor tool."""
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to analyze")


class EntityExtractorOutput(BaseModel):
    """Output schema for entity extractor tool."""
    total_entities: int
    entities_by_type: Dict[str, List[Dict[str, Any]]]
    entity_relationships: Dict[str, List[str]]
    entity_summary: str
    extraction_method: str


class CrossReferenceInput(BaseModel):
    """Input schema for cross-reference tool."""
    topic: str = Field(..., description="Topic to cross-reference across documents", min_length=1, max_length=500)
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to compare")


class CrossReferenceOutput(BaseModel):
    """Output schema for cross-reference tool."""
    topic: str
    documents_analyzed: int
    cross_references: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    summary: str


class CitationGeneratorInput(BaseModel):
    """Input schema for citation generator tool."""
    search_results: List[Dict[str, Any]] = Field(..., description="Search results to cite")
    style: str = Field("academic", description="Citation style (chicago, mla, apa, academic)")


class CitationGeneratorOutput(BaseModel):
    """Output schema for citation generator tool."""
    total_citations: int
    citations: List[Dict[str, Any]]
    bibliography: List[str]
    citation_style: str


# Tool function implementations
async def search_documents(query: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Search through uploaded historical documents for relevant information.
    
    This function provides enhanced search capabilities specifically designed for
    historical documents, including terminology expansion and historical context.
    
    Args:
        query: The search query with historical context
        document_ids: Optional list of document IDs to search within
        
    Returns:
        Dictionary with search results and historical context
    """
    try:
        # Validate input
        input_data = DocumentSearchInput(query=query, document_ids=document_ids)
        
        # Execute search using existing tool
        result = await historical_search_tool.search(
            query=input_data.query,
            document_ids=input_data.document_ids
        )
        
        # Validate output
        output_data = DocumentSearchOutput(**result)
        
        return output_data.dict()
        
    except Exception as e:
        logger.error(f"Document search function failed: {str(e)}")
        return {
            "query": query,
            "enhanced_query": query,
            "results": [],
            "total_results": 0,
            "search_strategy": "error",
            "error": str(e)
        }


async def build_timeline(document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Extract and organize dates, events, and chronological information from historical documents.
    
    This function analyzes documents to identify dates, events, and temporal relationships,
    then organizes them into a coherent timeline with historical context.
    
    Args:
        document_ids: Optional list of document IDs to analyze
        
    Returns:
        Dictionary with timeline events and chronological analysis
    """
    try:
        # Validate input
        input_data = TimelineBuilderInput(document_ids=document_ids)
        
        # Execute timeline building using existing tool
        result = await timeline_builder_tool.extract_timeline(
            document_ids=input_data.document_ids
        )
        
        # Validate output
        output_data = TimelineBuilderOutput(**result)
        
        return output_data.dict()
        
    except Exception as e:
        logger.error(f"Timeline builder function failed: {str(e)}")
        return {
            "total_events": 0,
            "timeline_events": [],
            "grouped_by_period": {},
            "timeline_summary": f"Timeline extraction failed: {str(e)}",
            "date_range": {"start": "Unknown", "end": "Unknown"},
            "error": str(e)
        }


async def extract_entities(document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Identify people, places, battles, and historical entities from documents.
    
    This function extracts and categorizes historical entities mentioned in documents,
    including people, places, battles, organizations, and their relationships.
    
    Args:
        document_ids: Optional list of document IDs to analyze
        
    Returns:
        Dictionary with extracted entities organized by type
    """
    try:
        # Validate input
        input_data = EntityExtractorInput(document_ids=document_ids)
        
        # Execute entity extraction using existing tool
        result = await entity_extractor_tool.extract_entities(
            document_ids=input_data.document_ids
        )
        
        # Validate output
        output_data = EntityExtractorOutput(**result)
        
        return output_data.dict()
        
    except Exception as e:
        logger.error(f"Entity extractor function failed: {str(e)}")
        return {
            "total_entities": 0,
            "entities_by_type": {},
            "entity_relationships": {},
            "entity_summary": f"Entity extraction failed: {str(e)}",
            "extraction_method": "error",
            "error": str(e)
        }


async def cross_reference_documents(topic: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Compare information across multiple historical documents to find agreements and contradictions.
    
    This function analyzes how different documents discuss the same topic, identifying
    agreements, contradictions, and supporting evidence across sources.
    
    Args:
        topic: Topic to cross-reference across documents
        document_ids: Optional list of document IDs to compare
        
    Returns:
        Dictionary with cross-reference analysis
    """
    try:
        # Validate input
        input_data = CrossReferenceInput(topic=topic, document_ids=document_ids)
        
        # Execute cross-reference analysis using existing tool
        result = await cross_reference_tool.cross_reference_documents(
            topic=input_data.topic,
            document_ids=input_data.document_ids
        )
        
        # Validate output
        output_data = CrossReferenceOutput(**result)
        
        return output_data.dict()
        
    except Exception as e:
        logger.error(f"Cross-reference function failed: {str(e)}")
        return {
            "topic": topic,
            "documents_analyzed": 0,
            "cross_references": [],
            "analysis": {},
            "summary": f"Cross-reference analysis failed: {str(e)}",
            "error": str(e)
        }


async def generate_citations(search_results: List[Dict[str, Any]], style: str = "academic") -> Dict[str, Any]:
    """
    Create proper academic citations for referenced sources.
    
    This function formats search results into proper academic citations following
    various citation styles (Chicago, MLA, APA, Academic) for scholarly work.
    
    Args:
        search_results: List of search results to cite
        style: Citation style ('chicago', 'mla', 'apa', 'academic')
        
    Returns:
        Dictionary with formatted citations and bibliography
    """
    try:
        # Validate input
        input_data = CitationGeneratorInput(search_results=search_results, style=style)
        
        # Execute citation generation using existing tool
        result = await citation_generator_tool.generate_citations(
            search_results=input_data.search_results,
            style=input_data.style
        )
        
        # Validate output
        output_data = CitationGeneratorOutput(**result)
        
        return output_data.dict()
        
    except Exception as e:
        logger.error(f"Citation generator function failed: {str(e)}")
        return {
            "total_citations": 0,
            "citations": [],
            "bibliography": [],
            "citation_style": style,
            "error": str(e)
        }


# Tool registry for agent SDK integration
HISTORICAL_TOOL_FUNCTIONS = {
    "search_documents": {
        "function": search_documents,
        "input_schema": DocumentSearchInput,
        "output_schema": DocumentSearchOutput,
        "description": "Search through uploaded historical documents for relevant information",
        "parameters": ["query", "document_ids (optional)"]
    },
    "build_timeline": {
        "function": build_timeline,
        "input_schema": TimelineBuilderInput,
        "output_schema": TimelineBuilderOutput,
        "description": "Extract and organize dates, events, and chronological information",
        "parameters": ["document_ids (optional)"]
    },
    "extract_entities": {
        "function": extract_entities,
        "input_schema": EntityExtractorInput,
        "output_schema": EntityExtractorOutput,
        "description": "Identify people, places, battles, and historical entities",
        "parameters": ["document_ids (optional)"]
    },
    "cross_reference_documents": {
        "function": cross_reference_documents,
        "input_schema": CrossReferenceInput,
        "output_schema": CrossReferenceOutput,
        "description": "Compare information across multiple documents",
        "parameters": ["topic", "document_ids (optional)"]
    },
    "generate_citations": {
        "function": generate_citations,
        "input_schema": CitationGeneratorInput,
        "output_schema": CitationGeneratorOutput,
        "description": "Create proper academic citations for sources",
        "parameters": ["search_results", "style (optional)"]
    }
}


def get_tool_function(tool_name: str):
    """
    Get a tool function by name for agent SDK integration.
    
    Args:
        tool_name: Name of the tool function
        
    Returns:
        Tool function or None if not found
    """
    tool_info = HISTORICAL_TOOL_FUNCTIONS.get(tool_name)
    return tool_info["function"] if tool_info else None


def get_tool_schema(tool_name: str):
    """
    Get input and output schemas for a tool function.
    
    Args:
        tool_name: Name of the tool function
        
    Returns:
        Dictionary with input and output schemas or None if not found
    """
    tool_info = HISTORICAL_TOOL_FUNCTIONS.get(tool_name)
    if tool_info:
        return {
            "input_schema": tool_info["input_schema"],
            "output_schema": tool_info["output_schema"],
            "description": tool_info["description"],
            "parameters": tool_info["parameters"]
        }
    return None


def list_available_tools() -> Dict[str, Dict[str, Any]]:
    """
    List all available tool functions with their descriptions and schemas.
    
    Returns:
        Dictionary of available tools with metadata
    """
    return {
        tool_name: {
            "description": tool_info["description"],
            "parameters": tool_info["parameters"],
            "input_schema": tool_info["input_schema"].schema(),
            "output_schema": tool_info["output_schema"].schema()
        }
        for tool_name, tool_info in HISTORICAL_TOOL_FUNCTIONS.items()
    }