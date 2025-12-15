"""DynamoDB service for user data persistence."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key

from src.config import get_settings
from src.models.user import Conversation, Language, Payment, Report, SubscriptionType, User

settings = get_settings()


class DatabaseService:
    """DynamoDB database service."""

    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.users_table = self.dynamodb.Table(settings.dynamodb_table_users)
        self.conversations_table = self.dynamodb.Table(settings.dynamodb_table_conversations)
        self.reports_table = self.dynamodb.Table(settings.dynamodb_table_reports)

    def _user_to_item(self, user: User) -> dict:
        """Convert User model to DynamoDB item."""
        return {
            "PK": f"USER#{user.telegram_id}",
            "telegram_id": user.telegram_id,
            "name": user.name,
            "birth_date": user.birth_date.isoformat(),
            "language": user.language.value,
            "created_at": user.created_at.isoformat(),
            "subscription_type": user.subscription_type.value,
            "subscription_expires": (
                user.subscription_expires.isoformat() if user.subscription_expires else None
            ),
            "questions_today": user.questions_today,
            "questions_today_reset": (
                user.questions_today_reset.isoformat() if user.questions_today_reset else None
            ),
            "questions_bonus": user.questions_bonus,
            "compatibility_this_week": user.compatibility_this_week,
            "compatibility_week_reset": (
                user.compatibility_week_reset.isoformat()
                if user.compatibility_week_reset
                else None
            ),
            "referral_code": user.referral_code,
            "referred_by": user.referred_by,
            "referrals_count": user.referrals_count,
            "purchased_reports": user.purchased_reports,
            "payment_history": [
                {
                    "date": p.date.isoformat(),
                    "type": p.type,
                    "amount": p.amount,
                    "currency": p.currency,
                }
                for p in user.payment_history
            ],
            "notifications_enabled": user.notifications_enabled,
            "notification_time": user.notification_time,
        }

    def _item_to_user(self, item: dict) -> User:
        """Convert DynamoDB item to User model."""
        return User(
            telegram_id=item["telegram_id"],
            name=item["name"],
            birth_date=date.fromisoformat(item["birth_date"]),
            language=Language(item.get("language", "ru")),
            created_at=datetime.fromisoformat(item["created_at"]),
            subscription_type=SubscriptionType(item.get("subscription_type", "free")),
            subscription_expires=(
                datetime.fromisoformat(item["subscription_expires"])
                if item.get("subscription_expires")
                else None
            ),
            questions_today=int(item.get("questions_today", 0)),
            questions_today_reset=(
                date.fromisoformat(item["questions_today_reset"])
                if item.get("questions_today_reset")
                else None
            ),
            questions_bonus=int(item.get("questions_bonus", 0)),
            compatibility_this_week=int(item.get("compatibility_this_week", 0)),
            compatibility_week_reset=(
                date.fromisoformat(item["compatibility_week_reset"])
                if item.get("compatibility_week_reset")
                else None
            ),
            referral_code=item.get("referral_code", ""),
            referred_by=item.get("referred_by"),
            referrals_count=int(item.get("referrals_count", 0)),
            purchased_reports=item.get("purchased_reports", []),
            payment_history=[
                Payment(
                    date=datetime.fromisoformat(p["date"]),
                    type=p["type"],
                    amount=int(p["amount"]),
                    currency=p.get("currency", "XTR"),
                )
                for p in item.get("payment_history", [])
            ],
            notifications_enabled=item.get("notifications_enabled", True),
            notification_time=item.get("notification_time", "08:00"),
        )

    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram_id."""
        response = self.users_table.get_item(Key={"PK": f"USER#{telegram_id}"})
        item = response.get("Item")
        if item:
            return self._item_to_user(item)
        return None

    async def create_user(
        self,
        telegram_id: int,
        name: str,
        birth_date: date,
        language: Language = Language.RU,
        referred_by: Optional[int] = None,
    ) -> User:
        """Create new user."""
        user = User(
            telegram_id=telegram_id,
            name=name,
            birth_date=birth_date,
            language=language,
            referral_code=self._generate_referral_code(),
            referred_by=referred_by,
        )
        self.users_table.put_item(Item=self._user_to_item(user))

        # If referred, update referrer's bonuses
        if referred_by:
            await self._process_referral(referred_by)

        return user

    async def update_user(self, user: User) -> User:
        """Update existing user."""
        self.users_table.put_item(Item=self._user_to_item(user))
        return user

    async def increment_questions_today(self, user: User) -> User:
        """Increment daily question counter, reset if new day."""
        today = date.today()

        # Reset counter if new day
        if user.questions_today_reset != today:
            user.questions_today = 0
            user.questions_today_reset = today

        # Use bonus questions first if available
        if user.questions_bonus > 0:
            user.questions_bonus -= 1
        else:
            user.questions_today += 1

        return await self.update_user(user)

    async def increment_compatibility_this_week(self, user: User) -> User:
        """Increment weekly compatibility counter."""
        today = date.today()

        # Reset counter if new week (Monday)
        if user.compatibility_week_reset is None or (
            today - user.compatibility_week_reset
        ).days >= 7:
            user.compatibility_this_week = 0
            user.compatibility_week_reset = today

        user.compatibility_this_week += 1
        return await self.update_user(user)

    async def activate_subscription(
        self,
        user: User,
        subscription_type: SubscriptionType,
    ) -> User:
        """Activate subscription for user."""
        from datetime import timedelta

        user.subscription_type = subscription_type
        user.subscription_expires = datetime.utcnow() + timedelta(
            days=settings.subscription_days
        )
        return await self.update_user(user)

    async def add_payment(
        self,
        user: User,
        payment_type: str,
        amount: int,
    ) -> User:
        """Add payment to user's payment history."""
        payment = Payment(
            date=datetime.utcnow(),
            type=payment_type,
            amount=amount,
            currency="XTR",
        )
        user.payment_history.append(payment)
        return await self.update_user(user)

    async def add_purchased_report(self, user: User, report_type: str) -> User:
        """Add purchased report to user."""
        if report_type not in user.purchased_reports:
            user.purchased_reports.append(report_type)
        return await self.update_user(user)

    async def _process_referral(self, referrer_id: int) -> None:
        """Process referral bonus for referrer."""
        referrer = await self.get_user(referrer_id)
        if referrer:
            referrer.referrals_count += 1
            referrer.questions_bonus += settings.referral_bonus_questions
            # Add bonus report access (first referral gets one free report)
            if referrer.referrals_count == 1:
                referrer.purchased_reports.append("full_portrait")  # Bonus report
            await self.update_user(referrer)

    def _generate_referral_code(self) -> str:
        """Generate unique referral code."""
        return str(uuid.uuid4())[:8].upper()

    # Conversation methods

    async def save_message(self, telegram_id: int, role: str, content: str) -> None:
        """Save conversation message."""
        timestamp = datetime.utcnow().isoformat()
        self.conversations_table.put_item(
            Item={
                "PK": f"USER#{telegram_id}",
                "SK": f"MSG#{timestamp}",
                "role": role,
                "content": content,
                "timestamp": timestamp,
            }
        )

    async def get_conversation_history(
        self,
        telegram_id: int,
        limit: int = 20,
    ) -> list[dict]:
        """Get recent conversation history."""
        response = self.conversations_table.query(
            KeyConditionExpression=Key("PK").eq(f"USER#{telegram_id}"),
            ScanIndexForward=False,  # Most recent first
            Limit=limit,
        )

        messages = []
        for item in reversed(response.get("Items", [])):
            messages.append({"role": item["role"], "content": item["content"]})

        return messages

    # Report methods

    async def save_report(
        self,
        telegram_id: int,
        report_type: str,
        content: str,
    ) -> None:
        """Save generated report."""
        self.reports_table.put_item(
            Item={
                "PK": f"USER#{telegram_id}",
                "SK": f"REPORT#{report_type}",
                "content": content,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    async def get_report(
        self,
        telegram_id: int,
        report_type: str,
    ) -> Optional[str]:
        """Get saved report."""
        response = self.reports_table.get_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"REPORT#{report_type}",
            }
        )
        item = response.get("Item")
        if item:
            return item["content"]
        return None

    # Users with notifications enabled (for daily forecasts)

    async def get_users_for_notifications(self, hour: int) -> list[User]:
        """Get users who should receive notifications at given hour."""
        # This would require a GSI on notification_time
        # For MVP, we'll scan (not efficient but works for small user base)
        response = self.users_table.scan(
            FilterExpression="notifications_enabled = :enabled AND begins_with(notification_time, :hour)",
            ExpressionAttributeValues={
                ":enabled": True,
                ":hour": f"{hour:02d}:",
            },
        )

        return [self._item_to_user(item) for item in response.get("Items", [])]


# Global instance
db = DatabaseService()
