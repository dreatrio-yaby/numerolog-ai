"""API handlers for Telegram Mini App."""

import hashlib
import hmac
import json
from datetime import date, datetime
from typing import Any
from urllib.parse import unquote

from aiogram import Bot
from aiogram.types import LabeledPrice

from src.config import get_settings
from src.models.user import Language
from src.services.ai import ai_service
from src.services.database import db
from src.services.numerology import calculate_compatibility, get_full_profile

settings = get_settings()

# Lazy-loaded Bot instance for invoice creation
_bot: Bot | None = None


def get_bot() -> Bot:
    """Get or create Bot instance for API operations."""
    global _bot
    if _bot is None:
        _bot = Bot(token=settings.telegram_bot_token)
    return _bot


# Available reports with prices
AVAILABLE_REPORTS = [
    {
        "id": "full_portrait",
        "name_ru": "Полный портрет",
        "name_en": "Full Portrait",
        "price": 120,
        "requires_input": None,
        "multi_instance": False,
    },
    {
        "id": "financial_code",
        "name_ru": "Финансовый код",
        "name_en": "Financial Code",
        "price": 150,
        "requires_input": None,
        "multi_instance": False,
    },
    {
        "id": "date_calendar",
        "name_ru": "Календарь дат",
        "name_en": "Date Calendar",
        "price": 130,
        "requires_input": "month_year",
        "multi_instance": True,
    },
    {
        "id": "year_forecast",
        "name_ru": "Прогноз на год",
        "name_en": "Year Forecast",
        "price": 150,
        "requires_input": "year",
        "multi_instance": True,
    },
    {
        "id": "name_selection",
        "name_ru": "Подбор имени",
        "name_en": "Name Selection",
        "price": 140,
        "requires_input": "name_context",
        "multi_instance": True,
    },
    {
        "id": "compatibility_pro",
        "name_ru": "Совместимость PRO",
        "name_en": "Compatibility PRO",
        "price": 150,
        "requires_input": "partner_data",
        "multi_instance": True,
    },
]


def validate_init_data(init_data: str) -> dict | None:
    """Validate Telegram Mini App initData and extract user info."""
    # Parse the init data
    parsed = {}
    for pair in init_data.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            parsed[key] = unquote(value)

    # Extract hash
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    # Build data check string (sorted alphabetically)
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    # Calculate secret key
    secret_key = hmac.new(
        b"WebAppData",
        settings.telegram_bot_token.encode(),
        hashlib.sha256,
    ).digest()

    # Calculate hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if calculated_hash != received_hash:
        return None

    # Extract user from parsed data
    user_data = parsed.get("user")
    if user_data:
        return json.loads(user_data)
    return None


