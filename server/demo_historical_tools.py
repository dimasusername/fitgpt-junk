#!/usr/bin/env python3
"""
Demo script for historical document analysis tools.

This script demonstrates the capabilities of the historical analysis toolkit
including document search, timeline building, entity extraction, cross-referencing,
and citation generation.
"""
import asyncio
import logging
from typing import Dict, Any

from app.services.historical_tools import historical_toolkit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_available_tools():
    """Demonstrate getting available tools information."""
    print("=" * 60)
    print("HISTORICAL ANALYSIS TOOLS DEMO")
    print("=" * 60)
    print()
    
    print("Available Tools:")
    print("-" * 20)
    
    tools = historical_toolkit.get_available_tools()
    
    for tool_name, tool_info in tools.items():
        print(f"\n🔧 {tool_info['name']}")
        print(f"   Description: {tool_info['description']}")
        print(f"   Parameters: {', '.join(tool_info['parameters'])}")
        print(f"   Use Cases:")
        for use_case in tool_info['use_cases']:
            print(f"     • {use_case}")
    
    print(f"\nTotal Tools Available: {len(tools)}")
    print()


async def demo_document_search():
    """Demonstrate historical document search capabilities."""
    print("=" * 60)
    print("DOCUMENT SEARCH DEMO")
    print("=" * 60)
    print()
    
    # Note: This would normally search actual documents, but for demo purposes
    # we'll show what the search would look like
    
    queries = [
        "Roman legion military structure",
        "Battle of Cannae Hannibal tactics",
        "Greek phalanx formation hoplites",
        "Caesar Gallic Wars conquest"
    ]
    
    print("Sample Historical Queries:")
    print("-" * 30)
    
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
        print(f"   → Enhanced query would include: historical terminology expansion")
        print(f"   → Search strategy: historical_terminology_optimized")
        print(f"   → Expected results: Relevant passages with historical context")
        print()
    
    print("Search Features:")
    print("• Historical terminology optimization")
    print("• Context-aware relevance scoring")
    print("• Source attribution with page numbers")
    print("• Entity extraction from results")
    print()


async def demo_timeline_builder():
    """Demonstrate timeline building capabilities."""
    print("=" * 60)
    print("TIMELINE BUILDER DEMO")
    print("=" * 60)
    print()
    
    print("Timeline Extraction Capabilities:")
    print("-" * 35)
    
    sample_dates = [
        ("264 BC", "First Punic War begins", "exact"),
        ("218 BC", "Hannibal crosses the Alps", "exact"),
        ("216 BC", "Battle of Cannae", "exact"),
        ("146 BC", "Destruction of Carthage", "exact"),
        ("49 BC", "Caesar crosses the Rubicon", "exact"),
        ("44 BC", "Assassination of Julius Caesar", "exact")
    ]
    
    print("Sample Timeline Events:")
    for date, event, confidence in sample_dates:
        period = "Roman Republic (509-27 BC)" if "BC" in date and int(date.split()[0]) > 27 else "Roman Empire"
        print(f"📅 {date}: {event}")
        print(f"   Period: {period}")
        print(f"   Confidence: {confidence}")
        print()
    
    print("Timeline Features:")
    print("• Automatic date extraction and parsing")
    print("• Historical period classification")
    print("• Chronological sorting and organization")
    print("• Context extraction around dates")
    print("• AI-enhanced event identification")
    print()


async def demo_entity_extraction():
    """Demonstrate entity extraction capabilities."""
    print("=" * 60)
    print("ENTITY EXTRACTION DEMO")
    print("=" * 60)
    print()
    
    print("Historical Entity Categories:")
    print("-" * 30)
    
    sample_entities = {
        "person": [
            ("Julius Caesar", "Roman general and statesman", 15),
            ("Hannibal Barca", "Carthaginian military commander", 12),
            ("Marcus Aurelius", "Roman Emperor and philosopher", 8),
            ("Alexander the Great", "Macedonian king and conqueror", 10)
        ],
        "place": [
            ("Rome", "Capital of Roman Empire", 25),
            ("Carthage", "Ancient city in North Africa", 18),
            ("Thermopylae", "Mountain pass in Greece", 6),
            ("Rubicon River", "River in northern Italy", 4)
        ],
        "battle": [
            ("Battle of Cannae", "Major battle of Second Punic War", 8),
            ("Battle of Pharsalus", "Decisive battle of Caesar's Civil War", 5),
            ("Siege of Alesia", "Final battle of Gallic Wars", 6),
            ("Battle of Actium", "Naval battle ending Roman Republic", 4)
        ],
        "organization": [
            ("Roman Legion", "Primary military unit of Rome", 20),
            ("Roman Senate", "Governing body of Roman Republic", 15),
            ("Praetorian Guard", "Elite Roman military unit", 7),
            ("Gallic Tribes", "Celtic peoples of ancient Gaul", 9)
        ]
    }
    
    for entity_type, entities in sample_entities.items():
        print(f"\n👥 {entity_type.title()}s:")
        for name, description, mentions in entities:
            print(f"   • {name} - {description} ({mentions} mentions)")
    
    print(f"\nTotal Sample Entities: {sum(len(entities) for entities in sample_entities.values())}")
    
    print("\nEntity Extraction Features:")
    print("• Pattern-based recognition for historical names")
    print("• AI-enhanced entity identification")
    print("• Relationship mapping between entities")
    print("• Mention frequency tracking")
    print("• Context preservation for each entity")
    print()


