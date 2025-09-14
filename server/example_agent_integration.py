"""
Example of how to integrate historical tool functions with an agent SDK.

This demonstrates the function-based approach for agent tool integration,
replacing the previous REST API endpoints.
"""
import asyncio
from typing import Dict, Any, List

from app.services.historical_tool_functions import (
    search_documents,
    build_timeline,
    extract_entities,
    cross_reference_documents,
    generate_citations,
    get_tool_function,
    get_tool_schema,
    list_available_tools,
    HISTORICAL_TOOL_FUNCTIONS
)


async def example_agent_workflow():
    """
    Example workflow showing how an agent would use the historical tool functions.
    """
    print("=== Historical Analysis Agent Workflow Example ===\n")
    
    # 1. List available tools
    print("1. Available Tools:")
    tools = list_available_tools()
    for tool_name, tool_info in tools.items():
        print(f"   - {tool_name}: {tool_info['description']}")
    print()
    
    # 2. Search for documents about Roman military
    print("2. Searching for Roman military information...")
    search_result = await search_documents(
        query="Roman legion military organization",
        document_ids=None  # Search all documents
    )
    print(f"   Found {search_result['total_results']} results")
    print(f"   Search strategy: {search_result['search_strategy']}")
    if search_result.get('error'):
        print(f"   Error: {search_result['error']}")
    print()
    
    # 3. Extract timeline from documents
    print("3. Building timeline from documents...")
    timeline_result = await build_timeline(document_ids=None)
    print(f"   Found {timeline_result['total_events']} timeline events")
    if timeline_result.get('error'):
        print(f"   Error: {timeline_result['error']}")
    print()
    
    # 4. Extract entities
    print("4. Extracting historical entities...")
    entities_result = await extract_entities(document_ids=None)
    print(f"   Found {entities_result['total_entities']} entities")
    if entities_result.get('error'):
        print(f"   Error: {entities_result['error']}")
    print()
    
    # 5. Cross-reference information
    print("5. Cross-referencing Roman military information...")
    cross_ref_result = await cross_reference_documents(
        topic="Roman military tactics",
        document_ids=None
    )
    print(f"   Analyzed {cross_ref_result['documents_analyzed']} documents")
    if cross_ref_result.get('error'):
        print(f"   Error: {cross_ref_result['error']}")
    print()
    
    # 6. Generate citations
    print("6. Generating citations...")
    if search_result['results']:
        citations_result = await generate_citations(
            search_results=search_result['results'][:3],  # First 3 results
            style="academic"
        )
        print(f"   Generated {citations_result['total_citations']} citations")
        if citations_result.get('error'):
            print(f"   Error: {citations_result['error']}")
    else:
        print("   No search results to cite")
    print()


async def example_dynamic_tool_calling():
    """
    Example of dynamic tool calling using the tool registry.
    """
    print("=== Dynamic Tool Calling Example ===\n")
    
    # Simulate agent deciding which tool to use
    tool_name = "search_documents"
    
    # Get tool function dynamically
    tool_function = get_tool_function(tool_name)
    if not tool_function:
        print(f"Tool '{tool_name}' not found")
        return
    
    # Get tool schema for validation
    tool_schema = get_tool_schema(tool_name)
    print(f"Tool: {tool_name}")
    print(f"Description: {tool_schema['description']}")
    print(f"Parameters: {tool_schema['parameters']}")
    print()
    
    # Call the tool function
    result = await tool_function("Roman empire expansion")
    print(f"Result: Found {result.get('total_results', 0)} results")
    if result.get('error'):
        print(f"Error: {result['error']}")
    print()


def example_tool_registration_for_agent_sdk():
    """
    Example of how to register tools with an agent SDK.
    """
    print("=== Agent SDK Tool Registration Example ===\n")
    
    # This is how you would register tools with an agent SDK
    registered_tools = {}
    
    for tool_name, tool_info in HISTORICAL_TOOL_FUNCTIONS.items():
        registered_tools[tool_name] = {
            "function": tool_info["function"],
            "description": tool_info["description"],
            "parameters": tool_info["parameters"],
            "input_schema": tool_info["input_schema"].schema(),
            "output_schema": tool_info["output_schema"].schema()
        }
    
    print("Tools registered with agent SDK:")
    for tool_name, tool_data in registered_tools.items():
        print(f"   - {tool_name}")
        print(f"     Description: {tool_data['description']}")
        print(f"     Parameters: {tool_data['parameters']}")
        print(f"     Input schema keys: {list(tool_data['input_schema']['properties'].keys())}")
        print(f"     Output schema keys: {list(tool_data['output_schema']['properties'].keys())}")
        print()
    
    return registered_tools


async def example_error_handling():
    """
    Example of error handling in tool functions.
    """
    print("=== Error Handling Example ===\n")
    
    # Test with invalid input
    print("Testing with empty query...")
    result = await search_documents("")
    if result.get('error'):
        print(f"   Handled error gracefully: {result['error']}")
    else:
        print("   No error occurred")
    print()
    
    # Test with invalid topic
    print("Testing cross-reference with empty topic...")
    result = await cross_reference_documents("")
    if result.get('error'):
        print(f"   Handled error gracefully: {result['error']}")
    else:
        print("   No error occurred")
    print()


async def main():
    """
    Main function to run all examples.
    """
    print("Historical Tool Functions - Agent Integration Examples")
    print("=" * 60)
    print()
    
    # Run examples
    await example_agent_workflow()
    await example_dynamic_tool_calling()
    example_tool_registration_for_agent_sdk()
    await example_error_handling()
    
    print("Examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())