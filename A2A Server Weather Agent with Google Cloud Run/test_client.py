
import logging
import asyncio
import click
from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
)


async def main(base_url: str, query: str) -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    async with httpx.AsyncClient(timeout=60.0) as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)

        try:
            logger.info(f'Attempting to fetch agent card from: {base_url}{AGENT_CARD_WELL_KNOWN_PATH}')
            agent_card = await resolver.get_agent_card()
            logger.info('Successfully fetched agent card:')
            logger.info(agent_card.model_dump_json(indent=2, exclude_none=True))

        except Exception as e:
            logger.error(f'Critical error fetching agent card: {e}', exc_info=True)
            raise RuntimeError('Failed to fetch the agent card. Cannot continue.') from e

        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        logger.info('A2AClient initialized.')

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': query}
                ],
                'message_id': uuid4().hex,
            },
        }
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )

        response = await client.send_message(request)
        print(response.model_dump(mode='json', exclude_none=True))

@click.command()
@click.option('--url', default='<your-a2a-server-agent-url>', help='The base URL of the weather agent.')
@click.option('--query', default='What is the weather in London?', help='The query to send to the weather agent.')
def run(url: str, query: str):
    asyncio.run(main(url, query))

if __name__ == '__main__':
    run()
