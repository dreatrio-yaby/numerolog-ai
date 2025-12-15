"""AI service for generating numerology interpretations."""

from typing import Optional

from openai import AsyncOpenAI

from src.config import get_settings
from src.knowledge.numbers import (
    LIFE_PATH_MEANINGS,
    get_life_path_meaning,
    get_matrix_meaning,
    get_personal_year_meaning,
)
from src.models.user import NumerologyProfile, User

settings = get_settings()

# System prompts
SYSTEM_PROMPT_RU = """Ты — дружелюбный AI-нумеролог. Твоя задача — помогать людям понять себя через числа.

Правила общения:
- Говори просто и понятно, без сложной эзотерической терминологии
- Будь дружелюбным, как умный друг, а не формальный консультант
- Используй "ты", а не "вы"
- Избегай категоричности: "это может означать..." вместо "это значит..."
- Давай практические советы, а не просто описания
- Не противоречь базовым значениям чисел в нумерологии
- Используй эмодзи умеренно (✨ 🔮 💫)
- Отвечай кратко, но содержательно (3-5 абзацев максимум)

Ты знаешь все основные нумерологические системы: пифагорейскую, каббалистическую и ведическую.
Твоя главная цель — помочь человеку лучше понять себя и свой путь."""

SYSTEM_PROMPT_EN = """You are a friendly AI numerologist. Your task is to help people understand themselves through numbers.

Communication rules:
- Speak simply and clearly, without complex esoteric terminology
- Be friendly, like a smart friend, not a formal consultant
- Use casual language
- Avoid being categorical: "this may mean..." instead of "this means..."
- Give practical advice, not just descriptions
- Don't contradict basic numerology meanings
- Use emojis moderately (✨ 🔮 💫)
- Keep answers concise but meaningful (3-5 paragraphs max)

You know all major numerology systems: Pythagorean, Kabbalistic, and Vedic.
Your main goal is to help people better understand themselves and their path."""


