"""
Demo script for testing the ReAct agent system.

This script demonstrates the ReAct agent's capabilities including:
- Reasoning through complex queries
- Tool usage and execution
- Error handling and recovery
- Session management and monitoring
"""
import asyncio
import logging
import json
from datetime import datetime

from app.services.agent_service import agent_service
from app.services.react_agent import react_agent
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_agent_query():
    """Demo basic agent query processing."""
    print("\n" + "="*60)
    print("DEMO: Basic Agent Query Processing")
    print("="*60)
    
    query = "What can you tell me about Roman military organization based on the uploaded documents?"
    
    print(f"Query: {query}")
    print("\nProcessing with ReAct agent...")
    
    try:
        result = await agent_service.process_query(query)
        
        print(f"\nSession ID: {result['session_id']}")
        print(f"Success: {result['success']}")
        print(f"Reasoning Steps: {result['reasoning_steps']}")
        print(f"Tool Calls: {result['tool_calls']}")
        print(f"Duration: {result['session_duration']:.2f}s")
        
        if result['success']:
            print(f"\nAnswer: {result['answer'][:300]}...")
            
            print("\nDetailed Reasoning:")
            for step in result['detailed_reasoning']:
                print(f"  Step {step['step']}: {step['thought'][:100]}...")
                if step['action']:
                    print(f"    Action: {step['action'][:100]}...")
                if step['tools_used']:
                    print(f"    Tools: {', '.join(step['tools_used'])}")
        else:
            print(f"\nError: {result['error']}")
            
    except Exception as e:
        print(f"Demo failed: {str(e)}")


async def demo_streaming_agent_query():
    """Demo streaming agent query processing."""
    print("\n" + "="*60)
    print("DEMO: Streaming Agent Query Processing")
    print("="*60)
    
    query = "Compare Roman and Greek military tactics based on the available documents"
    
    print(f"Query: {query}")
    print("\nProcessing with streaming...")
    
    try:
        step_count = 0
        async for update in agent_service.process_query_streaming(query):
            update_type = update.get("type", "unknown")
            
            if update_type == "session_start":
                print(f"\n🚀 Session started: {update['session_id']}")
            
            elif update_type == "iteration_start":
                print(f"\n🔄 Iteration {update['iteration']}/{update['max_iterations']}")
            
            elif update_type == "step_start":
                step_count += 1
                print(f"\n💭 Step {update['step_number']}: Thinking...")
            
            elif update_type == "thinking":
                # Show thinking progress (truncated)
                content = update.get("content", "")
                if len(content) > 50:
                    print(".", end="", flush=True)
            
            elif update_type == "step_parsed":
                print(f"\n   Thought: {update['thought'][:100]}...")
                if update.get('action'):
                    print(f"   Action: {update['action'][:100]}...")
            
            elif update_type == "executing_tools":
                print(f"   🔧 Executing: {update['action']}")
            
            elif update_type == "tools_executed":
                tool_names = [tc['tool_name'] for tc in update.get('tool_calls', [])]
                print(f"   ✅ Tools completed: {', '.join(tool_names)}")
            
            elif update_type == "generating_final_answer":
                print(f"\n📝 Generating final answer...")
            
            elif update_type == "session_complete":
                session = update['session']
                print(f"\n✅ Session complete!")
                print(f"   Success: {update['success']}")
                print(f"   Tool calls: {session['total_tool_calls']}")
                if update['final_answer']:
                    print(f"   Answer: {update['final_answer'][:200]}...")
            
            elif update_type == "error":
                print(f"\n❌ Error: {update['error']}")
                break
        
        print(f"\nStreaming demo completed with {step_count} reasoning steps.")
        
    except Exception as e:
        print(f"Streaming demo failed: {str(e)}")