async def demo_cross_reference():
    """Demonstrate cross-reference analysis capabilities."""
    print("=" * 60)
    print("CROSS-REFERENCE ANALYSIS DEMO")
    print("=" * 60)
    print()
    
    print("Sample Cross-Reference Analysis:")
    print("-" * 35)
    
    sample_topic = "Roman Military Tactics"
    
    print(f"Topic: {sample_topic}")
    print()
    
    sample_comparisons = [
        {
            "doc1": "Caesar's Commentaries on the Gallic Wars",
            "doc2": "Polybius - The Histories",
            "similarity": 0.78,
            "agreements": [
                "Both describe Roman legion organization",
                "Similar accounts of siege warfare techniques",
                "Consistent description of Roman discipline"
            ],
            "contradictions": [
                "Different casualty numbers for Battle of Alesia",
                "Varying accounts of Gallic resistance strength"
            ]
        },
        {
            "doc1": "Livy - Ab Urbe Condita",
            "doc2": "Tacitus - Annals",
            "similarity": 0.65,
            "agreements": [
                "Both emphasize Roman military superiority",
                "Similar descriptions of Germanic tribes"
            ],
            "contradictions": [
                "Different perspectives on Roman expansion ethics",
                "Varying emphasis on individual vs. collective heroism"
            ]
        }
    ]
    
    for i, comparison in enumerate(sample_comparisons, 1):
        print(f"Comparison {i}:")
        print(f"  📚 Document 1: {comparison['doc1']}")
        print(f"  📚 Document 2: {comparison['doc2']}")
        print(f"  🎯 Similarity Score: {comparison['similarity']:.2f}")
        print()
        
        print("  ✅ Agreements:")
        for agreement in comparison['agreements']:
            print(f"    • {agreement}")
        print()
        
        print("  ⚠️  Contradictions:")
        for contradiction in comparison['contradictions']:
            print(f"    • {contradiction}")
        print()
    
    print("Cross-Reference Features:")
    print("• Semantic similarity analysis between documents")
    print("• Automatic identification of agreements and contradictions")
    print("• Common entity detection across sources")
    print("• Evidence strength assessment")
    print("• Comprehensive source comparison")
    print()


async def demo_citation_generation():
    """Demonstrate citation generation capabilities."""
    print("=" * 60)
    print("CITATION GENERATION DEMO")
    print("=" * 60)
    print()
    
    print("Citation Styles Supported:")
    print("-" * 30)
    
    sample_source = {
        "document_name": "Caesar's Commentaries on the Gallic Wars",
        "page_number": 45,
        "content": "The legion was organized into ten cohorts, each containing six centuries of eighty men.",
        "context": "Military organization"
    }
    
    citation_styles = {
        "academic": f"[{sample_source['document_name']}, p. {sample_source['page_number']}]",
        "chicago": f"{sample_source['document_name']}, {sample_source['page_number']}.",
        "mla": f"({sample_source['document_name']} {sample_source['page_number']})",
        "apa": f"({sample_source['document_name']}, p. {sample_source['page_number']})"
    }
    
    for style, citation in citation_styles.items():
        print(f"\n📖 {style.upper()} Style:")
        print(f"   Citation: {citation}")
        print(f"   Quote: \"{sample_source['content'][:60]}...\"")
    
    print(f"\nBibliography Entry:")
    print(f"   {sample_source['document_name']} - Historical Document")
    
    print("\nCitation Features:")
    print("• Multiple academic citation styles")
    print("• Automatic bibliography generation")
    print("• Page number and source tracking")
    print("• Quote preservation with context")
    print("• Proper academic formatting")
    print()


async def demo_comprehensive_analysis():
    """Demonstrate comprehensive analysis workflow."""
    print("=" * 60)
    print("COMPREHENSIVE ANALYSIS DEMO")
    print("=" * 60)
    print()
    
    topic = "Roman Civil Wars"
    
    print(f"Comprehensive Analysis Topic: {topic}")
    print("-" * 40)
    print()
    
    analysis_steps = [
        ("🔍 Document Search", "Finding relevant passages about Roman Civil Wars"),
        ("👥 Entity Extraction", "Identifying key figures: Caesar, Pompey, Crassus, etc."),
        ("📅 Timeline Building", "Organizing events from 133 BC to 30 BC"),
        ("🔗 Cross-Reference", "Comparing accounts from different historians"),
        ("📖 Citation Generation", "Creating proper academic citations")
    ]
    
    print("Analysis Workflow:")
    for step, description in analysis_steps:
        print(f"{step}: {description}")
    
    print()
    print("Expected Comprehensive Results:")
    print("• 15-20 relevant document passages")
    print("• 25+ historical entities (people, places, battles)")
    print("• 10-15 chronological events with dates")
    print("• 3-5 cross-document comparisons")
    print("• Complete bibliography with 5+ sources")
    print("• Synthesized summary of findings")
    print()
    
    print("Use Cases for Comprehensive Analysis:")
    print("• Academic research projects")
    print("• Historical fact-checking")
    print("• Comparative historical studies")
    print("• Timeline reconstruction")
    print("• Source verification and validation")
    print()


async def main():
    """Run the complete historical tools demonstration."""
    try:
        print("🏛️  HISTORICAL DOCUMENT ANALYSIS TOOLKIT DEMO")
        print("=" * 80)
        print()
        
        # Run all demonstrations
        await demo_available_tools()
        await demo_document_search()
        await demo_timeline_builder()
        await demo_entity_extraction()
        await demo_cross_reference()
        await demo_citation_generation()
        await demo_comprehensive_analysis()
        
        print("=" * 80)
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        print()
        print("The Historical Analysis Toolkit provides:")
        print("• 5 specialized tools for historical document analysis")
        print("• Optimized for ancient history and classical civilizations")
        print("• Academic-grade citation and source attribution")
        print("• AI-enhanced entity recognition and timeline extraction")
        print("• Cross-document comparison and verification")
        print()
        print("Ready for integration with ReAct agents and multi-agent workflows!")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())