class AIService:
    """AI service for generating numerology content."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def _get_system_prompt(self, lang: str) -> str:
        """Get system prompt for language."""
        return SYSTEM_PROMPT_RU if lang == "ru" else SYSTEM_PROMPT_EN

    async def generate_profile_interpretation(
        self,
        user: User,
        profile: NumerologyProfile,
    ) -> str:
        """Generate personalized interpretation of user's numerology profile."""
        lang = user.language.value

        # Build context from knowledge base
        life_path_info = get_life_path_meaning(profile.life_path, lang)
        personal_year_info = get_personal_year_meaning(profile.personal_year, lang)

        # Build matrix summary
        matrix_summary = []
        for pos, count in profile.matrix.items():
            meaning = get_matrix_meaning(pos, count, lang)
            if meaning:
                matrix_summary.append(f"{meaning['name']}: {meaning['interpretation']}")

        if lang == "ru":
            prompt = f"""Создай краткий персональный нумерологический портрет для {user.name}.

Данные:
- Дата рождения: {user.birth_date}
- Число Судьбы (Life Path): {profile.life_path} — "{life_path_info['name']}"
- Число Души: {profile.soul_number}
- Число Имени: {profile.expression_number}
- Персональный год: {profile.personal_year}
- Персональный день: {profile.personal_day}

Характеристика числа {profile.life_path}:
{life_path_info['description']}

Персональный год {profile.personal_year}:
{personal_year_info}

Матрица Пифагора:
{chr(10).join(matrix_summary[:5])}

Напиши дружелюбный, персонализированный анализ на 3-4 абзаца.
Обращайся к {user.name} на "ты". Дай практический совет на текущий период."""
        else:
            prompt = f"""Create a brief personal numerology profile for {user.name}.

Data:
- Birth date: {user.birth_date}
- Life Path Number: {profile.life_path} — "{life_path_info['name']}"
- Soul Number: {profile.soul_number}
- Expression Number: {profile.expression_number}
- Personal Year: {profile.personal_year}
- Personal Day: {profile.personal_day}

Life Path {profile.life_path} characteristics:
{life_path_info['description']}

Personal Year {profile.personal_year}:
{personal_year_info}

Pythagoras Matrix:
{chr(10).join(matrix_summary[:5])}

Write a friendly, personalized analysis in 3-4 paragraphs.
Address {user.name} casually. Give practical advice for the current period."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt(lang)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content

    async def answer_question(
        self,
        user: User,
        profile: NumerologyProfile,
        question: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> str:
        """Answer user's question using their numerology profile context."""
        lang = user.language.value

        # Build context
        life_path_info = get_life_path_meaning(profile.life_path, lang)

        if lang == "ru":
            context = f"""Контекст пользователя {user.name}:
- Число Судьбы: {profile.life_path} ({life_path_info['name']})
- Число Души: {profile.soul_number}
- Персональный год: {profile.personal_year}
- Персональный месяц: {profile.personal_month}
- Персональный день: {profile.personal_day}

{life_path_info['short']}

Вопрос пользователя: {question}

Ответь с учётом нумерологического профиля. Дай практический совет."""
        else:
            context = f"""User context for {user.name}:
- Life Path: {profile.life_path} ({life_path_info['name']})
- Soul Number: {profile.soul_number}
- Personal Year: {profile.personal_year}
- Personal Month: {profile.personal_month}
- Personal Day: {profile.personal_day}

{life_path_info['short']}

User's question: {question}

Answer considering the numerology profile. Give practical advice."""

        messages = [{"role": "system", "content": self._get_system_prompt(lang)}]

        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": context})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
        )

        return response.choices[0].message.content

    async def generate_daily_forecast(
        self,
        user: User,
        profile: NumerologyProfile,
    ) -> str:
        """Generate daily forecast based on personal day number."""
        lang = user.language.value

        if lang == "ru":
            prompt = f"""Сгенерируй краткий прогноз на сегодня для {user.name}.

Персональный день: {profile.personal_day}
Персональный месяц: {profile.personal_month}
Персональный год: {profile.personal_year}
Число Судьбы: {profile.life_path}

Напиши 3-4 предложения: общая энергия дня, что стоит делать, чего избегать.
Будь конкретным и практичным."""
        else:
            prompt = f"""Generate a brief daily forecast for {user.name}.

Personal Day: {profile.personal_day}
Personal Month: {profile.personal_month}
Personal Year: {profile.personal_year}
Life Path: {profile.life_path}

Write 3-4 sentences: overall energy of the day, what to do, what to avoid.
Be specific and practical."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt(lang)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.8,
        )

        return response.choices[0].message.content

    async def generate_compatibility_analysis(
        self,
        compatibility_data: dict,
        lang: str = "ru",
    ) -> str:
        """Generate compatibility analysis between two people."""
        if lang == "ru":
            prompt = f"""Проанализируй совместимость двух людей.

Данные:
- Общая совместимость: {compatibility_data['overall_score']}%
- Совместимость по Числу Судьбы: {compatibility_data['life_path_score']}%
- Совместимость по Числу Души: {compatibility_data['soul_score']}%

Человек 1: Число Судьбы {compatibility_data['person1']['life_path']}, Число Души {compatibility_data['person1']['soul']}
Человек 2: Число Судьбы {compatibility_data['person2']['life_path']}, Число Души {compatibility_data['person2']['soul']}

Напиши краткий анализ (2-3 абзаца):
1. Сильные стороны этой пары
2. Возможные сложности
3. Совет для гармоничных отношений"""
        else:
            prompt = f"""Analyze compatibility between two people.

Data:
- Overall compatibility: {compatibility_data['overall_score']}%
- Life Path compatibility: {compatibility_data['life_path_score']}%
- Soul compatibility: {compatibility_data['soul_score']}%

Person 1: Life Path {compatibility_data['person1']['life_path']}, Soul {compatibility_data['person1']['soul']}
Person 2: Life Path {compatibility_data['person2']['life_path']}, Soul {compatibility_data['person2']['soul']}

Write a brief analysis (2-3 paragraphs):
1. Strengths of this pair
2. Potential challenges
3. Advice for harmonious relationships"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt(lang)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=600,
            temperature=0.7,
        )

        return response.choices[0].message.content


# Global instance
ai_service = AIService()
