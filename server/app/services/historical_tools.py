"""
Historical document analysis tools for specialized agent capabilities.

This module provides tools optimized for historical document analysis including:
- Document search with historical terminology optimization
- Timeline builder for chronological information extraction
- Entity extractor for historical people, places, and events
- Cross-reference tool for comparing information across documents
- Citation generator for proper academic source attribution
"""
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

import google.generativeai as genai
from fastapi import HTTPException

from app.core.config import settings
from app.services.vector_search import vector_search_service, SearchConfig
from app.services.embeddings import embedding_service
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


@dataclass
class TimelineEvent:
    """Represents a historical event with temporal information."""
    date: str
    event: str
    source_document: str
    page_number: Optional[int]
    confidence: float
    date_type: str  # 'exact', 'approximate', 'range', 'relative'


@dataclass
class HistoricalEntity:
    """Represents a historical entity (person, place, event)."""
    name: str
    entity_type: str  # 'person', 'place', 'battle', 'organization', 'concept'
    context: str
    source_document: str
    page_number: Optional[int]
    mentions: int
    related_entities: List[str]


@dataclass
class CrossReference:
    """Represents a cross-reference between documents."""
    topic: str
    document1: str
    document2: str
    similarity_score: float
    common_entities: List[str]
    contradictions: List[str]
    supporting_evidence: List[str]


@dataclass
class Citation:
    """Represents an academic citation."""
    document_name: str
    page_number: Optional[int]
    quote: str
    citation_format: str
    context: str


