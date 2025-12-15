"""Application configuration."""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram
    telegram_bot_token: str = ""

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # AWS
    aws_region: str = "eu-central-1"
    dynamodb_table_users: str = "numerolog-users"
    dynamodb_table_conversations: str = "numerolog-conversations"
    dynamodb_table_reports: str = "numerolog-reports"

    # Application
    env: str = "development"
    debug: bool = False

    # Limits
    free_questions_per_day: int = 10
    free_compatibility_per_week: int = 2

    # Pricing (Telegram Stars)
    price_lite: int = 175  # ~350 RUB
    price_pro: int = 500  # ~1000 RUB
    price_report: int = 100  # ~200 RUB
    subscription_days: int = 30

    # Referral
    referral_bonus_questions: int = 10
    referral_bonus_reports: int = 1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields like AWS keys


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
