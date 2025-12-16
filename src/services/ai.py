"""AI service for generating numerology interpretations."""

from typing import Optional

from openai import AsyncOpenAI

from src.config import get_settings
from src.knowledge.numbers import (
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
- Число Судьбы (Life Path): {profile.life_path} — "{life_path_info["name"]}"
- Число Души: {profile.soul_number}
- Число Имени: {profile.expression_number}
- Персональный год: {profile.personal_year}
- Персональный день: {profile.personal_day}

Характеристика числа {profile.life_path}:
{life_path_info["description"]}

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
- Life Path Number: {profile.life_path} — "{life_path_info["name"]}"
- Soul Number: {profile.soul_number}
- Expression Number: {profile.expression_number}
- Personal Year: {profile.personal_year}
- Personal Day: {profile.personal_day}

Life Path {profile.life_path} characteristics:
{life_path_info["description"]}

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
- Число Судьбы: {profile.life_path} ({life_path_info["name"]})
- Число Души: {profile.soul_number}
- Персональный год: {profile.personal_year}
- Персональный месяц: {profile.personal_month}
- Персональный день: {profile.personal_day}

{life_path_info["short"]}

Вопрос пользователя: {question}

Ответь с учётом нумерологического профиля. Дай практический совет."""
        else:
            context = f"""User context for {user.name}:
- Life Path: {profile.life_path} ({life_path_info["name"]})
- Soul Number: {profile.soul_number}
- Personal Year: {profile.personal_year}
- Personal Month: {profile.personal_month}
- Personal Day: {profile.personal_day}

{life_path_info["short"]}

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
- Общая совместимость: {compatibility_data["overall_score"]}%
- Совместимость по Числу Судьбы: {compatibility_data["life_path_score"]}%
- Совместимость по Числу Души: {compatibility_data["soul_score"]}%

Человек 1: Число Судьбы {compatibility_data["person1"]["life_path"]}, Число Души {compatibility_data["person1"]["soul"]}
Человек 2: Число Судьбы {compatibility_data["person2"]["life_path"]}, Число Души {compatibility_data["person2"]["soul"]}

Напиши краткий анализ (2-3 абзаца):
1. Сильные стороны этой пары
2. Возможные сложности
3. Совет для гармоничных отношений"""
        else:
            prompt = f"""Analyze compatibility between two people.

Data:
- Overall compatibility: {compatibility_data["overall_score"]}%
- Life Path compatibility: {compatibility_data["life_path_score"]}%
- Soul compatibility: {compatibility_data["soul_score"]}%

Person 1: Life Path {compatibility_data["person1"]["life_path"]}, Soul {compatibility_data["person1"]["soul"]}
Person 2: Life Path {compatibility_data["person2"]["life_path"]}, Soul {compatibility_data["person2"]["soul"]}

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

    # ===== PREMIUM REPORT GENERATION METHODS =====

    async def generate_full_portrait_report(
        self,
        user: User,
        profile: NumerologyProfile,
    ) -> str:
        """Generate comprehensive full portrait report (premium)."""
        lang = user.language.value
        life_path_info = get_life_path_meaning(profile.life_path, lang)
        personal_year_info = get_personal_year_meaning(profile.personal_year, lang)

        # Build matrix analysis
        matrix_analysis = []
        for pos in range(1, 10):
            count = profile.matrix.get(pos, 0)
            meaning = get_matrix_meaning(pos, count, lang)
            if meaning:
                matrix_analysis.append(
                    f"• Позиция {pos} ({count} цифр): {meaning['name']} — {meaning['interpretation']}"
                )

        if lang == "ru":
            prompt = f"""Создай ПОЛНЫЙ НУМЕРОЛОГИЧЕСКИЙ ПОРТРЕТ для {user.name}.

Это премиум-отчёт, который пользователь оплатил. Он должен быть детальным, глубоким и практичным.

ДАННЫЕ КЛИЕНТА:
• Имя: {user.name}
• Дата рождения: {user.birth_date}
• Число Судьбы (Life Path): {profile.life_path} — "{life_path_info["name"]}"
• Число Души: {profile.soul_number}
• Число Выражения (Имени): {profile.expression_number}
• Число Личности: {profile.personality_number}
• Число Дня Рождения: {profile.birthday_number}
• Число Зрелости: {profile.maturity_number}
• Персональный год: {profile.personal_year}

ХАРАКТЕРИСТИКА ЧИСЛА СУДЬБЫ {profile.life_path}:
{life_path_info["description"]}

ПЕРСОНАЛЬНЫЙ ГОД {profile.personal_year}:
{personal_year_info}

МАТРИЦА ПИФАГОРА:
{chr(10).join(matrix_analysis)}

СТРУКТУРА ОТЧЁТА (создай каждый раздел по 2-3 абзаца):

1. 🌟 ТВОЯ МИССИЯ И ЖИЗНЕННЫЙ ПУТЬ
   - Глубокий анализ числа Судьбы {profile.life_path}
   - Как это число влияет на твой жизненный путь
   - Главные уроки и возможности

2. 💫 ВНУТРЕННИЙ МИР И ЖЕЛАНИЯ ДУШИ
   - Анализ числа Души {profile.soul_number}
   - Скрытые мотивации и истинные желания
   - Что приносит настоящее счастье

3. 🎭 КАК ТЕБЯ ВИДЯТ ДРУГИЕ
   - Число Личности {profile.personality_number}
   - Первое впечатление
   - Как использовать это знание

4. 💼 ТАЛАНТЫ И ПРОФЕССИОНАЛЬНАЯ РЕАЛИЗАЦИЯ
   - Число Выражения {profile.expression_number}
   - Природные способности
   - Идеальные сферы деятельности (3-5 примеров)

5. 🔮 СИЛЬНЫЕ СТОРОНЫ ПО МАТРИЦЕ
   - Анализ сильных позиций в матрице
   - Как использовать эти качества

6. ⚠️ ЗОНЫ РОСТА
   - Слабые позиции в матрице
   - Рекомендации по развитию

7. 📅 ТЕКУЩИЙ ПЕРИОД
   - Персональный год {profile.personal_year}
   - Конкретные рекомендации на этот год

8. 🎯 ПРАКТИЧЕСКИЕ СОВЕТЫ
   - 5-7 конкретных рекомендаций для {user.name}

Пиши тепло и дружелюбно, на "ты". Используй имя {user.name}. Избегай общих фраз — давай конкретику на основе чисел."""
        else:
            prompt = f"""Create a FULL NUMEROLOGY PORTRAIT for {user.name}.

This is a premium report that the user paid for. It should be detailed, deep, and practical.

CLIENT DATA:
• Name: {user.name}
• Birth date: {user.birth_date}
• Life Path Number: {profile.life_path} — "{life_path_info["name"]}"
• Soul Number: {profile.soul_number}
• Expression Number: {profile.expression_number}
• Personality Number: {profile.personality_number}
• Birthday Number: {profile.birthday_number}
• Maturity Number: {profile.maturity_number}
• Personal Year: {profile.personal_year}

LIFE PATH {profile.life_path} CHARACTERISTICS:
{life_path_info["description"]}

PERSONAL YEAR {profile.personal_year}:
{personal_year_info}

PYTHAGORAS MATRIX:
{chr(10).join(matrix_analysis)}

REPORT STRUCTURE (write 2-3 paragraphs for each section):

1. 🌟 YOUR MISSION AND LIFE PATH
2. 💫 INNER WORLD AND SOUL DESIRES
3. 🎭 HOW OTHERS SEE YOU
4. 💼 TALENTS AND CAREER
5. 🔮 STRENGTHS FROM MATRIX
6. ⚠️ GROWTH AREAS
7. 📅 CURRENT PERIOD
8. 🎯 PRACTICAL ADVICE (5-7 specific recommendations)

Write warmly and friendly. Use {user.name}'s name. Be specific based on the numbers."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt(lang)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
            temperature=0.7,
        )
        return response.choices[0].message.content

    async def generate_financial_code_report(
        self,
        user: User,
        profile: NumerologyProfile,
    ) -> str:
        """Generate financial code and money attraction report (premium)."""
        lang = user.language.value
        life_path_info = get_life_path_meaning(profile.life_path, lang)

        # Extract finance-related matrix positions
        work_meaning = get_matrix_meaning(6, profile.matrix.get(6, 0), lang)
        luck_meaning = get_matrix_meaning(7, profile.matrix.get(7, 0), lang)
        duty_meaning = get_matrix_meaning(8, profile.matrix.get(8, 0), lang)

        if lang == "ru":
            prompt = f"""Создай ОТЧЁТ "ФИНАНСОВЫЙ КОД" для {user.name}.

Это премиум-отчёт о деньгах, карьере и материальном благополучии.

ДАННЫЕ КЛИЕНТА:
• Число Судьбы: {profile.life_path} — {life_path_info["name"]}
• Число Выражения: {profile.expression_number}
• Персональный год: {profile.personal_year}
• День рождения: {profile.birthday_number}

ПОЗИЦИИ МАТРИЦЫ, СВЯЗАННЫЕ С ФИНАНСАМИ:
• Труд (6): {work_meaning["interpretation"] if work_meaning else "нет цифр"}
• Удача (7): {luck_meaning["interpretation"] if luck_meaning else "нет цифр"}
• Долг/Ответственность (8): {duty_meaning["interpretation"] if duty_meaning else "нет цифр"}

СТРУКТУРА ОТЧЁТА:

1. 💰 ТВОЙ ДЕНЕЖНЫЙ АРХЕТИП
   - Как число Судьбы {profile.life_path} влияет на отношения с деньгами
   - Природный стиль заработка
   - Твоя денежная "суперсила"

2. 📈 СИЛЬНЫЕ ФИНАНСОВЫЕ КАЧЕСТВА
   - Что помогает тебе зарабатывать
   - Как усилить эти качества
   - Примеры успешного применения

3. ⚠️ ФИНАНСОВЫЕ ЛОВУШКИ
   - Типичные денежные ошибки для числа {profile.life_path}
   - Как их избежать
   - Признаки того, что ты в ловушке

4. 💼 ИДЕАЛЬНЫЕ ИСТОЧНИКИ ДОХОДА
   - 5-7 конкретных направлений для {user.name}
   - Активный доход: подходящие профессии/бизнесы
   - Пассивный доход: что подойдёт именно тебе

5. 🗓️ ФИНАНСОВЫЙ ПРОГНОЗ НА ГОД
   - Персональный год {profile.personal_year} и деньги
   - Лучшие месяцы для крупных решений
   - Когда копить, когда инвестировать

6. 🎯 ДЕНЕЖНАЯ СТРАТЕГИЯ
   - Конкретный план действий на ближайшие 3 месяца
   - Привычки богатства для {user.name}
   - Аффирмации и настройки для твоего числа

Будь максимально конкретен. Это платный отчёт — дай реальную практическую ценность!"""
        else:
            prompt = f"""Create a "FINANCIAL CODE" REPORT for {user.name}.

This is a premium report about money, career, and material prosperity.

CLIENT DATA:
• Life Path: {profile.life_path} — {life_path_info["name"]}
• Expression Number: {profile.expression_number}
• Personal Year: {profile.personal_year}
• Birthday Number: {profile.birthday_number}

MATRIX POSITIONS RELATED TO FINANCES:
• Work (6): {work_meaning["interpretation"] if work_meaning else "no digits"}
• Luck (7): {luck_meaning["interpretation"] if luck_meaning else "no digits"}
• Duty/Responsibility (8): {duty_meaning["interpretation"] if duty_meaning else "no digits"}

REPORT STRUCTURE:

1. 💰 YOUR MONEY ARCHETYPE
2. 📈 FINANCIAL STRENGTHS
3. ⚠️ MONEY TRAPS TO AVOID
4. 💼 IDEAL INCOME SOURCES (5-7 specific options)
5. 🗓️ FINANCIAL FORECAST FOR THE YEAR
6. 🎯 MONEY STRATEGY (3-month action plan)

Be very specific. This is a paid report — deliver real practical value!"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt(lang)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2500,
            temperature=0.7,
        )
        return response.choices[0].message.content

    async def generate_date_calendar_report(
        self,
        user: User,
        profile: NumerologyProfile,
        month: int = None,
        year: int = None,
    ) -> str:
        """Generate favorable dates calendar report (premium).

        Args:
            month: Target month (1-12). Defaults to current month.
            year: Target year. Defaults to current year.
        """
        from datetime import datetime

        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        lang = user.language.value
        life_path_info = get_life_path_meaning(profile.life_path, lang)

        # Calculate favorable numbers for this life path
        favorable_nums = self._get_favorable_numbers(profile.life_path)

        if lang == "ru":
            prompt = f"""Создай КАЛЕНДАРЬ БЛАГОПРИЯТНЫХ ДАТ для {user.name}.

ДАННЫЕ:
• Число Судьбы: {profile.life_path} — {life_path_info["name"]}
• Персональный год: {profile.personal_year}
• Персональный месяц: {profile.personal_month}

ГАРМОНИЧНЫЕ ЧИСЛА ДЛЯ СУДЬБЫ {profile.life_path}: {", ".join(map(str, favorable_nums))}

СТРУКТУРА ОТЧЁТА:

1. 📅 УНИВЕРСАЛЬНЫЕ БЛАГОПРИЯТНЫЕ ДНИ
   - Какие числа дней (1-31) гармонируют с числом Судьбы {profile.life_path}
   - Почему именно эти числа работают для тебя
   - Как усилить энергию этих дней

2. 💼 ДНИ ДЛЯ БИЗНЕСА И КАРЬЕРЫ
   - Лучшие даты для: начала проектов, переговоров, собеседований, подписания договоров
   - Конкретные рекомендации на ближайшие 3 месяца
   - Числа, которых стоит избегать для деловых вопросов

3. 💕 ДНИ ДЛЯ ЛЮБВИ И ОТНОШЕНИЙ
   - Лучшие даты для: первых свиданий, важных разговоров, предложений
   - Романтические дни на ближайший квартал
   - Когда лучше НЕ выяснять отношения

4. 💰 ДНИ ДЛЯ ФИНАНСОВ
   - Крупные покупки: когда совершать
   - Инвестиции: благоприятные даты
   - Когда лучше копить, а не тратить

5. ✈️ ДНИ ДЛЯ ПУТЕШЕСТВИЙ И ПЕРЕМЕН
   - Начало поездок: лучшие даты
   - Переезды, смена работы: когда начинать
   - Неблагоприятные периоды для перемен

6. 🏥 ДНИ ДЛЯ ЗДОРОВЬЯ
   - Лучшие даты для: начала диеты, спорта, лечения
   - Когда организм наиболее восприимчив к изменениям

7. ⚠️ НЕБЛАГОПРИЯТНЫЕ ПЕРИОДЫ
   - Конкретные даты для осторожности
   - Что лучше не делать в эти дни
   - Как минимизировать негативную энергию

Дай КОНКРЕТНЫЕ ДАТЫ на ближайшие 3 месяца с объяснениями. Персональный год {profile.personal_year} влияет на общую энергию года — учитывай это."""
        else:
            prompt = f"""Create a FAVORABLE DATES CALENDAR for {user.name}.

DATA:
• Life Path: {profile.life_path} — {life_path_info["name"]}
• Personal Year: {profile.personal_year}
• Personal Month: {profile.personal_month}

HARMONIOUS NUMBERS FOR LIFE PATH {profile.life_path}: {", ".join(map(str, favorable_nums))}

REPORT STRUCTURE:

1. 📅 UNIVERSAL FAVORABLE DAYS
2. 💼 BUSINESS AND CAREER DAYS
3. 💕 LOVE AND RELATIONSHIPS DAYS
4. 💰 FINANCIAL DAYS
5. ✈️ TRAVEL AND CHANGE DAYS
6. 🏥 HEALTH DAYS
7. ⚠️ UNFAVORABLE PERIODS

Provide SPECIFIC DATES for the next 3 months with explanations."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt(lang)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2500,
            temperature=0.7,
        )
        return response.choices[0].message.content

    def _get_favorable_numbers(self, life_path: int) -> list[int]:
        """Get favorable numbers for a life path number."""
        # Numerology harmony: same number, complementary numbers
        harmonies = {
            1: [1, 2, 3, 5, 9],
            2: [1, 2, 4, 6, 8],
            3: [1, 3, 5, 6, 9],
            4: [2, 4, 6, 7, 8],
            5: [1, 3, 5, 7, 9],
            6: [2, 3, 4, 6, 9],
            7: [4, 5, 7, 8],
            8: [2, 4, 6, 8],
            9: [1, 3, 5, 6, 9],
            11: [1, 2, 4, 6, 11],
            22: [2, 4, 6, 8, 22],
        }
        return harmonies.get(life_path, [life_path])

    async def generate_year_forecast_report(
        self,
        user: User,
        profile: NumerologyProfile,
        year: int = None,
    ) -> str:
        """Generate detailed year forecast report (premium).

        Args:
            year: Target year for forecast. Defaults to current year.
        """
        from datetime import datetime

        if year is None:
            year = datetime.now().year

        lang = user.language.value
        life_path_info = get_life_path_meaning(profile.life_path, lang)
        personal_year_info = get_personal_year_meaning(profile.personal_year, lang)

        if lang == "ru":
            prompt = f"""Создай ДЕТАЛЬНЫЙ ПРОГНОЗ НА ГОД для {user.name}.

