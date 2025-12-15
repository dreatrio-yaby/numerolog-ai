# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"  # includes pytest, ruff

# Run locally (polling mode)
python -m src.lambda_handler

# Set webhook manually
python -m src.lambda_handler set_webhook <URL>

# Lint
ruff check src/
ruff format src/

# Test
pytest
pytest tests/test_file.py::test_name -v  # single test

# Deploy to AWS (via GitHub Actions - automatic on push to main)
# Manual deploy:
./scripts/deploy.sh
./scripts/set_webhook.sh
```

## Deployment

Deployment is automated via GitHub Actions (`.github/workflows/deploy.yml`):
- Triggers on push to `main` branch
- Can be triggered manually via Actions tab
- Automatically sets Telegram webhook after deploy

**Required GitHub Secrets:**
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`

## Architecture

**Serverless Telegram Bot** running on AWS Lambda with webhook pattern.

### Request Flow
1. Telegram sends update to API Gateway → `lambda_handler.handler()`
2. aiogram `Dispatcher.feed_update()` routes to appropriate handler in `src/handlers/bot.py`
3. Handlers use services (`ai`, `database`, `numerology`) and respond via aiogram `Bot`

### Key Components

- **`src/handlers/bot.py`**: All Telegram handlers. Uses aiogram FSM for multi-step flows (onboarding, compatibility). Global `router` is included in dispatcher via `dp.include_router(router)`.

- **`src/services/`**:
  - `ai.py` - OpenAI wrapper with Russian/English system prompts. Global `ai_service` instance.
  - `database.py` - DynamoDB CRUD. Global `db` instance. Single-table design with `PK` pattern (`USER#<id>`, `MSG#<ts>`, `REPORT#<type>`).
  - `numerology.py` - Pure calculation functions for life path, soul number, matrix, compatibility. No side effects.

- **`src/knowledge/numbers.py`**: Static dictionaries with numerology meanings (RU/EN). Referenced by AI service to build prompts.

- **`src/models/user.py`**: Pydantic models. `User` has business logic methods: `can_ask_question()`, `is_premium()`, `has_report()`.

### Monetization Logic
- FREE: 3 questions/day, 2 compatibility/week
- LITE/PRO: unlimited (30-day subscription via Telegram Stars)
- Premium reports: purchasable separately on any tier
- Referral bonuses add to `questions_bonus` field

### Localization
All user-facing text is in `TEXTS` dict in `bot.py` keyed by language code. User's `language` field determines which texts to use.

## Environment Variables

Required in `.env` or Lambda environment:
- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `DYNAMODB_TABLE_USERS`, `DYNAMODB_TABLE_CONVERSATIONS`, `DYNAMODB_TABLE_REPORTS`