async def demo_tool_usage_analysis():
    """Demo analyzing tool usage patterns."""
    print("\n" + "="*60)
    print("DEMO: Tool Usage Analysis")
    print("="*60)
    
    # Test queries that should use different tools
    test_queries = [
        "Search for information about Roman legions",
        "Create a timeline of Roman military campaigns",
        "Extract historical entities from the documents",
        "Compare Roman and Greek military strategies"
    ]
    
    print("Testing different tool usage patterns...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query[:50]}... ---")
        
        try:
            result = await agent_service.process_query(query, session_id=f"test_{i}")
            
            print(f"Tools used: {result['tool_calls']}")
            
            # Analyze which tools were used
            tools_used = set()
            for step in result['detailed_reasoning']:
                tools_used.update(step['tools_used'])
            
            if tools_used:
                print(f"Specific tools: {', '.join(tools_used)}")
            else:
                print("No tools used (direct answer)")
                
        except Exception as e:
            print(f"Test {i} failed: {str(e)}")
    
    # Get monitoring stats
    print("\n--- Tool Usage Statistics ---")
    try:
        stats = await agent_service.get_monitoring_stats()
        tool_stats = stats['statistics'].get('tool_usage', {})
        
        if tool_stats:
            print("Tool usage counts:")
            for tool, count in sorted(tool_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {tool}: {count}")
        else:
            print("No tool usage statistics available yet.")
            
    except Exception as e:
        print(f"Failed to get tool statistics: {str(e)}")


async def demo_error_handling():
    """Demo error handling and recovery."""
    print("\n" + "="*60)
    print("DEMO: Error Handling and Recovery")
    print("="*60)
    
    # Test queries that might cause errors
    error_test_queries = [
        "",  # Empty query
        "x" * 3000,  # Very long query
        "What is the meaning of life?",  # Non-historical query
    ]
    
    print("Testing error handling...")
    
    for i, query in enumerate(error_test_queries, 1):
        query_display = query[:50] + "..." if len(query) > 50 else query
        query_display = query_display if query_display else "[empty query]"
        
        print(f"\n--- Error Test {i}: {query_display} ---")
        
        try:
            result = await agent_service.process_query(query, session_id=f"error_test_{i}")
            
            print(f"Success: {result['success']}")
            if not result['success']:
                print(f"Error handled: {result['error'][:100]}...")
            else:
                print("Query processed successfully (unexpected)")
                
        except Exception as e:
            print(f"Exception caught: {str(e)[:100]}...")
    
    # Check error statistics
    print("\n--- Error Statistics ---")
    try:
        stats = await agent_service.get_monitoring_stats()
        error_stats = stats['statistics'].get('errors', {})
        
        if error_stats:
            print("Error counts:")
            for error_type, count in error_stats.items():
                print(f"  {error_type}: {count}")
        else:
            print("No error statistics available.")
            
    except Exception as e:
        print(f"Failed to get error statistics: {str(e)}")


async def demo_session_management():
    """Demo session management capabilities."""
    print("\n" + "="*60)
    print("DEMO: Session Management")
    print("="*60)
    
    # Create multiple sessions
    print("Creating multiple sessions...")
    
    session_queries = [
        ("session_1", "Tell me about Roman military tactics"),
        ("session_2", "What were Greek phalanx formations?"),
        ("session_3", "Compare ancient siege warfare methods")
    ]
    
    created_sessions = []
    
    for session_id, query in session_queries:
        try:
            result = await agent_service.process_query(query, session_id=session_id)
            created_sessions.append(session_id)
            print(f"✅ Created session: {session_id}")
        except Exception as e:
            print(f"❌ Failed to create session {session_id}: {str(e)}")
    
    # List active sessions
    print(f"\n--- Active Sessions ---")
    try:
        sessions = await agent_service.list_active_sessions()
        print(f"Total active sessions: {len(sessions)}")
        
        for session in sessions:
            print(f"  {session['session_id']}: {session['query'][:50]}...")
            print(f"    Success: {session['success']}, Tools: {session['tool_calls']}")
            
    except Exception as e:
        print(f"Failed to list sessions: {str(e)}")
    
    # Get detailed session info
    if created_sessions:
        print(f"\n--- Session Details: {created_sessions[0]} ---")
        try:
            session_details = await agent_service.get_session(created_sessions[0])
            if session_details:
                print(f"Query: {session_details['query']}")
                print(f"Steps: {len(session_details['reasoning_steps'])}")
                print(f"Tool calls: {session_details['total_tool_calls']}")
                print(f"Duration: {session_details['session_start']} to {session_details.get('session_end', 'ongoing')}")
            else:
                print("Session not found")
        except Exception as e:
            print(f"Failed to get session details: {str(e)}")
    
    # Clean up sessions
    print(f"\n--- Cleaning Up Sessions ---")
    try:
        count = await agent_service.clear_all_sessions()
        print(f"Cleared {count} sessions")
    except Exception as e:
        print(f"Failed to clear sessions: {str(e)}")


async def demo_monitoring_and_health():
    """Demo monitoring and health check capabilities."""
    print("\n" + "="*60)
    print("DEMO: Monitoring and Health Checks")
    print("="*60)
    
    # Get current health status
    print("--- Health Status ---")
    try:
        stats = await agent_service.get_monitoring_stats()
        health = stats['health']
        
        print(f"Status: {health['status']}")
        print(f"Success Rate: {health['success_rate']:.2%}")
        print(f"Total Sessions: {health['total_sessions']}")
        print(f"Recent Errors: {health['recent_errors']}")
        print(f"Avg Response Time: {health['average_response_time']:.2f}s")
        
    except Exception as e:
        print(f"Failed to get health status: {str(e)}")
    
    # Get performance statistics
    print("\n--- Performance Statistics ---")
    try:
        stats = await agent_service.get_monitoring_stats()
        perf_stats = stats['statistics']['performance']
        
        print(f"Total Sessions: {perf_stats['total_sessions']}")
        print(f"Successful: {perf_stats['successful_sessions']}")
        print(f"Failed: {perf_stats['failed_sessions']}")
        print(f"Avg Tool Calls/Session: {perf_stats['average_tool_calls_per_session']:.1f}")
        print(f"Total Tool Calls: {perf_stats['total_tool_calls']}")
        
    except Exception as e:
        print(f"Failed to get performance statistics: {str(e)}")
    
    # Get agent configuration
    print("\n--- Agent Configuration ---")
    try:
        stats = await agent_service.get_monitoring_stats()
        config = stats['agent_config']
        
        print(f"Model: {config.get('model', 'unknown')}")
        print(f"Max Iterations: {config.get('max_iterations', 'unknown')}")
        print(f"Temperature: {config.get('temperature', 'unknown')}")
        print(f"Available Tools: {len(config.get('available_tools', []))}")
        
        if config.get('available_tools'):
            print("Tools:")
            for tool in config['available_tools']:
                print(f"  - {tool}")
                
    except Exception as e:
        print(f"Failed to get agent configuration: {str(e)}")


async def main():
    """Run all ReAct agent demos."""
    print("ReAct Agent System Demo")
    print("=" * 60)
    print(f"Model: {settings.GEMINI_MODEL}")
    print(f"API Key configured: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    if not settings.GEMINI_API_KEY:
        print("\n❌ GEMINI_API_KEY not configured. Please set it in your .env file.")
        return
    
    # Run demos in sequence
    demos = [
        demo_basic_agent_query,
        demo_streaming_agent_query,
        demo_tool_usage_analysis,
        demo_error_handling,
        demo_session_management,
        demo_monitoring_and_health
    ]
    
    for demo_func in demos:
        try:
            await demo_func()
            await asyncio.sleep(1)  # Brief pause between demos
        except Exception as e:
            print(f"\n❌ Demo {demo_func.__name__} failed: {str(e)}")
            continue
    
    print("\n" + "="*60)
    print("All ReAct Agent demos completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())