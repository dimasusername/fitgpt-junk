"""
ReAct (Reasoning and Acting) agent system with Gemini integration.

This module implements a ReAct agent that can reason about problems and use tools
to solve them. The agent follows the Think -> Act -> Observe -> Repeat pattern
with automatic tool calling through the Google AI SDK.
"""
import asyncio
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from app.core.config import settings
from app.services.historical_tool_functions import (
    search_documents,
    build_timeline,
    extract_entities,
    cross_reference_documents,
    generate_citations,
    HISTORICAL_TOOL_FUNCTIONS
)

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent execution states."""
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ToolCall:
    """Represents a tool call made by the agent."""
    tool_name: str
    arguments: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    success: bool = False


@dataclass
class ReasoningStep:
    """Represents a reasoning step in the ReAct process."""
    step_number: int
    state: AgentState
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: List[ToolCall] = field(default_factory=list)


@dataclass
class AgentSession:
    """Represents an agent session with conversation history."""
    session_id: str
    query: str
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    total_tool_calls: int = 0
    session_start: datetime = field(default_factory=datetime.now)
    session_end: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None


class ReActAgent:
    """
    ReAct agent that can reason about problems and use tools to solve them.
    
    The agent follows the Think -> Act -> Observe -> Repeat pattern:
    1. Think: Analyze the problem and decide what to do
    2. Act: Execute a tool or provide a final answer
    3. Observe: Process the results and update understanding
    4. Repeat: Continue until the problem is solved or max iterations reached
    """
    
    def __init__(self, max_iterations: int = 5, temperature: float = 0.3):
        """
        Initialize the ReAct agent.
        
        Args:
            max_iterations: Maximum number of reasoning iterations
            temperature: Temperature for LLM generation (0.0 to 1.0)
        """
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.available_tools = HISTORICAL_TOOL_FUNCTIONS
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini model with proper configuration."""
        try:
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured")
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Configure the model for ReAct reasoning
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
                response_mime_type="text/plain"
            )
            
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config=generation_config
            )
            
            logger.info(f"ReAct agent initialized with model: {settings.GEMINI_MODEL}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise
    
    async def process_query(self, query: str, session_id: Optional[str] = None) -> AgentSession:
        """
        Process a query using the ReAct reasoning pattern.
        
        Args:
            query: The user's query to process
            session_id: Optional session ID for tracking
            
        Returns:
            AgentSession with complete reasoning trace
        """
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = AgentSession(session_id=session_id, query=query)
        
        try:
            logger.info(f"Starting ReAct processing for query: {query[:100]}...")
            
            # Build the initial system prompt
            system_prompt = self._build_system_prompt()
            
            # Start the reasoning loop
            conversation_history = [system_prompt, f"User Query: {query}"]
            
            for iteration in range(self.max_iterations):
                logger.info(f"ReAct iteration {iteration + 1}/{self.max_iterations}")
                
                # Generate reasoning step
                step = await self._generate_reasoning_step(
                    conversation_history, iteration + 1, session
                )
                
                session.reasoning_steps.append(step)
                
                # Update conversation history
                conversation_history.append(f"Step {step.step_number}:")
                conversation_history.append(f"Thought: {step.thought}")
                
                if step.action:
                    conversation_history.append(f"Action: {step.action}")
                
                if step.observation:
                    conversation_history.append(f"Observation: {step.observation}")
                
                # Check if we have a final answer
                if step.state == AgentState.COMPLETED:
                    session.final_answer = step.observation
                    session.success = True
                    break
                
                # Check for errors
                if step.state == AgentState.ERROR:
                    session.error = step.observation
                    break
            
            # If we didn't get a final answer, generate one
            if not session.final_answer and not session.error:
                final_step = await self._generate_final_answer(conversation_history, session)
                session.reasoning_steps.append(final_step)
                session.final_answer = final_step.observation
                session.success = True
            
            session.session_end = datetime.now()
            session.total_tool_calls = sum(len(step.tool_calls) for step in session.reasoning_steps)
            
            logger.info(f"ReAct processing completed. Success: {session.success}")
            
            return session
            
        except Exception as e:
            logger.error(f"ReAct processing failed: {str(e)}")
            session.error = str(e)
            session.session_end = datetime.now()
            return session
    
    async def process_query_streaming(self, query: str, session_id: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a query with streaming updates for real-time feedback.
        
        Args:
            query: The user's query to process
            session_id: Optional session ID for tracking
            
        Yields:
            Dictionary updates with reasoning steps and progress
        """
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = AgentSession(session_id=session_id, query=query)
        
        try:
            # Yield initial status
            yield {
                "type": "session_start",
                "session_id": session_id,
                "query": query,
                "timestamp": session.session_start.isoformat()
            }
            
            # Build the initial system prompt
            system_prompt = self._build_system_prompt()
            conversation_history = [system_prompt, f"User Query: {query}"]
            
            for iteration in range(self.max_iterations):
                # Yield iteration start
                yield {
                    "type": "iteration_start",
                    "iteration": iteration + 1,
                    "max_iterations": self.max_iterations
                }
                
                # Generate reasoning step with streaming
                async for update in self._generate_reasoning_step_streaming(
                    conversation_history, iteration + 1, session
                ):
                    yield update
                
                # Get the completed step
                step = session.reasoning_steps[-1] if session.reasoning_steps else None
                if not step:
                    break
                
                # Update conversation history
                conversation_history.append(f"Step {step.step_number}:")
                conversation_history.append(f"Thought: {step.thought}")
                
                if step.action:
                    conversation_history.append(f"Action: {step.action}")
                
                if step.observation:
                    conversation_history.append(f"Observation: {step.observation}")
                
                # Check completion conditions
                if step.state == AgentState.COMPLETED:
                    session.final_answer = step.observation
                    session.success = True
                    break
                
                if step.state == AgentState.ERROR:
                    session.error = step.observation
                    break
            
            # Generate final answer if needed
            if not session.final_answer and not session.error:
                yield {"type": "generating_final_answer"}
                final_step = await self._generate_final_answer(conversation_history, session)
                session.reasoning_steps.append(final_step)
                session.final_answer = final_step.observation
                session.success = True
            
            # Yield final results
            session.session_end = datetime.now()
            session.total_tool_calls = sum(len(step.tool_calls) for step in session.reasoning_steps)
            
            yield {
                "type": "session_complete",
                "session": self._session_to_dict(session),
                "success": session.success,
                "final_answer": session.final_answer,
                "error": session.error
            }
            
        except Exception as e:
            logger.error(f"Streaming ReAct processing failed: {str(e)}")
            yield {
                "type": "session_error",
                "error": str(e),
                "session_id": session_id
            }
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the ReAct agent."""
        tool_descriptions = []
        for tool_name, tool_info in self.available_tools.items():
            tool_descriptions.append(
                f"- {tool_name}: {tool_info['description']}\n"
                f"  Parameters: {', '.join(tool_info['parameters'])}"
            )
        
        tools_text = "\n".join(tool_descriptions)
        
        return f"""You are a ReAct (Reasoning and Acting) agent specialized in historical document analysis. 
You can reason about problems and use tools to solve them.

Available Tools:
{tools_text}

ReAct Pattern:
1. Thought: Analyze the problem and decide what to do next
2. Action: Either use a tool or provide a final answer
3. Observation: Process the results and update your understanding
4. Repeat until you have a complete answer

Tool Usage Format:
Action: tool_name(parameter1="value1", parameter2="value2")

Final Answer Format:
Action: Final Answer
Observation: [Your complete answer here]

Guidelines:
- Always think step by step
- Use tools when you need specific information
- Provide detailed observations about tool results
- Give comprehensive final answers with proper citations
- If a tool fails, try alternative approaches
- Focus on historical accuracy and scholarly analysis

Begin your reasoning with "Thought:" and continue with the ReAct pattern."""
    
    async def _generate_reasoning_step(
        self, 
        conversation_history: List[str], 
        step_number: int, 
        session: AgentSession
    ) -> ReasoningStep:
        """Generate a single reasoning step."""
        try:
            # Create the prompt for this step
            prompt = "\n".join(conversation_history) + f"\n\nStep {step_number}:\nThought:"
            
            # Generate response from Gemini
            response = await self._generate_with_retry(prompt)
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini")
            
            # Parse the response
            step = self._parse_reasoning_response(response.text, step_number)
            
            # Execute any tool calls
            if step.action and not step.action.startswith("Final Answer"):
                await self._execute_tool_calls(step, session)
            
            return step
            
        except Exception as e:
            logger.error(f"Failed to generate reasoning step: {str(e)}")
            return ReasoningStep(
                step_number=step_number,
                state=AgentState.ERROR,
                thought=f"Error generating reasoning step: {str(e)}",
                observation=f"Failed to process step {step_number}: {str(e)}"
            )
    
    async def _generate_reasoning_step_streaming(
        self, 
        conversation_history: List[str], 
        step_number: int, 
        session: AgentSession
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a reasoning step with streaming updates."""
        try:
            # Yield step start
            yield {
                "type": "step_start",
                "step_number": step_number,
                "state": "thinking"
            }
            
            # Create the prompt
            prompt = "\n".join(conversation_history) + f"\n\nStep {step_number}:\nThought:"
            
            # Generate response with streaming
            response_text = ""
            async for chunk in self._generate_streaming(prompt):
                response_text += chunk
                yield {
                    "type": "thinking",
                    "step_number": step_number,
                    "content": chunk,
                    "full_content": response_text
                }
            
            # Parse the complete response
            step = self._parse_reasoning_response(response_text, step_number)
            
            # Yield parsed step
            yield {
                "type": "step_parsed",
                "step_number": step_number,
                "thought": step.thought,
                "action": step.action,
                "state": step.state.value
            }
            
            # Execute tool calls if needed
            if step.action and not step.action.startswith("Final Answer"):
                yield {
                    "type": "executing_tools",
                    "step_number": step_number,
                    "action": step.action
                }
                
                await self._execute_tool_calls(step, session)
                
                yield {
                    "type": "tools_executed",
                    "step_number": step_number,
                    "tool_calls": [self._tool_call_to_dict(tc) for tc in step.tool_calls],
                    "observation": step.observation
                }
            
            # Add step to session
            session.reasoning_steps.append(step)
            
            yield {
                "type": "step_complete",
                "step_number": step_number,
                "step": self._reasoning_step_to_dict(step)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate streaming reasoning step: {str(e)}")
            error_step = ReasoningStep(
                step_number=step_number,
                state=AgentState.ERROR,
                thought=f"Error generating reasoning step: {str(e)}",
                observation=f"Failed to process step {step_number}: {str(e)}"
            )
            session.reasoning_steps.append(error_step)
            
            yield {
                "type": "step_error",
                "step_number": step_number,
                "error": str(e)
            }
    
    async def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> GenerateContentResponse:
        """Generate content with retry logic."""
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return response
            except Exception as e:
                logger.warning(f"Generation attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
    
    async def _generate_streaming(self, prompt: str) -> AsyncGenerator[str, None]:
        """Generate content with streaming."""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content, prompt, stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Streaming generation failed: {str(e)}")
            yield f"[Error: {str(e)}]"
    
    def _parse_reasoning_response(self, response_text: str, step_number: int) -> ReasoningStep:
        """Parse the agent's reasoning response."""
        try:
            # Initialize step
            step = ReasoningStep(step_number=step_number, state=AgentState.THINKING, thought="")
            
            # Extract thought
            thought_match = re.search(r'Thought:\s*(.*?)(?=Action:|$)', response_text, re.DOTALL | re.IGNORECASE)
            if thought_match:
                step.thought = thought_match.group(1).strip()
            else:
                step.thought = response_text.strip()
            
            # Extract action
            action_match = re.search(r'Action:\s*(.*?)(?=Observation:|$)', response_text, re.DOTALL | re.IGNORECASE)
            if action_match:
                step.action = action_match.group(1).strip()
                step.state = AgentState.ACTING
                
                # Check if it's a final answer
                if step.action.startswith("Final Answer"):
                    step.state = AgentState.COMPLETED
                    # Extract the final answer content
                    final_answer_match = re.search(r'Final Answer\s*:?\s*(.*)', step.action, re.DOTALL | re.IGNORECASE)
                    if final_answer_match:
                        step.observation = final_answer_match.group(1).strip()
                    else:
                        step.observation = "Final answer provided."
            
            # Extract observation (if already present)
            obs_match = re.search(r'Observation:\s*(.*?)$', response_text, re.DOTALL | re.IGNORECASE)
            if obs_match and not step.observation:
                step.observation = obs_match.group(1).strip()
                if step.state != AgentState.COMPLETED:  # Don't override COMPLETED state
                    step.state = AgentState.OBSERVING
            
            return step
            
        except Exception as e:
            logger.error(f"Failed to parse reasoning response: {str(e)}")
            return ReasoningStep(
                step_number=step_number,
                state=AgentState.ERROR,
                thought=f"Failed to parse response: {str(e)}",
                observation=f"Parsing error: {str(e)}"
            )
    
    async def _execute_tool_calls(self, step: ReasoningStep, session: AgentSession):
        """Execute tool calls from the action."""
        try:
            if not step.action:
                return
            
            # Parse tool calls from action
            tool_calls = self._parse_tool_calls(step.action)
            
            if not tool_calls:
                step.observation = f"No valid tool calls found in action: {step.action}"
                step.state = AgentState.OBSERVING
                return
            
            # Execute each tool call
            observations = []
            for tool_call in tool_calls:
                start_time = datetime.now()
                
                try:
                    # Get the tool function
                    tool_info = self.available_tools.get(tool_call.tool_name)
                    if not tool_info:
                        tool_call.error = f"Unknown tool: {tool_call.tool_name}"
                        tool_call.success = False
                        observations.append(f"Error: Unknown tool '{tool_call.tool_name}'")
                        continue
                    
                    # Execute the tool
                    tool_function = tool_info["function"]
                    result = await tool_function(**tool_call.arguments)
                    
                    # Record results
                    execution_time = (datetime.now() - start_time).total_seconds()
                    tool_call.execution_time = execution_time
                    tool_call.result = result
                    
                    # Check if tool returned an error
                    if result.get('error'):
                        tool_call.error = result['error']
                        tool_call.success = False
                        error_msg = f"Tool {tool_call.tool_name} failed: {result['error']}"
                        observations.append(error_msg)
                    else:
                        tool_call.success = True
                        # Format observation
                        observation = self._format_tool_result(tool_call.tool_name, result)
                        observations.append(observation)
                    
                    logger.info(f"Tool {tool_call.tool_name} executed successfully in {execution_time:.2f}s")
                    
                except Exception as e:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    tool_call.execution_time = execution_time
                    tool_call.error = str(e)
                    tool_call.success = False
                    
                    error_msg = f"Tool {tool_call.tool_name} failed: {str(e)}"
                    observations.append(error_msg)
                    logger.error(error_msg)
                
                step.tool_calls.append(tool_call)
            
            # Combine observations
            step.observation = "\n".join(observations)
            step.state = AgentState.OBSERVING
            
        except Exception as e:
            logger.error(f"Failed to execute tool calls: {str(e)}")
            step.observation = f"Tool execution failed: {str(e)}"
            step.state = AgentState.ERROR
    
    def _parse_tool_calls(self, action: str) -> List[ToolCall]:
        """Parse tool calls from action text."""
        tool_calls = []
        
        try:
            # Pattern to match tool calls: tool_name(param1="value1", param2="value2")
            pattern = r'(\w+)\s*\(\s*(.*?)\s*\)'
            matches = re.findall(pattern, action)
            
            for tool_name, params_str in matches:
                if tool_name not in self.available_tools:
                    continue
                
                # Parse parameters
                arguments = {}
                if params_str.strip():
                    # Simple parameter parsing (handles quoted strings and basic types)
                    param_pattern = r'(\w+)\s*=\s*(["\'])(.*?)\2|(\w+)\s*=\s*(\w+)'
                    param_matches = re.findall(param_pattern, params_str)
                    
                    for match in param_matches:
                        if match[0] and match[2]:  # Quoted string
                            arguments[match[0]] = match[2]
                        elif match[3] and match[4]:  # Unquoted value
                            value = match[4]
                            # Try to convert to appropriate type
                            if value.lower() == 'true':
                                arguments[match[3]] = True
                            elif value.lower() == 'false':
                                arguments[match[3]] = False
                            elif value.lower() == 'none':
                                arguments[match[3]] = None
                            elif value.isdigit():
                                arguments[match[3]] = int(value)
                            else:
                                arguments[match[3]] = value
                
                tool_call = ToolCall(tool_name=tool_name, arguments=arguments)
                tool_calls.append(tool_call)
            
        except Exception as e:
            logger.error(f"Failed to parse tool calls: {str(e)}")
        
        return tool_calls
    
    def _format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format tool result for observation."""
        try:
            if result.get('error'):
                return f"{tool_name} failed: {result['error']}"
            
            # Format based on tool type
            if tool_name == "search_documents":
                total = result.get('total_results', 0)
                if total > 0:
                    results = result.get('results', [])[:3]  # Show top 3
                    formatted_results = []
                    for r in results:
                        source = r.get('document_name', 'Unknown')
                        page = r.get('page_number', 'N/A')
                        content = r.get('content', '')[:200] + "..." if len(r.get('content', '')) > 200 else r.get('content', '')
                        formatted_results.append(f"- {source} (p.{page}): {content}")
                    return f"Found {total} results:\n" + "\n".join(formatted_results)
                else:
                    return "No documents found matching the query."
            
            elif tool_name == "build_timeline":
                total_events = result.get('total_events', 0)
                if total_events > 0:
                    summary = result.get('timeline_summary', 'Timeline created successfully.')
                    date_range = result.get('date_range', {})
                    return f"Timeline built with {total_events} events ({date_range.get('start', 'Unknown')} to {date_range.get('end', 'Unknown')}). {summary}"
                else:
                    return "No timeline events found in the documents."
            
            elif tool_name == "extract_entities":
                total_entities = result.get('total_entities', 0)
                if total_entities > 0:
                    entities_by_type = result.get('entities_by_type', {})
                    summary_parts = []
                    for entity_type, entities in entities_by_type.items():
                        if entities:
                            summary_parts.append(f"{len(entities)} {entity_type}s")
                    summary = ", ".join(summary_parts) if summary_parts else "entities"
                    return f"Extracted {total_entities} entities: {summary}."
                else:
                    return "No entities found in the documents."
            
            elif tool_name == "cross_reference_documents":
                docs_analyzed = result.get('documents_analyzed', 0)
                cross_refs = result.get('cross_references', [])
                summary = result.get('summary', 'Cross-reference analysis completed.')
                return f"Analyzed {docs_analyzed} documents, found {len(cross_refs)} cross-references. {summary}"
            
            elif tool_name == "generate_citations":
                total_citations = result.get('total_citations', 0)
                style = result.get('citation_style', 'academic')
                return f"Generated {total_citations} citations in {style} style."
            
            else:
                # Generic formatting
                return f"{tool_name} completed successfully: {str(result)[:300]}..."
            
        except Exception as e:
            logger.error(f"Failed to format tool result: {str(e)}")
            return f"{tool_name} completed with result: {str(result)[:200]}..."
    
    async def _generate_final_answer(self, conversation_history: List[str], session: AgentSession) -> ReasoningStep:
        """Generate a final answer if the agent didn't provide one."""
        try:
            prompt = "\n".join(conversation_history) + "\n\nBased on your reasoning and tool usage above, provide a comprehensive final answer to the user's query."
            
            response = await self._generate_with_retry(prompt)
            
            final_step = ReasoningStep(
                step_number=len(session.reasoning_steps) + 1,
                state=AgentState.COMPLETED,
                thought="Generating final answer based on previous reasoning and tool results.",
                action="Final Answer",
                observation=response.text.strip() if response and response.text else "Unable to generate final answer."
            )
            
            return final_step
            
        except Exception as e:
            logger.error(f"Failed to generate final answer: {str(e)}")
            return ReasoningStep(
                step_number=len(session.reasoning_steps) + 1,
                state=AgentState.ERROR,
                thought="Failed to generate final answer.",
                observation=f"Error generating final answer: {str(e)}"
            )
    
    def _session_to_dict(self, session: AgentSession) -> Dict[str, Any]:
        """Convert AgentSession to dictionary."""
        return {
            "session_id": session.session_id,
            "query": session.query,
            "reasoning_steps": [self._reasoning_step_to_dict(step) for step in session.reasoning_steps],
            "final_answer": session.final_answer,
            "total_tool_calls": session.total_tool_calls,
            "session_start": session.session_start.isoformat(),
            "session_end": session.session_end.isoformat() if session.session_end else None,
            "success": session.success,
            "error": session.error
        }
    
    def _reasoning_step_to_dict(self, step: ReasoningStep) -> Dict[str, Any]:
        """Convert ReasoningStep to dictionary."""
        return {
            "step_number": step.step_number,
            "state": step.state.value,
            "thought": step.thought,
            "action": step.action,
            "observation": step.observation,
            "timestamp": step.timestamp.isoformat(),
            "tool_calls": [self._tool_call_to_dict(tc) for tc in step.tool_calls]
        }
    
    def _tool_call_to_dict(self, tool_call: ToolCall) -> Dict[str, Any]:
        """Convert ToolCall to dictionary."""
        return {
            "tool_name": tool_call.tool_name,
            "arguments": tool_call.arguments,
            "timestamp": tool_call.timestamp.isoformat(),
            "execution_time": tool_call.execution_time,
            "result": tool_call.result,
            "error": tool_call.error,
            "success": tool_call.success
        }


# Global agent instance
react_agent = ReActAgent()