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

# Deploy to AWS - ONLY via GitHub Actions (automatic on push to main)
# DO NOT use manual deploy scripts
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

**Infrastructure:** `infrastructure/template.yaml` (SAM CloudFormation) defines:
- 3 Lambda functions: `WebhookFunction`, `NotificationsFunction`, `ApiFunction`
- HTTP API Gateway with CORS for Mini App origin
- 3 DynamoDB tables: Users, Conversations, Reports

## Architecture

**Serverless Telegram Bot** running on AWS Lambda with webhook pattern.

### Bot Commands
- `/start` — Onboarding / restart
- `/profile` — Numerology portrait
- `/today` — Daily forecast
- `/compatibility` — Compatibility analysis
- `/buy` — Purchase subscription
- `/invite` — Referral program
- `/report` — Premium reports
- `/help` — Help

### Request Flow (Bot)
1. Telegram sends update to API Gateway → `lambda_handler.handler()`
2. aiogram `Dispatcher.feed_update()` routes to appropriate handler in `src/handlers/bot.py`
3. Handlers use services (`ai`, `database`, `numerology`) and respond via aiogram `Bot`

### Request Flow (Mini App API)
1. Mini App sends request to API Gateway → `api_handler.handler()`
2. `src/handlers/api.py` validates Telegram initData and routes to endpoint handlers
3. Returns JSON response with CORS headers for `https://dreatrio-yaby.github.io`

### Key Components

- **`src/handlers/bot.py`**: All Telegram handlers. Uses aiogram FSM for multi-step flows. Global `router` is included in dispatcher via `dp.include_router(router)`. FSM states: `OnboardingStates` (name → birth_date), `CompatibilityStates` (partner birth_date), `ReportInputStates` (name_purpose, child_gender, partner_name, partner_birthdate).

- **`src/handlers/api.py`**: REST API for Mini App. Endpoints: `GET /api/user`, `PUT /api/user/settings`, `GET /api/payments`, `GET /api/reports`, `GET /api/reports/{id}`, `POST /api/invoice`. Auth via `X-Telegram-Init-Data` header.

- **`src/services/`**:
  - `ai.py` - OpenAI wrapper with Russian/English system prompts. Global `ai_service` instance.
  - `database.py` - DynamoDB CRUD. Global `db` instance. Key patterns: `PK=USER#<id>` for users, `SK=MSG#<ts>` for messages, `SK=REPORT#<type>` for reports, `SK=PENDING#<id>` for pre-payment data, `SK=LOCK#<id>` for generation locks.
  - `numerology.py` - Pure calculation functions for life path, soul number, matrix, compatibility. No side effects.

- **`src/knowledge/numbers.py`**: Static dictionaries with numerology meanings (RU/EN). Referenced by AI service to build prompts.

- **`src/models/user.py`**: Pydantic models. `User` has business logic methods: `can_ask_question()`, `is_premium()`, `has_report()`, `is_onboarded()`.

- **`src/notifications_handler.py`**: Scheduled Lambda (hourly via CloudWatch) for daily forecast notifications based on user's `notification_time` setting.

### Mini App (webapp/)

Telegram Mini App for settings and profile, hosted on GitHub Pages. Deployed separately via `.github/workflows/deploy-webapp.yml`.

- **`webapp/js/telegram.js`**: Telegram WebApp SDK wrapper
- **`webapp/js/api.js`**: API client with initData auth
- **`webapp/js/app.js`**: Main app logic, handles both onboarded and non-onboarded states
- **`webapp/js/report.js`**: Report viewing page logic
- **`webapp/i18n/`**: Translation files (ru.json, en.json)

User is created at `/start` (before full onboarding). Mini App checks `is_onboarded` flag to show appropriate UI.

### Monetization Logic
- FREE: 3 questions/day, 2 compatibility/week
- LITE/PRO: unlimited (30-day subscription via Telegram Stars)
- Premium reports: purchasable separately on any tier
- Referral bonuses add to `questions_bonus` field

### Localization
- Bot: `TEXTS` dict in `bot.py` keyed by language code
- Mini App: JSON files in `webapp/i18n/`
- User's `language` field determines which texts to use

## Error Handling

**ВАЖНО:** Не используй try-except/try-catch конструкции. Ошибки должны пробрасываться с полным stack trace для упрощения отладки. Это временное правило на период активной разработки.

## Git Workflow

После завершения реализации задачи всегда предлагай пользователю сделать коммит (или несколько коммитов, если изменения логически разделяемы) и пуш в репозиторий, а также обновление CLAUDE.md при необходимости.

## Environment Variables

Required in `.env` or Lambda environment:
- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `DYNAMODB_TABLE_USERS`, `DYNAMODB_TABLE_CONVERSATIONS`, `DYNAMODB_TABLE_REPORTS`
