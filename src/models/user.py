"""User data models."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SubscriptionType(str, Enum):
    """User subscription types."""

    FREE = "free"
    LITE = "lite"
    PRO = "pro"


class Language(str, Enum):
    """Supported languages."""

    RU = "ru"
    EN = "en"


class Payment(BaseModel):
    """Payment record model."""

    date: datetime
    type: str  # subscription_lite, subscription_pro, report_<name>
    amount: int  # Telegram Stars
    currency: str = "XTR"


class User(BaseModel):
    """User model."""

    telegram_id: int
    name: Optional[str] = None
    birth_date: Optional[date] = None
    language: Language = Language.RU
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Subscription
    subscription_type: SubscriptionType = SubscriptionType.FREE
    subscription_expires: Optional[datetime] = None

    # Limits tracking
    questions_today: int = 0
    questions_today_reset: Optional[date] = None
    questions_bonus: int = 0  # From referrals
    compatibility_this_week: int = 0
    compatibility_week_reset: Optional[date] = None

    # Referral
    referral_code: str = ""
    referred_by: Optional[int] = None  # telegram_id of referrer
    referrals_count: int = 0

    # Reports purchased (for FREE/LITE users)
    purchased_reports: list[str] = Field(default_factory=list)

    # Payment history
    payment_history: list[Payment] = Field(default_factory=list)

    # Settings
    notifications_enabled: bool = True
    notification_time: str = "08:00"  # HH:MM format

    def is_premium(self) -> bool:
        """Check if user has active premium subscription."""
        if self.subscription_type == SubscriptionType.FREE:
            return False
        if self.subscription_expires is None:
            return False
        return datetime.utcnow() < self.subscription_expires

    def can_ask_question(self) -> bool:
        """Check if user can ask a question."""
        if self.is_premium():
            return True
        # Check bonus questions first
        if self.questions_bonus > 0:
            return True
        # Check daily limit
        return self.questions_today < 3

    def can_check_compatibility(self) -> bool:
        """Check if user can check compatibility."""
        if self.is_premium():
            return True
        return self.compatibility_this_week < 2

    def has_report(self, report_type: str) -> bool:
        """Check if user has access to a report."""
        if self.subscription_type == SubscriptionType.PRO and self.is_premium():
            return True
        return report_type in self.purchased_reports

    def is_onboarded(self) -> bool:
        """Check if user has completed onboarding (has name and birth_date)."""
        return self.name is not None and self.birth_date is not None


class NumerologyProfile(BaseModel):
    """User's numerology profile with calculated numbers."""

    # Core numbers
    life_path: int  # Число Судьбы
    soul_number: int  # Число Души
    expression_number: int  # Число Имени
    personality_number: int  # Число Личности

    # Pythagoras matrix
    matrix: dict[int, int]  # {1: count, 2: count, ...}

    # Additional numbers
    birthday_number: int
    maturity_number: int

    # Personal cycles
    personal_year: int
    personal_month: int
    personal_day: int


class Conversation(BaseModel):
    """Chat message model."""

    telegram_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    role: str  # "user" or "assistant"
    content: str


class Report(BaseModel):
    """Generated report model."""

    telegram_id: int
    report_type: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
