
import logging
import os
import sys

import click
import httpx
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv

from app.agent import WeatherAgent
from app.agent_executor import WeatherAgentExecutor


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=8080)
def main(host, port):
    """Starts the Weather Agent server."""
    try:
        mcp_server_url = os.getenv('MCP_SERVER_URL')
        if not mcp_server_url:
            raise MissingAPIKeyError(
                'MCP_SERVER_URL environment variable not set.'
            )

        if os.getenv('model_source', 'google') == 'openai':
            if not os.getenv('OPENAI_API_KEY'):
                raise MissingAPIKeyError(
                    'OPENAI_API_KEY environment variable not set.'
                )
        elif os.getenv('model_source', 'google') == 'google':
            if not os.getenv('GOOGLE_API_KEY'):
                raise MissingAPIKeyError(
                    'GOOGLE_API_KEY environment variable not set.'
                )
        else:
            if not os.getenv('TOOL_LLM_URL'):
                raise MissingAPIKeyError(
                    'TOOL_LLM_URL environment variable not set.'
                )
            if not os.getenv('TOOL_LLM_NAME'):
                raise MissingAPIKeyError(
                    'TOOL_LLM_NAME environment not variable not set.'
                )

        capabilities = AgentCapabilities(streaming=True, push_notifications=True)
        skill = AgentSkill(
            id='get_weather',
            name='Weather Tool',
            description='Helps with getting the current weather and forecast',
            tags=['weather', 'forecast'],
            examples=['What is the weather in London?', 'Give me a 5-day forecast for New York'],
        )
        host_override = os.getenv('HOST_OVERRIDE')
        agent_card_url = host_override if host_override else f'http://{host}:{port}/'

        agent_card = AgentCard(
            name='Weather Agent',
            description='Helps with weather information',
            url=agent_card_url,
            version='1.0.0',
            default_input_modes=WeatherAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=WeatherAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )


        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(httpx_client=httpx_client,
                        config_store=push_config_store)
        request_handler = DefaultRequestHandler(
            agent_executor=WeatherAgentExecutor(mcp_server_url),
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender= push_sender
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        sys.exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