ДАННЫЕ:
• Число Судьбы: {profile.life_path} — {life_path_info["name"]}
• Персональный год: {profile.personal_year}

ХАРАКТЕРИСТИКА ПЕРСОНАЛЬНОГО ГОДА {profile.personal_year}:
{personal_year_info}

СТРУКТУРА ОТЧЁТА:

1. 🎯 ГЛАВНАЯ ТЕМА ГОДА
   - Общая характеристика персонального года {profile.personal_year}
   - Ключевые возможности этого года
   - Главный урок, который предстоит усвоить

2. 💼 КАРЬЕРА И РАБОТА
   - Тенденции в профессиональной сфере
   - Лучшие периоды для карьерных шагов
   - Конкретные рекомендации по профессиональному росту
   - Стоит ли менять работу/начинать бизнес

3. 💰 ФИНАНСЫ
   - Денежные перспективы года
   - Когда зарабатывать активно, когда копить
   - Крупные траты: да или нет?
   - Инвестиции в этом году

4. 💕 ЛЮБОВЬ И ОТНОШЕНИЯ
   - Прогноз для одиноких: шансы встретить партнёра
   - Прогноз для пар: что ждёт отношения
   - Ключевые периоды для романтики
   - Как улучшить отношения в этом году

5. 🏥 ЗДОРОВЬЕ И ЭНЕРГИЯ
   - На что обратить внимание
   - Периоды восстановления и активности
   - Рекомендации по образу жизни

