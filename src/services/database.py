"""DynamoDB service for user data persistence."""

import uuid
from datetime import date, datetime
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key

from src.config import get_settings
from src.models.user import Language, Payment, SubscriptionType, User

settings = get_settings()

# Report types that support multiple instances with context
MULTI_INSTANCE_REPORTS = {"compatibility_pro", "name_selection", "year_forecast", "date_calendar"}


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
            "birth_date": user.birth_date.isoformat() if user.birth_date else None,
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
                user.compatibility_week_reset.isoformat() if user.compatibility_week_reset else None
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
            name=item.get("name"),
            birth_date=(date.fromisoformat(item["birth_date"]) if item.get("birth_date") else None),
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
        name: Optional[str] = None,
        birth_date: Optional[date] = None,
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
        if (
            user.compatibility_week_reset is None
            or (today - user.compatibility_week_reset).days >= 7
        ):
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
        user.subscription_expires = datetime.utcnow() + timedelta(days=settings.subscription_days)
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
        """Get saved report content.

        For multi-instance reports, returns the latest instance.
        For backward compatibility with existing code.
        """
        if report_type in MULTI_INSTANCE_REPORTS:
            # Check for multi-instance reports first
            instances = await self.get_report_instances(telegram_id, report_type)
            if instances:
                instance = await self.get_report_instance(
                    telegram_id, report_type, instances[0]["instance_id"]
                )
                if instance:
                    return instance.get("content")
            return None

        # Single-instance report (legacy format)
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

    async def get_report_with_metadata(
        self,
        telegram_id: int,
        report_type: str,
        instance_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Get saved report with metadata (content, created_at).

        For multi-instance reports, if instance_id is provided, returns that instance.
        Otherwise returns the latest instance.
        For single-instance reports, returns the only instance.
        """
        if report_type in MULTI_INSTANCE_REPORTS:
            if instance_id:
                # Get specific instance
                return await self.get_report_instance(telegram_id, report_type, instance_id)
            else:
                # Get latest instance
                instances = await self.get_report_instances(telegram_id, report_type)
                if instances:
                    return await self.get_report_instance(
                        telegram_id, report_type, instances[0]["instance_id"]
                    )
                return None

        # Single-instance report (legacy format)
        response = self.reports_table.get_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"REPORT#{report_type}",
            }
        )
        item = response.get("Item")
        if item:
            return {
                "content": item["content"],
                "created_at": item.get("created_at"),
            }
        return None

    # Multi-instance report methods

    async def save_report_instance(
        self,
        telegram_id: int,
        report_type: str,
        content: str,
        context: dict,
    ) -> str:
        """Save report with context for multi-instance reports.

        Returns the generated instance_id.
        """
        instance_id = str(uuid.uuid4())[:8]
        self.reports_table.put_item(
            Item={
                "PK": f"USER#{telegram_id}",
                "SK": f"REPORT#{report_type}#{instance_id}",
                "report_type": report_type,
                "instance_id": instance_id,
                "content": content,
                "context": context,
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        return instance_id

    async def get_report_instances(
        self,
        telegram_id: int,
        report_type: str,
    ) -> list[dict]:
        """Get all instances of a multi-instance report type.

        Returns list of {instance_id, context, created_at} sorted by created_at desc.
        Does NOT include content to minimize data transfer.
        """
        response = self.reports_table.query(
            KeyConditionExpression=(
                Key("PK").eq(f"USER#{telegram_id}") &
                Key("SK").begins_with(f"REPORT#{report_type}#")
            ),
        )

        instances = []
        for item in response.get("Items", []):
            instances.append({
                "instance_id": item.get("instance_id"),
                "context": item.get("context", {}),
                "created_at": item.get("created_at"),
            })

        # Sort by created_at descending (newest first)
        instances.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return instances

    async def get_report_instance(
        self,
        telegram_id: int,
        report_type: str,
        instance_id: str,
    ) -> Optional[dict]:
        """Get specific report instance with full content."""
        response = self.reports_table.get_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"REPORT#{report_type}#{instance_id}",
            }
        )
        item = response.get("Item")
        if item:
            return {
                "instance_id": item.get("instance_id"),
                "content": item.get("content"),
                "context": item.get("context", {}),
                "created_at": item.get("created_at"),
            }
        return None

    async def delete_report_instance(
        self,
        telegram_id: int,
        report_type: str,
        instance_id: str,
    ) -> None:
        """Delete specific report instance."""
        self.reports_table.delete_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"REPORT#{report_type}#{instance_id}",
            }
        )

    async def get_report_instance_count(
        self,
        telegram_id: int,
        report_type: str,
    ) -> int:
        """Get count of report instances for a type."""
        response = self.reports_table.query(
            KeyConditionExpression=(
                Key("PK").eq(f"USER#{telegram_id}") &
                Key("SK").begins_with(f"REPORT#{report_type}#")
            ),
            Select="COUNT",
        )
        return response.get("Count", 0)

    # Pending report data (for reports that need additional input before purchase)

    async def save_pending_report_data(
        self,
        telegram_id: int,
        report_id: str,
        data: dict,
    ) -> None:
        """Save additional data needed for report generation (before payment)."""
        self.reports_table.put_item(
            Item={
                "PK": f"USER#{telegram_id}",
                "SK": f"PENDING#{report_id}",
                "data": data,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    async def get_pending_report_data(
        self,
        telegram_id: int,
        report_id: str,
    ) -> Optional[dict]:
        """Get pending report data."""
        response = self.reports_table.get_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"PENDING#{report_id}",
            }
        )
        item = response.get("Item")
        if item:
            return item.get("data")
        return None

    async def delete_pending_report_data(
        self,
        telegram_id: int,
        report_id: str,
    ) -> None:
        """Delete pending report data after generation."""
        self.reports_table.delete_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"PENDING#{report_id}",
            }
        )

    # Report generation lock (to prevent duplicate processing)

    async def is_report_generating(self, telegram_id: int, report_id: str) -> bool:
        """Check if report is currently being generated."""
        response = self.reports_table.get_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"LOCK#{report_id}",
            }
        )
        item = response.get("Item")
        if item:
            # Check if lock is stale (older than 2 minutes)
            created_at = datetime.fromisoformat(item["created_at"])
            if (datetime.utcnow() - created_at).total_seconds() > 120:
                await self.clear_report_generating(telegram_id, report_id)
                return False
            return True
        return False

    async def set_report_generating(self, telegram_id: int, report_id: str) -> None:
        """Set lock indicating report is being generated."""
        self.reports_table.put_item(
            Item={
                "PK": f"USER#{telegram_id}",
                "SK": f"LOCK#{report_id}",
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    async def clear_report_generating(self, telegram_id: int, report_id: str) -> None:
        """Clear the generation lock."""
        self.reports_table.delete_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"LOCK#{report_id}",
            }
        )

    # Compatibility results storage

    async def save_compatibility_result(
        self,
        telegram_id: int,
        partner_date: date,
        scores: dict,
        ai_interpretation: Optional[str] = None,
    ) -> str:
        """Save compatibility calculation result. Returns result_id."""
        result_id = str(uuid.uuid4())[:8]
        self.reports_table.put_item(
            Item={
                "PK": f"USER#{telegram_id}",
                "SK": f"COMPAT#{result_id}",
                "partner_date": partner_date.isoformat(),
                "scores": scores,
                "ai_interpretation": ai_interpretation,
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        return result_id

    async def get_compatibility_result(
        self,
        telegram_id: int,
        result_id: str,
    ) -> Optional[dict]:
        """Get saved compatibility result."""
        response = self.reports_table.get_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"COMPAT#{result_id}",
            }
        )
        item = response.get("Item")
        if item:
            return {
                "result_id": result_id,
                "partner_date": item.get("partner_date"),
                "scores": item.get("scores", {}),
                "ai_interpretation": item.get("ai_interpretation"),
                "created_at": item.get("created_at"),
            }
        return None

    async def update_compatibility_interpretation(
        self,
        telegram_id: int,
        result_id: str,
        ai_interpretation: str,
    ) -> None:
        """Update AI interpretation for existing compatibility result."""
        self.reports_table.update_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"COMPAT#{result_id}",
            },
            UpdateExpression="SET ai_interpretation = :interp",
            ExpressionAttributeValues={":interp": ai_interpretation},
        )

    async def get_compatibility_history(
        self,
        telegram_id: int,
        limit: int = 10,
    ) -> list[dict]:
        """Get user's compatibility check history."""
        response = self.reports_table.query(
            KeyConditionExpression=(
                Key("PK").eq(f"USER#{telegram_id}") &
                Key("SK").begins_with("COMPAT#")
            ),
        )

        results = []
        for item in response.get("Items", []):
            result_id = item["SK"].replace("COMPAT#", "")
            results.append({
                "result_id": result_id,
                "partner_date": item.get("partner_date"),
                "overall_score": item.get("scores", {}).get("overall_score"),
                "created_at": item.get("created_at"),
            })

        # Sort by created_at descending
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results[:limit]

    async def delete_compatibility_result(
        self,
        telegram_id: int,
        result_id: str,
    ) -> None:
        """Delete compatibility result."""
        self.reports_table.delete_item(
            Key={
                "PK": f"USER#{telegram_id}",
                "SK": f"COMPAT#{result_id}",
            }
        )

    # Users with notifications enabled (for daily forecasts)

    async def get_users_for_notifications(self, hour: int) -> list[User]:
        """Get users who should receive notifications at given hour."""
        # This would require a GSI on notification_time
        # For MVP, we'll scan (not efficient but works for small user base)
        response = self.users_table.scan(
            FilterExpression=(
                "notifications_enabled = :enabled AND begins_with(notification_time, :hour)"
            ),
            ExpressionAttributeValues={
                ":enabled": True,
                ":hour": f"{hour:02d}:",
            },
        )

        return [self._item_to_user(item) for item in response.get("Items", [])]


# Global instance
db = DatabaseService()
