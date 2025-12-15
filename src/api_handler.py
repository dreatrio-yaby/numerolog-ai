"""AWS Lambda handler for Mini App API."""

import asyncio
import json
import logging
from typing import Any

from src.handlers.api import api_handler

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict, context: Any) -> dict:
    """
    AWS Lambda handler for Mini App API.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    logger.info(f"API event: {json.dumps(event)}")

    # Run async handler
    response = asyncio.get_event_loop().run_until_complete(api_handler(event))
    return response