6. 📆 ПОМЕСЯЧНЫЙ ПРОГНОЗ
   Для каждого месяца (2-3 предложения):
   - Январь: ...
   - Февраль: ...
   - Март: ...
   - Апрель: ...
   - Май: ...
   - Июнь: ...
   - Июль: ...
   - Август: ...
   - Сентябрь: ...
   - Октябрь: ...
   - Ноябрь: ...
   - Декабрь: ...

7. ⚠️ ПРЕДОСТЕРЕЖЕНИЯ
   - Возможные трудности года
   - Как их избежать или минимизировать
   - Периоды повышенной осторожности

8. 🎯 5 ГЛАВНЫХ СОВЕТОВ НА ГОД
   Конкретные, практичные рекомендации для {user.name}

Учитывай влияние числа Судьбы {profile.life_path} на то, как {user.name} проживёт этот персональный год."""
        else:
            prompt = f"""Create a DETAILED YEAR FORECAST for {user.name}.

DATA:
• Life Path: {profile.life_path} — {life_path_info["name"]}
• Personal Year: {profile.personal_year}

PERSONAL YEAR {profile.personal_year} CHARACTERISTICS:
{personal_year_info}

REPORT STRUCTURE:

1. 🎯 MAIN THEME OF THE YEAR
2. 💼 CAREER AND WORK
3. 💰 FINANCES
4. 💕 LOVE AND RELATIONSHIPS
5. 🏥 HEALTH AND ENERGY
6. 📆 MONTH-BY-MONTH FORECAST (all 12 months)
7. ⚠️ WARNINGS
8. 🎯 5 TOP TIPS FOR THE YEAR

