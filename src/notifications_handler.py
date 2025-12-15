"""AWS Lambda handler for daily notifications."""

import asyncio
import logging
from datetime import datetime
from typing import Any

from aiogram import Bot

from src.config import get_settings
from src.services.ai import ai_service
from src.services.database import db
from src.services.numerology import NumerologyService

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

settings = get_settings()

# Initialize bot
bot = Bot(token=settings.telegram_bot_token)
numerology = NumerologyService()


async def send_daily_forecasts(hour: int) -> int:
    """
    Send daily forecasts to users who have notifications enabled at this hour.

    Args:
        hour: Current hour (0-23)

    Returns:
        Number of notifications sent
    """
    users = await db.get_users_for_notifications(hour)
    sent_count = 0

    for user in users:
        # Calculate profile
        profile = numerology.calculate_profile(user.birth_date)

        # Generate forecast
        forecast = await ai_service.generate_daily_forecast(user, profile)

        # Send message
        if user.language.value == "ru":
            message = f"🌅 *Твой прогноз на сегодня*\n\n{forecast}"
        else:
            message = f"🌅 *Your forecast for today*\n\n{forecast}"

        await bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="Markdown",
        )
        sent_count += 1
        logger.info(f"Sent daily forecast to user {user.telegram_id}")

    return sent_count


def handler(event: dict, context: Any) -> dict:
    """
    AWS Lambda handler for scheduled notifications.

    Args:
        event: EventBridge scheduled event
        context: Lambda context

    Returns:
        Response with count of sent notifications
    """
    logger.info(f"Notifications handler triggered: {event}")

    # Get current UTC hour
    current_hour = datetime.utcnow().hour

    # Send forecasts
    sent_count = asyncio.get_event_loop().run_until_complete(send_daily_forecasts(current_hour))

    logger.info(f"Sent {sent_count} daily forecasts for hour {current_hour}")

    return {
        "statusCode": 200,
        "body": {
            "hour": current_hour,
            "notifications_sent": sent_count,
        },
    }


# For local testing
if __name__ == "__main__":
    import sys

    hour = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.utcnow().hour
    print(f"Testing notifications for hour {hour}...")
    count = asyncio.run(send_daily_forecasts(hour))
    print(f"Sent {count} notifications")
