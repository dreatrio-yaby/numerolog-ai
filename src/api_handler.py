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

    try:
        # Run async handler
        response = asyncio.get_event_loop().run_until_complete(api_handler(event))
        return response

    except Exception as e:
        logger.error(f"Error processing API request: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "https://dreatrio-yaby.github.io",
                "Access-Control-Allow-Methods": "GET, PUT, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Telegram-Init-Data",
            },
            "body": json.dumps({"error": "Internal server error"}),
        }