Consider how Life Path {profile.life_path} influences how {user.name} will experience this personal year."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt(lang)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
            temperature=0.7,
        )
        return response.choices[0].message.content

    async def generate_name_selection_report(
        self,
        user: User,
        profile: NumerologyProfile,
        context: dict,
    ) -> str:
        """Generate name selection report (premium). Context: purpose, gender (for child)."""
        lang = user.language.value
        purpose = context.get("purpose", "child")  # child, business, self
        gender = context.get("gender")  # male, female (for child)

        if lang == "ru":
            if purpose == "child":
                gender_text = (
                    "мальчика"
                    if gender == "male"
                    else "девочки"
                    if gender == "female"
                    else "ребёнка"
                )
                prompt = f"""Создай ОТЧЁТ ПО ПОДБОРУ ИМЕНИ ДЛЯ {gender_text.upper()}.

ДАННЫЕ РОДИТЕЛЯ ({user.name}):
• Число Судьбы: {profile.life_path}
• Число Выражения: {profile.expression_number}
• Дата рождения: {user.birth_date}

ЗАДАЧА: подобрать имена, которые будут гармонировать с числами родителя и принесут удачу ребёнку.

СТРУКТУРА ОТЧЁТА:

1. 🔢 КАКИЕ ЧИСЛА ИМЕНИ БЛАГОПРИЯТНЫ
   - Какие числа Выражения имени подходят для {gender_text}
   - Как они сочетаются с числом Судьбы родителя {profile.life_path}
   - Объяснение нумерологической гармонии

2. 📝 РЕКОМЕНДУЕМЫЕ ИМЕНА (15-20 вариантов)
   Для каждого имени укажи:
   - Само имя
   - Число Выражения этого имени
   - Почему оно подходит
   - Какие качества даст ребёнку

3. ⭐ ТОП-5 ЛУЧШИХ ИМЁН
   Подробный разбор пяти самых удачных вариантов

4. ⚠️ ИМЕНА, КОТОРЫХ ЛУЧШЕ ИЗБЕГАТЬ
   - Какие числа Выражения не рекомендуются
   - Конкретные примеры неподходящих имён
   - Почему они не гармонируют

5. 💡 КАК ПРОВЕРИТЬ ДРУГИЕ ИМЕНА
   - Краткая инструкция по расчёту числа имени
   - Таблица соответствия букв и цифр

Сделай отчёт максимально полезным для родителя!"""

            elif purpose == "business":
                prompt = f"""Создай ОТЧЁТ ПО ПОДБОРУ НАЗВАНИЯ ДЛЯ БИЗНЕСА.

ДАННЫЕ ВЛАДЕЛЬЦА ({user.name}):
• Число Судьбы: {profile.life_path}
• Число Выражения: {profile.expression_number}

ЗАДАЧА: подобрать название, которое будет резонировать с энергией владельца и привлекать успех.

СТРУКТУРА ОТЧЁТА:

1. 🔢 БЛАГОПРИЯТНЫЕ ЧИСЛА ДЛЯ БИЗНЕСА
   - Какие числа названия привлекают успех
   - Как они сочетаются с твоим числом Судьбы {profile.life_path}
   - Числа для разных типов бизнеса

2. 💼 РЕКОМЕНДАЦИИ ПО НАЗВАНИЮ
   - Какие буквы использовать в начале
   - Оптимальная длина названия
   - Энергетика гласных и согласных

3. 📝 ПРИМЕРЫ УДАЧНЫХ СТРУКТУР
   - 10-15 примеров структур названий
   - Для каждого: число и почему работает

4. ⚠️ ЧЕГО ИЗБЕГАТЬ
   - Неблагоприятные числа для бизнеса
   - Типичные ошибки в названиях
   - Как НЕ надо называть компанию

5. 💡 КАК ПРОВЕРИТЬ НАЗВАНИЕ
   - Инструкция по расчёту числа названия
   - Таблица букв и цифр

Помоги {user.name} создать успешный бренд!"""

            else:  # self (nickname/pseudonym)
                prompt = f"""Создай ОТЧЁТ ПО ПОДБОРУ ПСЕВДОНИМА/НИКА.

ДАННЫЕ ({user.name}):
• Число Судьбы: {profile.life_path}
• Число Выражения: {profile.expression_number}
• Число Личности: {profile.personality_number}

ЗАДАЧА: подобрать псевдоним/ник, который усилит твои сильные стороны и привлечёт нужную энергию.

СТРУКТУРА ОТЧЁТА:

1. 🎭 ТВОЯ НУМЕРОЛОГИЧЕСКАЯ ЛИЧНОСТЬ
   - Анализ текущих чисел
   - Какие качества хочешь усилить
   - Какую энергию привлечь

2. 🔢 ИДЕАЛЬНЫЕ ЧИСЛА ДЛЯ ПСЕВДОНИМА
   - Какие числа Выражения усилят твои таланты
   - Какие привлекут успех в твоей сфере
   - Как сочетать с родным именем

3. 📝 ВАРИАНТЫ ПСЕВДОНИМОВ (15-20)
   Для каждого:
   - Псевдоним
   - Число Выражения
   - Какую энергию несёт
   - Для какой деятельности подходит

4. ⭐ ТОП-5 РЕКОМЕНДАЦИЙ
   Подробный разбор лучших вариантов для {user.name}

5. 💡 КАК СОЗДАТЬ СВОЙ ВАРИАНТ
   - Принципы создания сильного псевдонима
   - Таблица букв и цифр
   - Как тестировать варианты"""

        else:  # English
            if purpose == "child":
                gender_text = (
                    "boy" if gender == "male" else "girl" if gender == "female" else "child"
                )
                prompt = f"""Create a NAME SELECTION REPORT for a {gender_text}.

PARENT DATA ({user.name}):
• Life Path: {profile.life_path}
• Expression: {profile.expression_number}

Provide 15-20 name recommendations with numerology analysis."""
            elif purpose == "business":
                prompt = f"""Create a BUSINESS NAME SELECTION REPORT for {user.name}.

• Life Path: {profile.life_path}
• Expression: {profile.expression_number}

Provide naming guidelines and 10-15 structure examples."""
            else:
                prompt = f"""Create a NICKNAME/PSEUDONYM SELECTION REPORT for {user.name}.

• Life Path: {profile.life_path}
• Expression: {profile.expression_number}

Provide 15-20 pseudonym options with analysis."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt(lang)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2500,
            temperature=0.7,
        )
        return response.choices[0].message.content

    async def generate_compatibility_pro_report(
        self,
        user: User,
        profile: NumerologyProfile,
        partner_data: dict,
    ) -> str:
        """Generate detailed compatibility PRO report (premium)."""
        from datetime import date

        from src.services.numerology import calculate_compatibility, get_full_profile

        lang = user.language.value
        life_path_info = get_life_path_meaning(profile.life_path, lang)

        # Calculate partner's profile
        partner_name = partner_data.get("name", "Партнёр")
        partner_birth_date = partner_data.get("birth_date")
        if isinstance(partner_birth_date, str):
            partner_birth_date = date.fromisoformat(partner_birth_date)

        partner_profile = get_full_profile(partner_name, partner_birth_date)
        partner_life_path_info = get_life_path_meaning(partner_profile.life_path, lang)

        # Calculate compatibility
        compatibility = calculate_compatibility(user.birth_date, partner_birth_date)

        if lang == "ru":
            prompt = f"""Создай ДЕТАЛЬНЫЙ ОТЧЁТ О СОВМЕСТИМОСТИ (PRO версия).

