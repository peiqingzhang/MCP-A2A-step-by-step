
import os
import json
import asyncio
from typing import Any, Dict, List, Literal
from collections.abc import AsyncIterable

from langchain_core.messages import AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from langchain.tools import Tool
from fastmcp import Client


import nest_asyncio
nest_asyncio.apply()


memory = MemorySaver()


async def mcp_tools(mcp_server_url: str) -> List[Tool]:
    """Discover tools from an MCP server and create LangChain tools."""

    async def discover_mcp_tools():
        """Discover available tools from MCP server"""
        try:
            async with Client(mcp_server_url, timeout=30.0) as client:
                tools = await client.list_tools()
                if not tools:
                    raise Exception("No tools found on MCP server.")
                return tools
        except Exception as e:
            raise Exception(f"Failed to connect to MCP server: {e}")

    def call_mcp_tool_sync(tool_name: str, arguments: Dict[str, Any]) -> str:
        """Synchronous wrapper for MCP tool calls"""
        async def _call_mcp_tool():
            try:
                async with Client(mcp_server_url, timeout=30.0) as client:
                    result = await client.call_tool(tool_name, arguments)
                    if result.content and len(result.content) > 0:
                        return result.content[0].text
                    else:
                        return f"No result from {tool_name}"
            except Exception as e:
                return f"Error calling {tool_name}: {str(e)}"

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return loop.run_until_complete(_call_mcp_tool())
            else:
                return asyncio.run(_call_mcp_tool())
        except:
            return asyncio.run(_call_mcp_tool())

    def create_langchain_tool(mcp_tool):
        """Create a LangChain tool from an MCP tool"""
        def tool_function(tool_input: str) -> str:
            try:
                if tool_input.startswith('{') and tool_input.endswith('}'):
                    arguments = json.loads(tool_input)
                else:
                    arguments = {"location": tool_input.strip()}
            except json.JSONDecodeError:
                arguments = {"location": tool_input.strip()}
            
            return call_mcp_tool_sync(mcp_tool.name, arguments)
        
        return Tool(
            name=mcp_tool.name,
            description=mcp_tool.description or f"MCP tool: {mcp_tool.name}",
            func=tool_function
        )

    discovered_tools = await discover_mcp_tools()
    return [create_langchain_tool(tool) for tool in discovered_tools]


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str


class WeatherAgent:
    """WeatherAgent - a specialized assistant for weather information."""

    SYSTEM_INSTRUCTION = (
        'You are a specialized assistant for weather information. '
        'Your sole purpose is to use the provided tools to answer questions about the weather. '
        'If the user asks about anything other than the weather, '
        'politely state that you cannot help with that topic and can only assist with weather-related queries. '
        'Do not attempt to answer unrelated questions or use tools for other purposes.'
    )

    FORMAT_INSTRUCTION = (
        'Set response status to input_required if the user needs to provide more information to complete the request.'
        'Set response status to error if there is an error while processing the request.'
        'Set response status to completed if the request is complete.'
    )

    def __init__(self, mcp_server_url: str):
        model_source = os.getenv('model_source', 'google')
        if model_source == 'openai':
            self.model = ChatOpenAI(
                model='gpt-4o-mini',
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                temperature=0.7,
            )
        elif model_source == 'google':
            self.model = ChatGoogleGenerativeAI(model='gemini-pro')
        else:
            self.model = ChatOpenAI(
                model=os.getenv('TOOL_LLM_NAME'),
                openai_api_key=os.getenv('API_KEY', 'EMPTY'),
                openai_api_base=os.getenv('TOOL_LLM_URL'),
                temperature=0,
            )
        
        self.tools = asyncio.run(mcp_tools(mcp_server_url))

        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=(self.FORMAT_INSTRUCTION, ResponseFormat),
        )

    async def stream(self, query, context_id) -> AsyncIterable[dict[str, Any]]:
        inputs = {'messages': [('user', query)]}
        config = {'configurable': {'thread_id': context_id}}

        for item in self.graph.stream(inputs, config, stream_mode='values'):
            message = item['messages'][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Checking the weather...',
                }
            elif isinstance(message, ToolMessage):
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Processing weather data..',
                }

        yield self.get_agent_response(config)

    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(
            structured_response, ResponseFormat
        ):
            if structured_response.status == 'input_required':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'error':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': (
                'We are unable to process your request at the moment. '
                'Please try again.'
            ),
        }

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