class HistoricalDocumentSearchTool:
    """Document search tool optimized for historical terminology and context."""
    
    def __init__(self):
        """Initialize the historical document search tool."""
        self.historical_terms = {
            # Military terms
            'legion', 'cohort', 'century', 'maniple', 'hastati', 'principes', 'triarii',
            'phalanx', 'hoplite', 'sarissa', 'aspis', 'dory', 'xiphos',
            'cavalry', 'infantry', 'siege', 'fortification', 'camp', 'battle',
            
            # Political terms
            'consul', 'praetor', 'quaestor', 'senate', 'republic', 'empire',
            'democracy', 'oligarchy', 'tyranny', 'archon', 'strategos',
            
            # Geographic terms
            'mediterranean', 'aegean', 'adriatic', 'tiber', 'rubicon',
            'thermopylae', 'marathon', 'salamis', 'cannae', 'zama',
            
            # Temporal terms
            'bc', 'ad', 'bce', 'ce', 'century', 'decade', 'era', 'period'
        }
    
    async def search(self, query: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search historical documents with terminology optimization.
        
        Args:
            query: Search query with historical context
            document_ids: Optional list of document IDs to search within
            
        Returns:
            Dictionary with search results and historical context
        """
        try:
            # Enhance query with historical context
            enhanced_query = await self._enhance_historical_query(query)
            
            # Configure search for historical documents
            search_config = SearchConfig(
                similarity_threshold=0.6,  # Lower threshold for historical terminology
                max_results=15,
                boost_recent_docs=False,  # Don't boost recent docs for historical content
                boost_page_context=True,
                min_content_length=100,
                include_metadata=True
            )
            
            # Perform vector search
            search_results = await vector_search_service.search(
                query=enhanced_query,
                config=search_config,
                document_ids=document_ids
            )
            
            # Post-process results for historical relevance
            historical_results = await self._process_historical_results(
                search_results, query
            )
            
            return {
                "query": query,
                "enhanced_query": enhanced_query,
                "results": historical_results,
                "total_results": len(historical_results),
                "search_strategy": "historical_terminology_optimized"
            }
            
        except Exception as e:
            logger.error(f"Historical document search failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Historical document search failed: {str(e)}"
            )
    
    async def _enhance_historical_query(self, query: str) -> str:
        """Enhance query with historical terminology and context."""
        try:
            # Use Gemini to expand historical context
            prompt = f"""
            Enhance this historical research query by adding relevant historical terminology and context.
            Focus on ancient history, military history, and classical civilizations.
            
            Original query: {query}
            
            Enhanced query should:
            1. Include synonyms and related historical terms
            2. Add relevant time periods if not specified
            3. Include alternative spellings of names/places
            4. Maintain the original intent
            
            Return only the enhanced query, no explanation.
            """
            
            response = genai.generate_text(
                model=f"models/{settings.GEMINI_MODEL}",
                prompt=prompt,
                temperature=0.3,
                max_output_tokens=200
            )
            
            enhanced_query = response.result.strip() if response.result else query
            
            # Add historical term boosting
            query_terms = enhanced_query.lower().split()
            historical_boost_terms = [
                term for term in query_terms 
                if term in self.historical_terms
            ]
            
            if historical_boost_terms:
                enhanced_query += f" {' '.join(historical_boost_terms)}"
            
            return enhanced_query
            
        except Exception as e:
            logger.warning(f"Failed to enhance historical query: {str(e)}")
            return query
    
    async def _process_historical_results(self, search_results: List[Any], original_query: str) -> List[Dict[str, Any]]:
        """Process search results for historical relevance."""
        try:
            processed_results = []
            
            for result in search_results:
                # Extract historical entities from content
                entities = await self._extract_quick_entities(result.content)
                
                # Calculate historical relevance score
                historical_score = self._calculate_historical_relevance(
                    result.content, original_query
                )
                
                processed_result = {
                    "chunk_id": result.chunk_id,
                    "content": result.content,
                    "similarity_score": result.similarity_score,
                    "relevance_score": result.relevance_score,
                    "historical_score": historical_score,
                    "page_number": result.page_number,
                    "source_attribution": result.source_attribution,
                    "historical_entities": entities,
                    "document_name": result.document_original_name
                }
                
                processed_results.append(processed_result)
            
            # Sort by combined historical and relevance scores
            processed_results.sort(
                key=lambda x: (x["historical_score"] + x["relevance_score"]) / 2,
                reverse=True
            )
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Failed to process historical results: {str(e)}")
            return [
                {
                    "chunk_id": r.chunk_id,
                    "content": r.content,
                    "similarity_score": r.similarity_score,
                    "relevance_score": r.relevance_score,
                    "source_attribution": r.source_attribution
                }
                for r in search_results
            ]
    
    async def _extract_quick_entities(self, text: str) -> List[str]:
        """Quick entity extraction using pattern matching."""
        entities = []
        
        # Roman names pattern (e.g., Marcus Aurelius, Gaius Julius Caesar)
        roman_names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b', text)
        entities.extend([name for name in roman_names if len(name.split()) >= 2])
        
        # Battle names (e.g., Battle of Cannae, Siege of Syracuse)
        battles = re.findall(r'\b(?:Battle|Siege|War)\s+of\s+[A-Z][a-z]+\b', text)
        entities.extend(battles)
        
        # Geographic locations (capitalized words that might be places)
        places = re.findall(r'\b[A-Z][a-z]{3,}\b', text)
        entities.extend([place for place in places if place not in ['The', 'This', 'That', 'They']])
        
        # Remove duplicates and return
        return list(set(entities))
    
    def _calculate_historical_relevance(self, content: str, query: str) -> float:
        """Calculate historical relevance score based on terminology and context."""
        try:
            content_lower = content.lower()
            query_lower = query.lower()
            
            # Base score from query term matches
            query_terms = query_lower.split()
            term_matches = sum(1 for term in query_terms if term in content_lower)
            base_score = min(term_matches / len(query_terms), 1.0)
            
            # Boost for historical terminology
            historical_term_count = sum(
                1 for term in self.historical_terms 
                if term in content_lower
            )
            historical_boost = min(historical_term_count * 0.1, 0.3)
            
            # Boost for dates and temporal references
            date_patterns = [
                r'\b\d+\s*(?:BC|AD|BCE|CE)\b',
                r'\b(?:first|second|third)\s+century\b',
                r'\b\d+\s*(?:st|nd|rd|th)\s+century\b'
            ]
            date_matches = sum(
                len(re.findall(pattern, content, re.IGNORECASE))
                for pattern in date_patterns
            )
            date_boost = min(date_matches * 0.05, 0.2)
            
            # Boost for proper nouns (likely historical entities)
            proper_nouns = len(re.findall(r'\b[A-Z][a-z]+\b', content))
            proper_noun_boost = min(proper_nouns * 0.01, 0.15)
            
            total_score = base_score + historical_boost + date_boost + proper_noun_boost
            return min(total_score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate historical relevance: {str(e)}")
            return 0.5


class TimelineBuilderTool:
    """Tool for extracting and organizing chronological information from historical documents."""
    
    def __init__(self):
        """Initialize the timeline builder tool."""
        self.date_patterns = [
            # Specific years
            (r'\b(\d{1,4})\s*(BC|BCE|AD|CE)\b', 'exact'),
            # Century references
            (r'\b(\w+)\s+century\s*(BC|BCE|AD|CE)?\b', 'century'),
            # Relative dates
            (r'\b(?:in|during|around|about|circa)\s+(\d{1,4})\s*(BC|BCE|AD|CE)\b', 'approximate'),
            # Date ranges
            (r'\b(\d{1,4})\s*-\s*(\d{1,4})\s*(BC|BCE|AD|CE)\b', 'range'),
            # Reign periods
            (r'\breign\s+of\s+([A-Z][a-z\s]+)\s*\(([^)]+)\)', 'reign')
        ]
    
    async def extract_timeline(self, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract chronological information from documents to build a timeline.
        
        Args:
            document_ids: Optional list of document IDs to analyze
            
        Returns:
            Dictionary with timeline events and chronological analysis
        """
        try:
            # Get document chunks to analyze
            chunks = await self._get_document_chunks(document_ids)
            
            # Extract temporal events from each chunk
            timeline_events = []
            for chunk in chunks:
                events = await self._extract_events_from_chunk(chunk)
                timeline_events.extend(events)
            
            # Sort events chronologically
            sorted_events = self._sort_events_chronologically(timeline_events)
            
            # Group events by time periods
            grouped_events = self._group_events_by_period(sorted_events)
            
            # Generate timeline summary
            timeline_summary = await self._generate_timeline_summary(sorted_events)
            
            return {
                "total_events": len(sorted_events),
                "timeline_events": [self._event_to_dict(event) for event in sorted_events],
                "grouped_by_period": grouped_events,
                "timeline_summary": timeline_summary,
                "date_range": self._get_date_range(sorted_events)
            }
            
        except Exception as e:
            logger.error(f"Timeline extraction failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Timeline extraction failed: {str(e)}"
            )
    
    async def _get_document_chunks(self, document_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get document chunks for timeline analysis."""
        try:
            client = get_supabase()
            
            query = client.table("document_chunks").select("""
                id, content, page_number, chunk_index,
                documents!inner(id, filename, original_name)
            """)
            
            if document_ids:
                query = query.in_("document_id", document_ids)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get document chunks: {str(e)}")
            return []
    
    async def _extract_events_from_chunk(self, chunk: Dict[str, Any]) -> List[TimelineEvent]:
        """Extract temporal events from a document chunk."""
        try:
            events = []
            content = chunk["content"]
            
            # Extract dates using patterns
            for pattern, date_type in self.date_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    # Extract context around the date
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 100)
                    context = content[start:end].strip()
                    
                    # Create timeline event
                    event = TimelineEvent(
                        date=match.group(0),
                        event=context,
                        source_document=chunk["documents"]["original_name"],
                        page_number=chunk.get("page_number"),
                        confidence=self._calculate_date_confidence(match.group(0), date_type),
                        date_type=date_type
                    )
                    
                    events.append(event)
            
            # Use AI to extract additional temporal information
            ai_events = await self._extract_ai_temporal_events(chunk)
            events.extend(ai_events)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to extract events from chunk: {str(e)}")
            return []
    
    async def _extract_ai_temporal_events(self, chunk: Dict[str, Any]) -> List[TimelineEvent]:
        """Use AI to extract temporal events that patterns might miss."""
        try:
            prompt = f"""
            Extract historical events with dates from this text. Focus on:
            1. Military campaigns and battles
            2. Political events and changes in leadership
            3. Significant historical milestones
            
            Text: {chunk['content'][:1000]}
            
            For each event, provide:
            - Date (if mentioned)
            - Brief description of the event
            - Confidence level (high/medium/low)
            
            Format as: DATE | EVENT | CONFIDENCE
            Only include events with clear temporal references.
            """
            
            response = genai.generate_text(
                model=f"models/{settings.GEMINI_MODEL}",
                prompt=prompt,
                temperature=0.2,
                max_output_tokens=300
            )
            
            if not response.result:
                return []
            
            # Parse AI response
            events = []
            lines = response.result.strip().split('\n')
            
            for line in lines:
                if '|' in line:
                    parts = [part.strip() for part in line.split('|')]
                    if len(parts) >= 3:
                        date_str, event_desc, confidence_str = parts[:3]
                        
                        confidence_map = {'high': 0.9, 'medium': 0.7, 'low': 0.5}
                        confidence = confidence_map.get(confidence_str.lower(), 0.5)
                        
                        event = TimelineEvent(
                            date=date_str,
                            event=event_desc,
                            source_document=chunk["documents"]["original_name"],
                            page_number=chunk.get("page_number"),
                            confidence=confidence,
                            date_type='ai_extracted'
                        )
                        
                        events.append(event)
            
            return events
            
        except Exception as e:
            logger.warning(f"AI temporal extraction failed: {str(e)}")
            return []
    
    def _calculate_date_confidence(self, date_str: str, date_type: str) -> float:
        """Calculate confidence score for extracted date."""
        confidence_map = {
            'exact': 0.9,
            'century': 0.7,
            'approximate': 0.6,
            'range': 0.8,
            'reign': 0.8,
            'ai_extracted': 0.5
        }
        
        base_confidence = confidence_map.get(date_type, 0.5)
        
        # Boost confidence for specific patterns
        if re.search(r'\b\d{1,4}\s*(BC|AD|BCE|CE)\b', date_str):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _sort_events_chronologically(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Sort events in chronological order."""
        try:
            def extract_year(event: TimelineEvent) -> int:
                """Extract numerical year for sorting."""
                date_str = event.date.lower()
                
                # Extract year number
                year_match = re.search(r'\b(\d{1,4})\b', date_str)
                if not year_match:
                    return 0  # Unknown dates go to beginning
                
                year = int(year_match.group(1))
                
                # Handle BC/BCE dates (negative years)
                if 'bc' in date_str or 'bce' in date_str:
                    year = -year
                
                return year
            
            return sorted(events, key=extract_year)
            
        except Exception as e:
            logger.error(f"Failed to sort events chronologically: {str(e)}")
            return events
    
    def _group_events_by_period(self, events: List[TimelineEvent]) -> Dict[str, List[Dict[str, Any]]]:
        """Group events by historical periods."""
        try:
            periods = defaultdict(list)
            
            for event in events:
                period = self._determine_historical_period(event.date)
                periods[period].append(self._event_to_dict(event))
            
            return dict(periods)
            
        except Exception as e:
            logger.error(f"Failed to group events by period: {str(e)}")
            return {"Unknown Period": [self._event_to_dict(e) for e in events]}
    
    def _determine_historical_period(self, date_str: str) -> str:
        """Determine historical period for a date."""
        try:
            date_lower = date_str.lower()
            
            # Extract year for period classification
            year_match = re.search(r'\b(\d{1,4})\b', date_lower)
            if not year_match:
                return "Unknown Period"
            
            year = int(year_match.group(1))
            
            # Handle BC dates (remember BC dates count backwards - higher numbers are earlier)
            if 'bc' in date_lower or 'bce' in date_lower:
                if year > 800:
                    return "Archaic Period (800+ BC)"
                elif year > 480:
                    return "Classical Period (480-323 BC)"
                elif year > 323:
                    return "Early Classical (480-323 BC)"
                elif year > 146:
                    return "Hellenistic Period (323-146 BC)"
                elif year > 27:
                    return "Roman Republic (146-27 BC)"
                else:
                    return "Early Roman Empire"
            else:
                # AD dates
                if year <= 476:
                    return "Roman Empire (27 BC - 476 AD)"
                elif year <= 1000:
                    return "Early Medieval (476-1000 AD)"
                else:
                    return "Medieval Period (1000+ AD)"
            
        except Exception as e:
            logger.error(f"Failed to determine historical period: {str(e)}")
            return "Unknown Period"
    
    async def _generate_timeline_summary(self, events: List[TimelineEvent]) -> str:
        """Generate a summary of the timeline."""
        try:
            if not events:
                return "No temporal events found in the documents."
            
            # Create summary of key events
            key_events = [
                f"- {event.date}: {event.event[:100]}..." 
                for event in events[:10]  # Top 10 events
            ]
            
            prompt = f"""
            Create a concise historical timeline summary based on these events:
            
            {chr(10).join(key_events)}
            
            Provide:
            1. Overall time period covered
            2. Major themes and developments
            3. Key turning points
            4. Historical significance
            
            Keep it under 200 words and focus on historical analysis.
            """
            
            response = genai.generate_text(
                model=f"models/{settings.GEMINI_MODEL}",
                prompt=prompt,
                temperature=0.3,
                max_output_tokens=250
            )
            
            return response.result.strip() if response.result else "Timeline summary unavailable."
            
        except Exception as e:
            logger.error(f"Failed to generate timeline summary: {str(e)}")
            return f"Timeline contains {len(events)} events spanning multiple historical periods."
    
    def _get_date_range(self, events: List[TimelineEvent]) -> Dict[str, str]:
        """Get the date range covered by the timeline."""
        if not events:
            return {"start": "Unknown", "end": "Unknown"}
        
        return {
            "start": events[0].date if events else "Unknown",
            "end": events[-1].date if events else "Unknown"
        }
    
    def _event_to_dict(self, event: TimelineEvent) -> Dict[str, Any]:
        """Convert TimelineEvent to dictionary."""
        return {
            "date": event.date,
            "event": event.event,
            "source_document": event.source_document,
            "page_number": event.page_number,
            "confidence": event.confidence,
            "date_type": event.date_type
        }


# Global tool instances
historical_search_tool = HistoricalDocumentSearchTool()
timeline_builder_tool = TimelineBuilderTool()

class EntityExtractorTool:
    """Tool for identifying and extracting historical entities (people, places, events)."""
    
    def __init__(self):
        """Initialize the entity extractor tool."""
        self.entity_patterns = {
            'person': [
                r'\b(?:Emperor|King|Queen|General|Admiral|Senator|Consul)\s+([A-Z][a-z\s]+)\b',
                r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:led|commanded|ruled|conquered)\b',
                r'\b([A-Z][a-z]+)\s+(?:the Great|the Elder|the Younger|Caesar|Augustus)\b'
            ],
            'place': [
                r'\b(?:city|town|province|region|kingdom|empire)\s+of\s+([A-Z][a-z]+)\b',
                r'\b([A-Z][a-z]+)\s+(?:River|Sea|Mountain|Hill|Valley|Plain)\b',
                r'\b(?:in|at|near|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
            ],
            'battle': [
                r'\b(?:Battle|Siege|War)\s+(?:of|at)\s+([A-Z][a-z\s]+)\b',
                r'\b([A-Z][a-z\s]+)\s+(?:Campaign|Expedition|War)\b'
            ],
            'organization': [
                r'\b([A-Z][a-z]+)\s+(?:Legion|Army|Navy|Senate|Republic|Empire)\b',
                r'\b(?:the)\s+([A-Z][a-z\s]+)\s+(?:Alliance|League|Confederation)\b'
            ]
        }
    
    async def extract_entities(self, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract historical entities from documents.
        
        Args:
            document_ids: Optional list of document IDs to analyze
            
        Returns:
            Dictionary with extracted entities organized by type
        """
        try:
            # Get document chunks to analyze
            chunks = await self._get_document_chunks(document_ids)
            
            # Extract entities using pattern matching
            pattern_entities = await self._extract_pattern_entities(chunks)
            
            # Extract entities using AI
            ai_entities = await self._extract_ai_entities(chunks)
            
            # Merge and deduplicate entities
            all_entities = self._merge_entities(pattern_entities, ai_entities)
            
            # Calculate entity relationships
            entity_relationships = await self._calculate_entity_relationships(all_entities, chunks)
            
            # Generate entity summary
            entity_summary = await self._generate_entity_summary(all_entities)
            
            return {
                "total_entities": sum(len(entities) for entities in all_entities.values()),
                "entities_by_type": {
                    entity_type: [self._entity_to_dict(entity) for entity in entities]
                    for entity_type, entities in all_entities.items()
                },
                "entity_relationships": entity_relationships,
                "entity_summary": entity_summary,
                "extraction_method": "hybrid_pattern_ai"
            }
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Entity extraction failed: {str(e)}"
            )
    
    async def _get_document_chunks(self, document_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get document chunks for entity analysis."""
        try:
            client = get_supabase()
            
            query = client.table("document_chunks").select("""
                id, content, page_number, chunk_index,
                documents!inner(id, filename, original_name)
            """)
            
            if document_ids:
                query = query.in_("document_id", document_ids)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get document chunks: {str(e)}")
            return []
    
    async def _extract_pattern_entities(self, chunks: List[Dict[str, Any]]) -> Dict[str, List[HistoricalEntity]]:
        """Extract entities using regex patterns."""
        try:
            entities_by_type = defaultdict(list)
            
            for chunk in chunks:
                content = chunk["content"]
                doc_name = chunk["documents"]["original_name"]
                page_num = chunk.get("page_number")
                
                for entity_type, patterns in self.entity_patterns.items():
                    for pattern in patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        
                        for match in matches:
                            entity_name = match.group(1).strip()
                            
                            # Extract context around the entity
                            start = max(0, match.start() - 50)
                            end = min(len(content), match.end() + 50)
                            context = content[start:end].strip()
                            
                            # Create entity
                            entity = HistoricalEntity(
                                name=entity_name,
                                entity_type=entity_type,
                                context=context,
                                source_document=doc_name,
                                page_number=page_num,
                                mentions=1,
                                related_entities=[]
                            )
                            
                            entities_by_type[entity_type].append(entity)
            
            # Deduplicate and count mentions
            return self._deduplicate_entities(entities_by_type)
            
        except Exception as e:
            logger.error(f"Pattern entity extraction failed: {str(e)}")
            return defaultdict(list)
    
    async def _extract_ai_entities(self, chunks: List[Dict[str, Any]]) -> Dict[str, List[HistoricalEntity]]:
        """Extract entities using AI for better accuracy."""
        try:
            entities_by_type = defaultdict(list)
            
            # Process chunks in batches to avoid token limits
            batch_size = 5
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                # Combine batch content
                batch_content = "\n\n".join([
                    f"[Document: {chunk['documents']['original_name']}]\n{chunk['content'][:500]}"
                    for chunk in batch
                ])
                
                prompt = f"""
                Extract historical entities from this ancient history text. Focus on:
                
                PEOPLE: Historical figures, rulers, generals, philosophers, etc.
                PLACES: Cities, regions, countries, geographical features, battlefields
                BATTLES: Military engagements, wars, campaigns, sieges
                ORGANIZATIONS: Armies, political bodies, alliances, institutions
                
                Text:
                {batch_content}
                
                For each entity, provide:
                ENTITY_TYPE | ENTITY_NAME | BRIEF_CONTEXT
                
                Only include entities clearly mentioned in the text.
                """
                
                try:
                    response = genai.generate_text(
                        model=f"models/{settings.GEMINI_MODEL}",
                        prompt=prompt,
                        temperature=0.2,
                        max_output_tokens=400
                    )
                    
                    if response.result:
                        ai_entities = self._parse_ai_entity_response(
                            response.result, batch
                        )
                        
                        for entity_type, entities in ai_entities.items():
                            entities_by_type[entity_type].extend(entities)
                
                except Exception as e:
                    logger.warning(f"AI entity extraction failed for batch: {str(e)}")
                    continue
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
            return dict(entities_by_type)
            
        except Exception as e:
            logger.error(f"AI entity extraction failed: {str(e)}")
            return defaultdict(list)
    
    def _parse_ai_entity_response(self, response: str, chunks: List[Dict[str, Any]]) -> Dict[str, List[HistoricalEntity]]:
        """Parse AI response to extract entities."""
        try:
            entities_by_type = defaultdict(list)
            lines = response.strip().split('\n')
            
            for line in lines:
                if '|' in line:
                    parts = [part.strip() for part in line.split('|')]
                    if len(parts) >= 3:
                        entity_type_raw, entity_name, context = parts[:3]
                        
                        # Normalize entity type
                        entity_type = entity_type_raw.lower()
                        if 'person' in entity_type or 'people' in entity_type:
                            entity_type = 'person'
                        elif 'place' in entity_type or 'location' in entity_type:
                            entity_type = 'place'
                        elif 'battle' in entity_type or 'war' in entity_type:
                            entity_type = 'battle'
                        elif 'organization' in entity_type or 'group' in entity_type:
                            entity_type = 'organization'
                        else:
                            entity_type = 'concept'
                        
                        # Find source document (use first chunk as approximation)
                        source_doc = chunks[0]["documents"]["original_name"] if chunks else "Unknown"
                        page_num = chunks[0].get("page_number") if chunks else None
                        
                        entity = HistoricalEntity(
                            name=entity_name,
                            entity_type=entity_type,
                            context=context,
                            source_document=source_doc,
                            page_number=page_num,
                            mentions=1,
                            related_entities=[]
                        )
                        
                        entities_by_type[entity_type].append(entity)
            
            return dict(entities_by_type)
            
        except Exception as e:
            logger.error(f"Failed to parse AI entity response: {str(e)}")
            return defaultdict(list)
    
    def _merge_entities(self, pattern_entities: Dict[str, List[HistoricalEntity]], 
                       ai_entities: Dict[str, List[HistoricalEntity]]) -> Dict[str, List[HistoricalEntity]]:
        """Merge and deduplicate entities from different extraction methods."""
        try:
            merged = defaultdict(list)
            
            # Add pattern entities
            for entity_type, entities in pattern_entities.items():
                merged[entity_type].extend(entities)
            
            # Add AI entities, checking for duplicates
            for entity_type, entities in ai_entities.items():
                for entity in entities:
                    # Check if similar entity already exists
                    is_duplicate = False
                    for existing in merged[entity_type]:
                        if self._entities_similar(entity, existing):
                            existing.mentions += 1
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        merged[entity_type].append(entity)
            
            return dict(merged)
            
        except Exception as e:
            logger.error(f"Failed to merge entities: {str(e)}")
            return pattern_entities
    
    def _entities_similar(self, entity1: HistoricalEntity, entity2: HistoricalEntity) -> bool:
        """Check if two entities are similar (likely the same entity)."""
        try:
            name1 = entity1.name.lower().strip()
            name2 = entity2.name.lower().strip()
            
            # Exact match
            if name1 == name2:
                return True
            
            # Check if one name contains the other
            if name1 in name2 or name2 in name1:
                return True
            
            # Check for common abbreviations or variations
            name1_words = set(name1.split())
            name2_words = set(name2.split())
            
            # If they share significant words, consider similar
            if len(name1_words & name2_words) >= min(len(name1_words), len(name2_words)) * 0.7:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to compare entities: {str(e)}")
            return False
    
    def _deduplicate_entities(self, entities_by_type: Dict[str, List[HistoricalEntity]]) -> Dict[str, List[HistoricalEntity]]:
        """Remove duplicate entities and count mentions."""
        try:
            deduplicated = {}
            
            for entity_type, entities in entities_by_type.items():
                unique_entities = []
                
                for entity in entities:
                    # Find existing similar entity
                    found_similar = False
                    for existing in unique_entities:
                        if self._entities_similar(entity, existing):
                            existing.mentions += 1
                            found_similar = True
                            break
                    
                    if not found_similar:
                        unique_entities.append(entity)
                
                deduplicated[entity_type] = unique_entities
            
            return deduplicated
            
        except Exception as e:
            logger.error(f"Failed to deduplicate entities: {str(e)}")
            return entities_by_type
    
    async def _calculate_entity_relationships(self, entities: Dict[str, List[HistoricalEntity]], 
                                            chunks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Calculate relationships between entities based on co-occurrence."""
        try:
            relationships = defaultdict(list)
            
            # Get all entity names
            all_entities = []
            for entity_list in entities.values():
                all_entities.extend([(e.name, e.entity_type) for e in entity_list])
            
            # Find co-occurrences in chunks
            for chunk in chunks:
                content = chunk["content"].lower()
                
                # Find entities mentioned in this chunk
                mentioned_entities = []
                for entity_name, entity_type in all_entities:
                    if entity_name.lower() in content:
                        mentioned_entities.append(entity_name)
                
                # Create relationships between co-occurring entities
                for i, entity1 in enumerate(mentioned_entities):
                    for entity2 in mentioned_entities[i+1:]:
                        if entity1 != entity2:
                            relationships[entity1].append(entity2)
                            relationships[entity2].append(entity1)
            
            # Deduplicate relationships
            for entity, related in relationships.items():
                relationships[entity] = list(set(related))
            
            return dict(relationships)
            
        except Exception as e:
            logger.error(f"Failed to calculate entity relationships: {str(e)}")
            return {}
    
    async def _generate_entity_summary(self, entities: Dict[str, List[HistoricalEntity]]) -> str:
        """Generate a summary of extracted entities."""
        try:
            if not entities:
                return "No entities extracted from the documents."
            
            # Count entities by type
            entity_counts = {
                entity_type: len(entity_list)
                for entity_type, entity_list in entities.items()
            }
            
            # Get top entities by mentions
            top_entities = []
            for entity_list in entities.values():
                top_entities.extend(entity_list)
            
            top_entities.sort(key=lambda x: x.mentions, reverse=True)
            top_entities = top_entities[:10]
            
            summary_parts = [
                f"Extracted {sum(entity_counts.values())} unique historical entities:",
                ""
            ]
            
            for entity_type, count in entity_counts.items():
                summary_parts.append(f"- {entity_type.title()}: {count}")
            
            if top_entities:
                summary_parts.extend([
                    "",
                    "Most frequently mentioned:",
                    ""
                ])
                
                for entity in top_entities[:5]:
                    summary_parts.append(
                        f"- {entity.name} ({entity.entity_type}, {entity.mentions} mentions)"
                    )
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate entity summary: {str(e)}")
            return "Entity summary unavailable."
    
    def _entity_to_dict(self, entity: HistoricalEntity) -> Dict[str, Any]:
        """Convert HistoricalEntity to dictionary."""
        return {
            "name": entity.name,
            "entity_type": entity.entity_type,
            "context": entity.context,
            "source_document": entity.source_document,
            "page_number": entity.page_number,
            "mentions": entity.mentions,
            "related_entities": entity.related_entities
        }


class CrossReferenceTool:
    """Tool for comparing information across multiple historical documents."""
    
    def __init__(self):
        """Initialize the cross-reference tool."""
        pass
    
    async def cross_reference_documents(self, topic: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare information about a topic across multiple documents.
        
        Args:
            topic: Topic to cross-reference across documents
            document_ids: Optional list of document IDs to compare
            
        Returns:
            Dictionary with cross-reference analysis
        """
        try:
            # Search for the topic across documents
            search_results = await historical_search_tool.search(topic, document_ids)
            
            if not search_results["results"]:
                return {
                    "topic": topic,
                    "cross_references": [],
                    "summary": "No information found about this topic in the documents."
                }
            
            # Group results by document
            results_by_document = self._group_results_by_document(search_results["results"])
            
            # Find cross-references between documents
            cross_references = await self._find_cross_references(topic, results_by_document)
            
            # Analyze agreements and contradictions
            analysis = await self._analyze_cross_references(topic, cross_references)
            
            # Generate cross-reference summary
            summary = await self._generate_cross_reference_summary(topic, analysis)
            
            return {
                "topic": topic,
                "documents_analyzed": len(results_by_document),
                "cross_references": [self._cross_ref_to_dict(cr) for cr in cross_references],
                "analysis": analysis,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Cross-reference analysis failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Cross-reference analysis failed: {str(e)}"
            )
    
    def _group_results_by_document(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group search results by source document."""
        try:
            grouped = defaultdict(list)
            
            for result in results:
                doc_name = result.get("document_name", "Unknown Document")
                grouped[doc_name].append(result)
            
            return dict(grouped)
            
        except Exception as e:
            logger.error(f"Failed to group results by document: {str(e)}")
            return {}
    
    async def _find_cross_references(self, topic: str, results_by_document: Dict[str, List[Dict[str, Any]]]) -> List[CrossReference]:
        """Find cross-references between documents."""
        try:
            cross_references = []
            document_names = list(results_by_document.keys())
            
            # Compare each pair of documents
            for i, doc1 in enumerate(document_names):
                for doc2 in document_names[i+1:]:
                    doc1_results = results_by_document[doc1]
                    doc2_results = results_by_document[doc2]
                    
                    # Calculate similarity between document contents
                    similarity_score = await self._calculate_document_similarity(
                        doc1_results, doc2_results
                    )
                    
                    # Find common entities
                    common_entities = self._find_common_entities(doc1_results, doc2_results)
                    
                    # Analyze for contradictions and supporting evidence
                    contradictions, supporting_evidence = await self._analyze_document_pair(
                        topic, doc1_results, doc2_results
                    )
                    
                    cross_ref = CrossReference(
                        topic=topic,
                        document1=doc1,
                        document2=doc2,
                        similarity_score=similarity_score,
                        common_entities=common_entities,
                        contradictions=contradictions,
                        supporting_evidence=supporting_evidence
                    )
                    
                    cross_references.append(cross_ref)
            
            return cross_references
            
        except Exception as e:
            logger.error(f"Failed to find cross-references: {str(e)}")
            return []
    
    async def _calculate_document_similarity(self, doc1_results: List[Dict[str, Any]], 
                                           doc2_results: List[Dict[str, Any]]) -> float:
        """Calculate similarity between document contents."""
        try:
            # Combine content from each document
            doc1_content = " ".join([result["content"] for result in doc1_results])
            doc2_content = " ".join([result["content"] for result in doc2_results])
            
            # Generate embeddings for comparison
            doc1_embedding = await embedding_service.generate_query_embedding(doc1_content[:1000])
            doc2_embedding = await embedding_service.generate_query_embedding(doc2_content[:1000])
            
            # Calculate cosine similarity
            import numpy as np
            
            doc1_vec = np.array(doc1_embedding)
            doc2_vec = np.array(doc2_embedding)
            
            similarity = np.dot(doc1_vec, doc2_vec) / (np.linalg.norm(doc1_vec) * np.linalg.norm(doc2_vec))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate document similarity: {str(e)}")
            return 0.0
    
    def _find_common_entities(self, doc1_results: List[Dict[str, Any]], 
                             doc2_results: List[Dict[str, Any]]) -> List[str]:
        """Find common entities mentioned in both documents."""
        try:
            # Extract entities from both documents
            doc1_entities = set()
            doc2_entities = set()
            
            for result in doc1_results:
                entities = result.get("historical_entities", [])
                doc1_entities.update(entities)
            
            for result in doc2_results:
                entities = result.get("historical_entities", [])
                doc2_entities.update(entities)
            
            # Find intersection
            common_entities = list(doc1_entities & doc2_entities)
            
            return common_entities
            
        except Exception as e:
            logger.error(f"Failed to find common entities: {str(e)}")
            return []
    
    async def _analyze_document_pair(self, topic: str, doc1_results: List[Dict[str, Any]], 
                                   doc2_results: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Analyze a pair of documents for contradictions and supporting evidence."""
        try:
            # Combine content from each document
            doc1_content = "\n".join([result["content"] for result in doc1_results[:3]])  # Limit content
            doc2_content = "\n".join([result["content"] for result in doc2_results[:3]])
            
            doc1_name = doc1_results[0]["document_name"] if doc1_results else "Document 1"
            doc2_name = doc2_results[0]["document_name"] if doc2_results else "Document 2"
            
            prompt = f"""
            Compare these two historical sources about "{topic}":
            
            Source 1 ({doc1_name}):
            {doc1_content[:800]}
            
            Source 2 ({doc2_name}):
            {doc2_content[:800]}
            
            Identify:
            1. CONTRADICTIONS: Where the sources disagree or present conflicting information
            2. SUPPORTING_EVIDENCE: Where the sources agree or support each other
            
            Format:
            CONTRADICTIONS:
            - [specific contradiction]
            
            SUPPORTING_EVIDENCE:
            - [specific agreement or mutual support]
            
            Focus on factual differences and agreements, not stylistic variations.
            """
            
            response = genai.generate_text(
                model=f"models/{settings.GEMINI_MODEL}",
                prompt=prompt,
                temperature=0.2,
                max_output_tokens=400
            )
            
            if not response.result:
                return [], []
            
            # Parse response
            contradictions = []
            supporting_evidence = []
            
            lines = response.result.strip().split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if 'CONTRADICTIONS:' in line:
                    current_section = 'contradictions'
                elif 'SUPPORTING_EVIDENCE:' in line:
                    current_section = 'supporting'
                elif line.startswith('- ') and current_section:
                    item = line[2:].strip()
                    if current_section == 'contradictions':
                        contradictions.append(item)
                    elif current_section == 'supporting':
                        supporting_evidence.append(item)
            
            return contradictions, supporting_evidence
            
        except Exception as e:
            logger.error(f"Failed to analyze document pair: {str(e)}")
            return [], []
    
    async def _analyze_cross_references(self, topic: str, cross_references: List[CrossReference]) -> Dict[str, Any]:
        """Analyze cross-references to identify patterns and insights."""
        try:
            if not cross_references:
                return {"overall_consensus": "No cross-references found"}
            
            # Count contradictions and agreements
            total_contradictions = sum(len(cr.contradictions) for cr in cross_references)
            total_agreements = sum(len(cr.supporting_evidence) for cr in cross_references)
            
            # Find most common entities across documents
            all_common_entities = []
            for cr in cross_references:
                all_common_entities.extend(cr.common_entities)
            
            entity_counts = defaultdict(int)
            for entity in all_common_entities:
                entity_counts[entity] += 1
            
            most_common_entities = sorted(
                entity_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            # Calculate average similarity
            avg_similarity = sum(cr.similarity_score for cr in cross_references) / len(cross_references)
            
            # Determine overall consensus
            if total_agreements > total_contradictions * 2:
                consensus = "Strong agreement across sources"
            elif total_agreements > total_contradictions:
                consensus = "General agreement with some discrepancies"
            elif total_contradictions > total_agreements:
                consensus = "Significant disagreements between sources"
            else:
                consensus = "Mixed evidence with balanced agreements and contradictions"
            
            return {
                "overall_consensus": consensus,
                "total_contradictions": total_contradictions,
                "total_agreements": total_agreements,
                "average_similarity": round(avg_similarity, 3),
                "most_common_entities": [{"entity": entity, "mentions": count} for entity, count in most_common_entities],
                "documents_compared": len(set([cr.document1 for cr in cross_references] + [cr.document2 for cr in cross_references]))
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze cross-references: {str(e)}")
            return {"overall_consensus": "Analysis unavailable"}
    
    async def _generate_cross_reference_summary(self, topic: str, analysis: Dict[str, Any]) -> str:
        """Generate a summary of the cross-reference analysis."""
        try:
            consensus = analysis.get("overall_consensus", "Unknown")
            contradictions = analysis.get("total_contradictions", 0)
            agreements = analysis.get("total_agreements", 0)
            docs_compared = analysis.get("documents_compared", 0)
            
            summary_parts = [
                f"Cross-reference analysis for '{topic}':",
                f"- Analyzed {docs_compared} documents",
                f"- Found {agreements} points of agreement and {contradictions} contradictions",
                f"- Overall assessment: {consensus}"
            ]
            
            common_entities = analysis.get("most_common_entities", [])
            if common_entities:
                summary_parts.extend([
                    "",
                    "Key entities mentioned across sources:",
                    ""
                ])
                for entity_info in common_entities[:3]:
                    summary_parts.append(f"- {entity_info['entity']} (mentioned in {entity_info['mentions']} comparisons)")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate cross-reference summary: {str(e)}")
            return f"Cross-reference analysis completed for '{topic}'"
    
    def _cross_ref_to_dict(self, cross_ref: CrossReference) -> Dict[str, Any]:
        """Convert CrossReference to dictionary."""
        return {
            "topic": cross_ref.topic,
            "document1": cross_ref.document1,
            "document2": cross_ref.document2,
            "similarity_score": cross_ref.similarity_score,
            "common_entities": cross_ref.common_entities,
            "contradictions": cross_ref.contradictions,
            "supporting_evidence": cross_ref.supporting_evidence
        }


class CitationGeneratorTool:
    """Tool for generating proper academic citations for historical sources."""
    
    def __init__(self):
        """Initialize the citation generator tool."""
        self.citation_styles = {
            'chicago': self._format_chicago_citation,
            'mla': self._format_mla_citation,
            'apa': self._format_apa_citation,
            'academic': self._format_academic_citation
        }
    
    async def generate_citations(self, search_results: List[Dict[str, Any]], 
                               style: str = 'academic') -> Dict[str, Any]:
        """
        Generate academic citations for search results.
        
        Args:
            search_results: List of search results to cite
            style: Citation style ('chicago', 'mla', 'apa', 'academic')
            
        Returns:
            Dictionary with formatted citations
        """
        try:
            if style not in self.citation_styles:
                style = 'academic'
            
            formatter = self.citation_styles[style]
            
            citations = []
            bibliography = []
            
            for result in search_results:
                # Create citation object
                citation = Citation(
                    document_name=result.get("document_name", "Unknown Document"),
                    page_number=result.get("page_number"),
                    quote=result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                    citation_format=style,
                    context=result.get("source_attribution", "")
                )
                
                # Format citation
                formatted_citation = formatter(citation)
                citations.append({
                    "citation": formatted_citation,
                    "quote": citation.quote,
                    "page_number": citation.page_number,
                    "document": citation.document_name
                })
                
                # Add to bibliography (deduplicated)
                bib_entry = self._create_bibliography_entry(citation, style)
                if bib_entry not in bibliography:
                    bibliography.append(bib_entry)
            
            # Generate citation summary
            citation_summary = self._generate_citation_summary(citations, style)
            
            return {
                "citation_style": style,
                "total_citations": len(citations),
                "citations": citations,
                "bibliography": bibliography,
                "citation_summary": citation_summary,
                "usage_note": f"Citations formatted in {style.upper()} style for academic use"
            }
            
        except Exception as e:
            logger.error(f"Citation generation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Citation generation failed: {str(e)}"
            )
    
    def _format_chicago_citation(self, citation: Citation) -> str:
        """Format citation in Chicago style."""
        try:
            doc_name = citation.document_name
            page_ref = f", {citation.page_number}" if citation.page_number else ""
            
            return f"{doc_name}{page_ref}."
            
        except Exception as e:
            logger.error(f"Failed to format Chicago citation: {str(e)}")
            return f"{citation.document_name}."
    
    def _format_mla_citation(self, citation: Citation) -> str:
        """Format citation in MLA style."""
        try:
            doc_name = citation.document_name
            page_ref = f" {citation.page_number}" if citation.page_number else ""
            
            return f"({doc_name}{page_ref})"
            
        except Exception as e:
            logger.error(f"Failed to format MLA citation: {str(e)}")
            return f"({citation.document_name})"
    
    def _format_apa_citation(self, citation: Citation) -> str:
        """Format citation in APA style."""
        try:
            doc_name = citation.document_name
            page_ref = f", p. {citation.page_number}" if citation.page_number else ""
            
            return f"({doc_name}{page_ref})"
            
        except Exception as e:
            logger.error(f"Failed to format APA citation: {str(e)}")
            return f"({citation.document_name})"
    
    def _format_academic_citation(self, citation: Citation) -> str:
        """Format citation in general academic style."""
        try:
            doc_name = citation.document_name
            page_ref = f", p. {citation.page_number}" if citation.page_number else ""
            
            return f"[{doc_name}{page_ref}]"
            
        except Exception as e:
            logger.error(f"Failed to format academic citation: {str(e)}")
            return f"[{citation.document_name}]"
    
    def _create_bibliography_entry(self, citation: Citation, style: str) -> str:
        """Create bibliography entry for the citation."""
        try:
            doc_name = citation.document_name
            
            if style == 'chicago':
                return f"{doc_name}. Historical Document."
            elif style == 'mla':
                return f"{doc_name}. Historical Document. PDF."
            elif style == 'apa':
                return f"{doc_name}. Historical document."
            else:  # academic
                return f"{doc_name} - Historical Document"
            
        except Exception as e:
            logger.error(f"Failed to create bibliography entry: {str(e)}")
            return citation.document_name
    
    def _generate_citation_summary(self, citations: List[Dict[str, Any]], style: str) -> str:
        """Generate a summary of the citations."""
        try:
            if not citations:
                return "No citations generated."
            
            # Count unique documents
            unique_docs = set(c["document"] for c in citations)
            
            # Count citations with page numbers
            with_pages = sum(1 for c in citations if c["page_number"])
            
            summary_parts = [
                f"Generated {len(citations)} citations in {style.upper()} format:",
                f"- Sources: {len(unique_docs)} unique documents",
                f"- Page references: {with_pages} citations include page numbers",
                "",
                "Usage: Copy citations and bibliography for academic papers."
            ]
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate citation summary: {str(e)}")
            return f"Generated {len(citations)} citations in {style.upper()} format."


# Global tool instances
entity_extractor_tool = EntityExtractorTool()
cross_reference_tool = CrossReferenceTool()
citation_generator_tool = CitationGeneratorTool()


class HistoricalAnalysisToolkit:
    """
    Main interface for all historical document analysis tools.
    Provides a unified API for accessing specialized historical analysis capabilities.
    """
    
    def __init__(self):
        """Initialize the historical analysis toolkit."""
        self.document_search = historical_search_tool
        self.timeline_builder = timeline_builder_tool
        self.entity_extractor = entity_extractor_tool
        self.cross_reference = cross_reference_tool
        self.citation_generator = citation_generator_tool
        
        # Tool registry for dynamic access
        self.tools = {
            'document_search': self.search_documents,
            'timeline_builder': self.build_timeline,
            'entity_extractor': self.extract_entities,
            'cross_reference': self.cross_reference_documents,
            'citation_generator': self.generate_citations
        }
    
    async def search_documents(self, query: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search historical documents with terminology optimization.
        
        Args:
            query: Search query with historical context
            document_ids: Optional list of document IDs to search within
            
        Returns:
            Dictionary with enhanced search results
        """
        return await self.document_search.search(query, document_ids)
    
    async def build_timeline(self, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract and organize chronological information from documents.
        
        Args:
            document_ids: Optional list of document IDs to analyze
            
        Returns:
            Dictionary with timeline events and analysis
        """
        return await self.timeline_builder.extract_timeline(document_ids)
    
    async def extract_entities(self, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract historical entities (people, places, events) from documents.
        
        Args:
            document_ids: Optional list of document IDs to analyze
            
        Returns:
            Dictionary with extracted entities organized by type
        """
        return await self.entity_extractor.extract_entities(document_ids)
    
    async def cross_reference_documents(self, topic: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare information about a topic across multiple documents.
        
        Args:
            topic: Topic to cross-reference across documents
            document_ids: Optional list of document IDs to compare
            
        Returns:
            Dictionary with cross-reference analysis
        """
        return await self.cross_reference.cross_reference_documents(topic, document_ids)
    
    async def generate_citations(self, search_results: List[Dict[str, Any]], 
                               style: str = 'academic') -> Dict[str, Any]:
        """
        Generate academic citations for search results.
        
        Args:
            search_results: List of search results to cite
            style: Citation style ('chicago', 'mla', 'apa', 'academic')
            
        Returns:
            Dictionary with formatted citations and bibliography
        """
        return await self.citation_generator.generate_citations(search_results, style)
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a specific tool by name with provided arguments.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Tool execution results
            
        Raises:
            HTTPException: If tool not found or execution fails
        """
        try:
            if tool_name not in self.tools:
                available_tools = list(self.tools.keys())
                raise HTTPException(
                    status_code=400,
                    detail=f"Tool '{tool_name}' not found. Available tools: {available_tools}"
                )
            
            tool_function = self.tools[tool_name]
            result = await tool_function(**kwargs)
            
            return {
                "tool_name": tool_name,
                "execution_status": "success",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Tool execution failed: {str(e)}"
            )
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available tools.
        
        Returns:
            Dictionary with tool descriptions and capabilities
        """
        return {
            "document_search": {
                "name": "Historical Document Search",
                "description": "Search documents with historical terminology optimization",
                "parameters": ["query", "document_ids (optional)"],
                "use_cases": ["Find information about specific topics", "Research historical events", "Locate relevant passages"]
            },
            "timeline_builder": {
                "name": "Timeline Builder",
                "description": "Extract and organize chronological information",
                "parameters": ["document_ids (optional)"],
                "use_cases": ["Create chronological timelines", "Identify historical periods", "Track event sequences"]
            },
            "entity_extractor": {
                "name": "Entity Extractor",
                "description": "Identify historical people, places, and events",
                "parameters": ["document_ids (optional)"],
                "use_cases": ["Find key historical figures", "Identify important locations", "Extract major events"]
            },
            "cross_reference": {
                "name": "Cross-Reference Tool",
                "description": "Compare information across multiple documents",
                "parameters": ["topic", "document_ids (optional)"],
                "use_cases": ["Compare different accounts", "Find contradictions", "Verify information across sources"]
            },
            "citation_generator": {
                "name": "Citation Generator",
                "description": "Generate academic citations for sources",
                "parameters": ["search_results", "style (optional)"],
                "use_cases": ["Create bibliographies", "Format academic citations", "Ensure proper source attribution"]
            }
        }
    
    async def analyze_comprehensive(self, topic: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive historical analysis using multiple tools.
        
        Args:
            topic: Topic for comprehensive analysis
            document_ids: Optional list of document IDs to analyze
            
        Returns:
            Dictionary with results from multiple analysis tools
        """
        try:
            logger.info(f"Starting comprehensive analysis for topic: {topic}")
            
            # Execute multiple tools in parallel for efficiency
            tasks = [
                self.search_documents(topic, document_ids),
                self.extract_entities(document_ids),
                self.build_timeline(document_ids),
                self.cross_reference_documents(topic, document_ids)
            ]
            
            search_results, entities, timeline, cross_refs = await asyncio.gather(*tasks)
            
            # Generate citations for search results
            citations = await self.generate_citations(search_results.get("results", []))
            
            # Create comprehensive summary
            summary = await self._generate_comprehensive_summary(
                topic, search_results, entities, timeline, cross_refs, citations
            )
            
            return {
                "topic": topic,
                "analysis_type": "comprehensive",
                "document_search": search_results,
                "entities": entities,
                "timeline": timeline,
                "cross_references": cross_refs,
                "citations": citations,
                "comprehensive_summary": summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Comprehensive analysis failed: {str(e)}"
            )
    
    async def _generate_comprehensive_summary(self, topic: str, search_results: Dict[str, Any], 
                                            entities: Dict[str, Any], timeline: Dict[str, Any],
                                            cross_refs: Dict[str, Any], citations: Dict[str, Any]) -> str:
        """Generate a comprehensive summary of all analysis results."""
        try:
            # Extract key information
            search_count = search_results.get("total_results", 0)
            entity_count = entities.get("total_entities", 0)
            timeline_events = timeline.get("total_events", 0)
            cross_ref_count = len(cross_refs.get("cross_references", []))
            citation_count = citations.get("total_citations", 0)
            
            summary_parts = [
                f"Comprehensive Historical Analysis: {topic}",
                "=" * 50,
                "",
                f"📚 Document Search: Found {search_count} relevant passages",
                f"👥 Entity Extraction: Identified {entity_count} historical entities",
                f"📅 Timeline Analysis: Extracted {timeline_events} chronological events",
                f"🔗 Cross-References: Analyzed {cross_ref_count} document comparisons",
                f"📖 Citations: Generated {citation_count} academic citations",
                "",
                "Key Findings:",
            ]
            
            # Add key entities if available
            if entities.get("entities_by_type"):
                summary_parts.append("- Major Historical Figures:")
                people = entities["entities_by_type"].get("person", [])[:3]
                for person in people:
                    summary_parts.append(f"  • {person['name']} ({person['mentions']} mentions)")
            
            # Add timeline highlights
            if timeline.get("timeline_summary"):
                summary_parts.extend([
                    "",
                    "Timeline Highlights:",
                    timeline["timeline_summary"][:200] + "..."
                ])
            
            # Add cross-reference insights
            if cross_refs.get("analysis", {}).get("overall_consensus"):
                summary_parts.extend([
                    "",
                    "Source Analysis:",
                    f"- {cross_refs['analysis']['overall_consensus']}"
                ])
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive summary: {str(e)}")
            return f"Comprehensive analysis completed for '{topic}' using multiple historical analysis tools."


# Global toolkit instance
historical_toolkit = HistoricalAnalysisToolkit()