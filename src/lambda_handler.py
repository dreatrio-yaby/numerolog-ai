"""AWS Lambda handler for Telegram webhook."""

import asyncio
import json
import logging
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update

from src.config import get_settings
from src.handlers.bot import router

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

settings = get_settings()

# Initialize bot and dispatcher
bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()
dp.include_router(router)


def handler(event: dict, context: Any) -> dict:
    """
    AWS Lambda handler for Telegram webhook.

    Args:
        event: API Gateway event with Telegram update
        context: Lambda context

    Returns:
        API Gateway response
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Parse request body
        if "body" in event:
            body = event["body"]
            if isinstance(body, str):
                body = json.loads(body)
        else:
            body = event

        # Create Update object
        update = Update.model_validate(body, context={"bot": bot})

        # Process update
        asyncio.get_event_loop().run_until_complete(dp.feed_update(bot, update))

        return {
            "statusCode": 200,
            "body": json.dumps({"ok": True}),
        }

    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        return {
            "statusCode": 200,  # Return 200 to Telegram to avoid retries
            "body": json.dumps({"ok": False, "error": str(e)}),
        }


async def set_webhook(url: str) -> bool:
    """
    Set Telegram webhook URL.

    Args:
        url: Webhook URL (API Gateway endpoint)

    Returns:
        True if successful
    """
    result = await bot.set_webhook(url)
    logger.info(f"Webhook set to {url}: {result}")
    return result


async def delete_webhook() -> bool:
    """Delete Telegram webhook."""
    result = await bot.delete_webhook()
    logger.info(f"Webhook deleted: {result}")
    return result


# For local testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "set_webhook":
            if len(sys.argv) > 2:
                url = sys.argv[2]
                asyncio.run(set_webhook(url))
            else:
                print("Usage: python lambda_handler.py set_webhook <url>")
        elif sys.argv[1] == "delete_webhook":
            asyncio.run(delete_webhook())
    else:
        # Run polling for local development
        print("Starting bot in polling mode...")
        asyncio.run(dp.start_polling(bot))