ДАННЫЕ ПЕРВОГО ЧЕЛОВЕКА ({user.name}):
• Число Судьбы: {profile.life_path} — {life_path_info["name"]}
• Число Души: {profile.soul_number}
• Число Выражения: {profile.expression_number}
• Число Личности: {profile.personality_number}

ДАННЫЕ ВТОРОГО ЧЕЛОВЕКА ({partner_name}):
• Число Судьбы: {partner_profile.life_path} — {partner_life_path_info["name"]}
• Число Души: {partner_profile.soul_number}
• Число Выражения: {partner_profile.expression_number}
• Число Личности: {partner_profile.personality_number}

РАСЧЁТНАЯ СОВМЕСТИМОСТЬ:
• Общая: {compatibility["overall_score"]}%
• По жизненному пути: {compatibility["life_path_score"]}%
• По душе: {compatibility["soul_score"]}%

СТРУКТУРА ОТЧЁТА:

1. 💑 ОБЩАЯ СОВМЕСТИМОСТЬ ({compatibility["overall_score"]}%)
   - Анализ общего потенциала пары
   - Почему вы вместе (кармические связи)
   - Что вас объединяет на глубинном уровне

2. 🔥 ФИЗИЧЕСКАЯ И СЕКСУАЛЬНАЯ СОВМЕСТИМОСТЬ
   - Физическое притяжение между {profile.life_path} и {partner_profile.life_path}
   - Страсть в отношениях
   - Как поддерживать огонь