def cors_response(status_code: int, body: Any) -> dict:
    """Create CORS-enabled response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://dreatrio-yaby.github.io",
            "Access-Control-Allow-Methods": "GET, PUT, POST, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Telegram-Init-Data",
        },
        "body": json.dumps(body) if body else "",
    }


def error_response(status_code: int, message: str) -> dict:
    """Create error response."""
    return cors_response(status_code, {"error": message})


async def handle_get_user(telegram_id: int) -> dict:
    """Handle GET /api/user - get full user data."""
    user = await db.get_user(telegram_id)
    if not user:
        return error_response(404, "User not found")

    is_onboarded = user.is_onboarded()

    # Build referral link
    bot_username = "NumeroChatBot"
    referral_link = f"https://t.me/{bot_username}?start=ref_{user.referral_code}"

    # Base response data (always available)
    response_data = {
        "is_onboarded": is_onboarded,
        "user": {
            "name": user.name,
            "birth_date": user.birth_date.isoformat() if user.birth_date else None,
            "language": user.language.value,
            "notifications_enabled": user.notifications_enabled,
            "notification_time": user.notification_time,
            "created_at": user.created_at.isoformat(),
        },
        "subscription": {
            "type": user.subscription_type.value,
            "expires": user.subscription_expires.isoformat() if user.subscription_expires else None,
            "is_active": user.is_premium(),
        },
        "referral": {
            "code": user.referral_code,
            "link": referral_link,
            "referrals_count": user.referrals_count,
            "questions_bonus": user.questions_bonus,
        },
        "reports": {
            "purchased": user.purchased_reports,
            "available": [r["id"] for r in AVAILABLE_REPORTS],
        },
        "limits": {
            "questions_today": user.questions_today,
            "questions_limit": 3,
            "compatibility_this_week": user.compatibility_this_week,
            "compatibility_limit": 2,
        },
    }

    # Add numerology data only if onboarded (has name and birth_date)
    if is_onboarded:
        profile = get_full_profile(user.name, user.birth_date)
        response_data["numerology"] = {
            "life_path": profile.life_path,
            "soul_number": profile.soul_number,
            "expression_number": profile.expression_number,
            "personality_number": profile.personality_number,
            "birthday_number": profile.birthday_number,
            "maturity_number": profile.maturity_number,
            "personal_year": profile.personal_year,
            "personal_month": profile.personal_month,
            "personal_day": profile.personal_day,
            "matrix": profile.matrix,
        }
    else:
        # Placeholder numerology data for non-onboarded users
        response_data["numerology"] = None

    return cors_response(200, response_data)


async def handle_update_settings(telegram_id: int, body: dict) -> dict:
    """Handle PUT /api/user/settings - update user settings."""
    user = await db.get_user(telegram_id)
    if not user:
        return error_response(404, "User not found")

    # Update allowed fields
    if "language" in body:
        lang = body["language"]
        if lang in ("ru", "en"):
            user.language = Language(lang)

    if "notifications_enabled" in body:
        user.notifications_enabled = bool(body["notifications_enabled"])

    if "notification_time" in body:
        time_str = body["notification_time"]
        # Validate HH:MM format
        if (
            len(time_str) == 5
            and time_str[2] == ":"
            and time_str[:2].isdigit()
            and time_str[3:].isdigit()
        ):
            hour = int(time_str[:2])
            minute = int(time_str[3:])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                user.notification_time = time_str

    await db.update_user(user)

    return cors_response(200, {"success": True})


async def handle_get_payments(telegram_id: int) -> dict:
    """Handle GET /api/payments - get payment history."""
    user = await db.get_user(telegram_id)
    if not user:
        return error_response(404, "User not found")

    payments = [
        {
            "date": p.date.isoformat(),
            "type": p.type,
            "amount": p.amount,
            "currency": p.currency,
        }
        for p in user.payment_history
    ]

    return cors_response(200, {"payments": payments})


async def handle_get_reports(telegram_id: int) -> dict:
    """Handle GET /api/reports - get available reports with status."""
    user = await db.get_user(telegram_id)
    if not user:
        return error_response(404, "User not found")

    is_pro = user.subscription_type.value == "pro" and user.is_premium()

    reports = []
    for report in AVAILABLE_REPORTS:
        report_id = report["id"]
        is_multi = report.get("multi_instance", False)

        status = "available"
        if report_id in user.purchased_reports:
            status = "purchased"
        elif is_pro:
            status = "included_in_pro"

        report_data = {
            "id": report_id,
            "name_ru": report["name_ru"],
            "name_en": report["name_en"],
            "price": report["price"],
            "status": status,
            "requires_input": report["requires_input"],
            "multi_instance": is_multi,
        }

        # For multi-instance reports, get all instances
        if is_multi and status in ("purchased", "included_in_pro"):
            instances = await db.get_report_instances(telegram_id, report_id)
            report_data["instances"] = instances
            report_data["instance_count"] = len(instances)
            report_data["is_generated"] = len(instances) > 0
        else:
            # Check if single-instance report content exists
            is_generated = False
            if status in ("purchased", "included_in_pro"):
                report_content = await db.get_report(telegram_id, report_id)
                is_generated = report_content is not None
            report_data["is_generated"] = is_generated

        reports.append(report_data)

    return cors_response(200, {"reports": reports})


async def handle_get_report_content(
    telegram_id: int, report_id: str, instance_id: str = None
) -> dict:
    """Handle GET /api/reports/{report_id} or GET /api/reports/{report_id}/{instance_id}."""
    user = await db.get_user(telegram_id)
    if not user:
        return error_response(404, "User not found")

    # Find report metadata
    report_meta = next((r for r in AVAILABLE_REPORTS if r["id"] == report_id), None)
    if not report_meta:
        return error_response(404, "Unknown report type")

    # Check if user has access to this report
    is_pro = user.subscription_type.value == "pro" and user.is_premium()
    has_access = report_id in user.purchased_reports or is_pro

    if not has_access:
        return error_response(403, "Report not purchased")

    is_multi = report_meta.get("multi_instance", False)

    # Get report content from database
    if is_multi:
        report_data = await db.get_report_with_metadata(telegram_id, report_id, instance_id)
    else:
        report_data = await db.get_report_with_metadata(telegram_id, report_id)

    if not report_data:
        return error_response(404, "Report not generated yet")

    # Build response
    response = {
        "id": report_id,
        "title_ru": report_meta["name_ru"],
        "title_en": report_meta["name_en"],
        "content": report_data["content"],
        "generated_at": report_data.get("created_at"),
    }

    # Add instance-specific data for multi-instance reports
    if is_multi:
        response["instance_id"] = report_data.get("instance_id")
        response["context"] = report_data.get("context", {})

    return cors_response(200, response)


async def handle_delete_report_instance(
    telegram_id: int, report_id: str, instance_id: str
) -> dict:
    """Handle DELETE /api/reports/{report_id}/{instance_id} - delete report instance."""
    user = await db.get_user(telegram_id)
    if not user:
        return error_response(404, "User not found")

    # Find report metadata
    report_meta = next((r for r in AVAILABLE_REPORTS if r["id"] == report_id), None)
    if not report_meta:
        return error_response(404, "Unknown report type")

    # Only multi-instance reports can be deleted
    if not report_meta.get("multi_instance", False):
        return error_response(400, "Cannot delete single-instance report")

    # Check if user has access
    is_pro = user.subscription_type.value == "pro" and user.is_premium()
    has_access = report_id in user.purchased_reports or is_pro

    if not has_access:
        return error_response(403, "Report not purchased")

    # Check if instance exists
    instance_data = await db.get_report_instance(telegram_id, report_id, instance_id)
    if not instance_data:
        return error_response(404, "Report instance not found")

    # Delete the instance
    await db.delete_report_instance(telegram_id, report_id, instance_id)

    return cors_response(200, {"success": True})


async def handle_create_invoice(telegram_id: int, body: dict) -> dict:
    """Handle POST /api/invoice - create invoice link for purchase."""
    user = await db.get_user(telegram_id)
    if not user:
        return error_response(404, "User not found")

    product_type = body.get("type")  # subscription_lite, subscription_pro, report_<id>

    if not product_type:
        return error_response(400, "Missing product type")

    # Determine price, title and description
    if product_type == "subscription_lite":
        amount = settings.price_lite
        title = "LITE — 30 дней" if user.language == Language.RU else "LITE — 30 days"
        description = (
            "Безлимит вопросов и совместимости"
            if user.language == Language.RU
            else "Unlimited questions and compatibility"
        )
    elif product_type == "subscription_pro":
        amount = settings.price_pro
        title = "PRO — 30 дней" if user.language == Language.RU else "PRO — 30 days"
        description = (
            "Безлимит + все премиум отчёты"
            if user.language == Language.RU
            else "Unlimited + all premium reports"
        )
    elif product_type.startswith("report_"):
        report_id = product_type[7:]
        report = next((r for r in AVAILABLE_REPORTS if r["id"] == report_id), None)
        if not report:
            return error_response(400, "Unknown report type")
        amount = report["price"]
        title = report["name_ru"] if user.language == Language.RU else report["name_en"]
        description = title
    else:
        return error_response(400, "Invalid product type")

    # Create invoice link using Bot API
    bot = get_bot()
    invoice_link = await bot.create_invoice_link(
        title=title,
        description=description,
        payload=product_type,
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=title, amount=amount)],
    )

    return cors_response(200, {"invoice_url": invoice_link})


async def handle_get_compatibility_history(telegram_id: int) -> dict:
    """Handle GET /api/compatibility - get compatibility check history."""
    user = await db.get_user(telegram_id)
    if not user:
        return error_response(404, "User not found")

    history = await db.get_compatibility_history(telegram_id)
    return cors_response(200, {"compatibility": history})


async def handle_get_compatibility_result(telegram_id: int, result_id: str) -> dict:
    """Handle GET /api/compatibility/{result_id} - get specific result."""
    user = await db.get_user(telegram_id)
    if not user:
        return error_response(404, "User not found")

    result = await db.get_compatibility_result(telegram_id, result_id)
    if not result:
        return error_response(404, "Result not found")

    return cors_response(200, result)


async def handle_create_compatibility(telegram_id: int, body: dict) -> dict:
    """Handle POST /api/compatibility - create new compatibility check from Mini App."""
    user = await db.get_user(telegram_id)
    if not user or not user.is_onboarded():
        return error_response(400, "User not onboarded")

    # Check limit for free users
    if not user.is_premium() and not user.can_check_compatibility():
        return error_response(403, "Limit reached")

    partner_date_str = body.get("partner_date")
    if not partner_date_str:
        return error_response(400, "Missing partner_date")

    partner_date = date.fromisoformat(partner_date_str)

    # Increment counter
    if not user.is_premium():
        await db.increment_compatibility_this_week(user)

    # Calculate compatibility
    scores = calculate_compatibility(user.birth_date, partner_date)

    # Save result
    result_id = await db.save_compatibility_result(telegram_id, partner_date, scores)

    return cors_response(200, {"result_id": result_id, "scores": scores})


async def handle_compatibility_interpret(telegram_id: int, result_id: str) -> dict:
    """Handle POST /api/compatibility/{result_id}/interpret - generate AI interpretation."""
    user = await db.get_user(telegram_id)
    if not user or not user.is_onboarded():
        return error_response(400, "User not onboarded")

    result = await db.get_compatibility_result(telegram_id, result_id)
    if not result:
        return error_response(404, "Result not found")

    # Return cached interpretation if exists
    if result.get("ai_interpretation"):
        return cors_response(200, {"interpretation": result["ai_interpretation"]})

    # Generate new interpretation
    profile = get_full_profile(user.name, user.birth_date)
    partner_date = date.fromisoformat(result["partner_date"])

    interpretation = await ai_service.generate_compatibility_analysis(
        user, profile, result["scores"], partner_date
    )

    # Cache interpretation
    await db.update_compatibility_interpretation(telegram_id, result_id, interpretation)

    return cors_response(200, {"interpretation": interpretation})


async def handle_delete_compatibility(telegram_id: int, result_id: str) -> dict:
    """Handle DELETE /api/compatibility/{result_id}."""
    user = await db.get_user(telegram_id)
    if not user:
        return error_response(404, "User not found")

    await db.delete_compatibility_result(telegram_id, result_id)
    return cors_response(200, {"success": True})


async def handle_generate_report(telegram_id: int, report_id: str, body: dict) -> dict:
    """Handle POST /api/reports/{report_id}/generate - generate report from Mini App."""
    user = await db.get_user(telegram_id)
    if not user or not user.is_onboarded():
        return error_response(400, "User not onboarded")

    # Find report metadata
    report_meta = next((r for r in AVAILABLE_REPORTS if r["id"] == report_id), None)
    if not report_meta:
        return error_response(404, "Unknown report type")

    # Check access
    is_pro = user.subscription_type.value == "pro" and user.is_premium()
    has_report = report_id in user.purchased_reports

    if not is_pro and not has_report:
        return error_response(403, "Report not purchased")

    context = body.get("context", {})

    # Check if already generating
    if await db.is_report_generating(telegram_id, report_id):
        return cors_response(200, {"status": "generating"})

    await db.set_report_generating(telegram_id, report_id)

    # Get profile
    profile = get_full_profile(user.name, user.birth_date)

    # Generate based on type
    content = None
    if report_id == "full_portrait":
        content = await ai_service.generate_full_portrait_report(user, profile)
    elif report_id == "financial_code":
        content = await ai_service.generate_financial_code_report(user, profile)
    elif report_id == "year_forecast":
        year = context.get("year", datetime.now().year)
        content = await ai_service.generate_year_forecast_report(user, profile, year)
    elif report_id == "date_calendar":
        month = context.get("month", datetime.now().month)
        year = context.get("year", datetime.now().year)
        content = await ai_service.generate_date_calendar_report(user, profile, month, year)
    elif report_id == "name_selection":
        content = await ai_service.generate_name_selection_report(user, profile, context)
    elif report_id == "compatibility_pro":
        content = await ai_service.generate_compatibility_pro_report(user, profile, context)
    else:
        await db.clear_report_generating(telegram_id, report_id)
        return error_response(400, "Unknown report type")

    # Save report
    is_multi = report_meta.get("multi_instance", False)
    instance_id = None

    if is_multi:
        instance_id = await db.save_report_instance(telegram_id, report_id, content, context)
    else:
        await db.save_report(telegram_id, report_id, content)

    # Mark as purchased if not already
    if report_id not in user.purchased_reports:
        await db.add_purchased_report(user, report_id)

    await db.clear_report_generating(telegram_id, report_id)

    return cors_response(
        200, {"status": "completed", "instance_id": instance_id, "content": content}
    )


async def handle_get_profile_interpretation(telegram_id: int) -> dict:
    """Handle GET /api/user/interpretation - get or generate profile AI interpretation."""
    user = await db.get_user(telegram_id)
    if not user or not user.is_onboarded():
        return error_response(400, "User not onboarded")

    # Check if interpretation is cached in reports table
    cached = await db.get_report(telegram_id, "profile_interpretation")
    if cached:
        return cors_response(200, {"interpretation": cached})

    # Generate new interpretation
    profile = get_full_profile(user.name, user.birth_date)
    interpretation = await ai_service.generate_profile_interpretation(user, profile)

    # Cache it
    await db.save_report(telegram_id, "profile_interpretation", interpretation)

    return cors_response(200, {"interpretation": interpretation})


async def api_handler(event: dict) -> dict:
    """Main API handler for Mini App requests."""
    # Handle OPTIONS for CORS preflight
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return cors_response(200, None)

    # Get request details
    http_context = event.get("requestContext", {}).get("http", {})
    method = http_context.get("method", "GET")
    path = http_context.get("path", "")

    # Validate initData from header
    headers = event.get("headers", {})
    init_data = headers.get("x-telegram-init-data") or headers.get("X-Telegram-Init-Data")

    if not init_data:
        return error_response(401, "Missing initData")

    tg_user = validate_init_data(init_data)
    if not tg_user:
        return error_response(401, "Invalid initData")

    telegram_id = tg_user.get("id")
    if not telegram_id:
        return error_response(401, "Missing user ID")

    # Parse body for POST/PUT requests
    body = {}
    if event.get("body"):
        body = json.loads(event["body"])

    # Route requests (use endswith to handle stage prefix like /prod/api/...)
    if path.endswith("/api/user") and method == "GET":
        return await handle_get_user(telegram_id)
    elif path.endswith("/api/user/settings") and method == "PUT":
        return await handle_update_settings(telegram_id, body)
    elif path.endswith("/api/user/interpretation") and method == "GET":
        return await handle_get_profile_interpretation(telegram_id)
    elif path.endswith("/api/payments") and method == "GET":
        return await handle_get_payments(telegram_id)
    elif path.endswith("/api/compatibility") and method == "GET":
        return await handle_get_compatibility_history(telegram_id)
    elif path.endswith("/api/compatibility") and method == "POST":
        return await handle_create_compatibility(telegram_id, body)
    elif "/api/compatibility/" in path:
        # Parse path: /api/compatibility/{result_id} or /api/compatibility/{result_id}/interpret
        path_after = path.split("/api/compatibility/")[-1]
        if path_after.endswith("/interpret") and method == "POST":
            result_id = path_after.replace("/interpret", "")
            return await handle_compatibility_interpret(telegram_id, result_id)
        else:
            result_id = path_after.split("/")[0]
            if method == "GET":
                return await handle_get_compatibility_result(telegram_id, result_id)
            elif method == "DELETE":
                return await handle_delete_compatibility(telegram_id, result_id)
            else:
                return error_response(405, "Method not allowed")
    elif path.endswith("/api/reports") and method == "GET":
        return await handle_get_reports(telegram_id)
    elif "/api/reports/" in path:
        # Parse: /api/reports/{id}, /api/reports/{id}/{instance}, /api/reports/{id}/generate
        path_parts = path.split("/api/reports/")[-1].split("/")
        report_id = path_parts[0] if path_parts else None

        # Check for /generate endpoint
        if len(path_parts) > 1 and path_parts[1] == "generate" and method == "POST":
            return await handle_generate_report(telegram_id, report_id, body)

        instance_id = path_parts[1] if len(path_parts) > 1 and path_parts[1] else None

        if method == "GET":
            return await handle_get_report_content(telegram_id, report_id, instance_id)
        elif method == "DELETE" and instance_id:
            return await handle_delete_report_instance(telegram_id, report_id, instance_id)
        else:
            return error_response(405, "Method not allowed")
    elif path.endswith("/api/invoice") and method == "POST":
        return await handle_create_invoice(telegram_id, body)
    else:
        return error_response(404, "Not found")