3. 💬 ЭМОЦИОНАЛЬНАЯ СВЯЗЬ
   - Понимание друг друга
   - Эмоциональные потребности {user.name}
   - Эмоциональные потребности {partner_name}
   - Как говорить на одном языке

4. 🏠 СОВМЕСТИМОСТЬ В БЫТУ
   - Повседневная жизнь вместе
   - Распределение обязанностей
   - Общий дом и уют

5. 💰 ФИНАНСОВАЯ СОВМЕСТИМОСТЬ
   - Отношение к деньгам: {user.name} vs {partner_name}
   - Совместный бюджет: плюсы и минусы
   - Как избежать денежных конфликтов

6. 👪 СЕМЬЯ И ДЕТИ
   - Потенциал как родители
   - Стили воспитания
   - Семейные ценности

7. ⚠️ ЗОНЫ КОНФЛИКТОВ
   - Главные точки трения между {profile.life_path} и {partner_profile.life_path}
   - Конкретные ситуации, которые могут вызвать проблемы
   - Как их преодолеть

8. 💪 СИЛЬНЫЕ СТОРОНЫ ПАРЫ
   - Что вас делает сильнее вместе
   - Общие ценности
   - Чему вы учите друг друга

9. 🎯 РЕКОМЕНДАЦИИ ДЛЯ СЧАСТЛИВЫХ ОТНОШЕНИЙ
   - 5 советов для {user.name}
   - 5 советов для {partner_name}
   - 5 вещей, которые стоит делать вместе

Пиши детально и персонализированно. Используй имена обоих. Это платный отчёт — дай максимум ценности!"""
        else:
            prompt = f"""Create a DETAILED COMPATIBILITY REPORT (PRO version).

PERSON 1 ({user.name}):
• Life Path: {profile.life_path} — {life_path_info["name"]}
• Soul: {profile.soul_number}
• Expression: {profile.expression_number}
• Personality: {profile.personality_number}

PERSON 2 ({partner_name}):
• Life Path: {partner_profile.life_path} — {partner_life_path_info["name"]}
• Soul: {partner_profile.soul_number}
• Expression: {partner_profile.expression_number}
• Personality: {partner_profile.personality_number}

COMPATIBILITY SCORES:
• Overall: {compatibility["overall_score"]}%
• Life Path: {compatibility["life_path_score"]}%
• Soul: {compatibility["soul_score"]}%

REPORT STRUCTURE:
1. 💑 OVERALL COMPATIBILITY
2. 🔥 PHYSICAL COMPATIBILITY
3. 💬 EMOTIONAL CONNECTION
4. 🏠 DAILY LIFE COMPATIBILITY
5. 💰 FINANCIAL COMPATIBILITY
6. 👪 FAMILY AND CHILDREN
7. ⚠️ CONFLICT ZONES
8. 💪 COUPLE'S STRENGTHS
9. 🎯 RECOMMENDATIONS (5 for each person + 5 for doing together)

Write in detail using both names. This is a paid report — maximize value!"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt(lang)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
            temperature=0.7,
        )
        return response.choices[0].message.content


# Global instance
ai_service = AIService()
