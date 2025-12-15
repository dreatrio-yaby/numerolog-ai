"""Numerology knowledge base - meanings of numbers."""

from typing import Dict

# Life Path Number meanings
LIFE_PATH_MEANINGS: Dict[int, Dict[str, str]] = {
    1: {
        "ru": {
            "name": "Лидер",
            "short": "Независимость, амбиции, новаторство",
            "description": """Ты прирождённый лидер с сильной волей и стремлением к независимости.
У тебя есть природный талант начинать новые проекты и вести за собой людей.
Ты ценишь свободу и не любишь, когда тебе указывают, что делать.

Сильные стороны: решительность, оригинальность, смелость, целеустремлённость.
Над чем работать: эгоизм, нетерпеливость, упрямство.""",
        },
        "en": {
            "name": "Leader",
            "short": "Independence, ambition, innovation",
            "description": """You are a natural-born leader with strong willpower and a drive for independence.
You have a talent for starting new projects and inspiring others to follow.
You value freedom and don't like being told what to do.

Strengths: determination, originality, courage, goal-oriented.
Areas to work on: selfishness, impatience, stubbornness.""",
        },
    },
    2: {
        "ru": {
            "name": "Дипломат",
            "short": "Сотрудничество, чувствительность, гармония",
            "description": """Ты миротворец и прирождённый дипломат. Умеешь чувствовать настроение других
и находить компромиссы. Тебе важна гармония в отношениях и комфортная обстановка.
Ты отличный командный игрок и партнёр.

Сильные стороны: эмпатия, терпение, тактичность, интуиция.
Над чем работать: нерешительность, зависимость от мнения других, избегание конфликтов.""",
        },
        "en": {
            "name": "Diplomat",
            "short": "Cooperation, sensitivity, harmony",
            "description": """You are a peacemaker and natural diplomat. You can sense others' moods
and find compromises. Harmony in relationships and a comfortable environment matter to you.
You're an excellent team player and partner.

Strengths: empathy, patience, tactfulness, intuition.
Areas to work on: indecisiveness, dependency on others' opinions, conflict avoidance.""",
        },
    },
    3: {
        "ru": {
            "name": "Творец",
            "short": "Творчество, самовыражение, оптимизм",
            "description": """Ты творческая личность с богатым воображением. Умеешь выражать себя
через слова, искусство или любую другую форму. Люди тянутся к твоему оптимизму и харизме.
Жизнь для тебя — это праздник и возможность творить.

Сильные стороны: креативность, общительность, вдохновение, артистизм.
Над чем работать: рассеянность, поверхностность, склонность к драматизации.""",
        },
        "en": {
            "name": "Creator",
            "short": "Creativity, self-expression, optimism",
            "description": """You are a creative soul with rich imagination. You express yourself
through words, art, or any other medium. People are drawn to your optimism and charisma.
Life for you is a celebration and an opportunity to create.

Strengths: creativity, sociability, inspiration, artistry.
Areas to work on: scatter-mindedness, superficiality, tendency to dramatize.""",
        },
    },
    4: {
        "ru": {
            "name": "Строитель",
            "short": "Стабильность, порядок, трудолюбие",
            "description": """Ты надёжный и практичный человек, который строит прочный фундамент
во всём. Ценишь порядок, систему и стабильность. На тебя можно положиться —
ты всегда выполняешь обещания и доводишь дела до конца.

Сильные стороны: надёжность, организованность, дисциплина, выносливость.
Над чем работать: упрямство, негибкость, склонность к рутине.""",
        },
        "en": {
            "name": "Builder",
            "short": "Stability, order, hard work",
            "description": """You are a reliable and practical person who builds solid foundations
in everything. You value order, systems, and stability. People can count on you —
you always keep promises and see things through.

Strengths: reliability, organization, discipline, endurance.
Areas to work on: stubbornness, inflexibility, tendency toward routine.""",
        },
    },
    5: {
        "ru": {
            "name": "Искатель",
            "short": "Свобода, перемены, приключения",
            "description": """Ты свободолюбивая душа, жаждущая перемен и приключений. Рутина — твой враг.
Тебе нужны новые впечатления, путешествия и разнообразие. Ты легко адаптируешься
к любым обстоятельствам и умеешь находить общий язык с разными людьми.

Сильные стороны: адаптивность, любознательность, энергичность, обаяние.
Над чем работать: непостоянство, безответственность, склонность к излишествам.""",
        },
        "en": {
            "name": "Adventurer",
            "short": "Freedom, change, adventure",
            "description": """You are a freedom-loving soul craving change and adventure. Routine is your enemy.
You need new experiences, travel, and variety. You adapt easily to any circumstances
and can connect with different people.

Strengths: adaptability, curiosity, energy, charm.
Areas to work on: inconsistency, irresponsibility, tendency toward excess.""",
        },
    },
    6: {
        "ru": {
            "name": "Хранитель",
            "short": "Забота, ответственность, семья",
            "description": """Ты заботливый и ответственный человек, для которого семья и близкие — главное.
Умеешь создавать уют и гармонию вокруг себя. Люди часто обращаются к тебе за советом
и поддержкой. Ты готов многим жертвовать ради тех, кого любишь.

Сильные стороны: заботливость, ответственность, гармоничность, верность.
Над чем работать: гиперопека, жертвенность, перфекционизм.""",
        },
        "en": {
            "name": "Nurturer",
            "short": "Care, responsibility, family",
            "description": """You are a caring and responsible person for whom family and loved ones come first.
You create comfort and harmony around you. People often turn to you for advice
and support. You're willing to sacrifice for those you love.

Strengths: nurturing, responsibility, harmony, loyalty.
Areas to work on: overprotectiveness, martyrdom, perfectionism.""",
        },
    },
    7: {
        "ru": {
            "name": "Мыслитель",
            "short": "Анализ, духовность, поиск истины",
            "description": """Ты глубокий мыслитель, ищущий ответы на главные вопросы жизни.
Тебе нужно время наедине с собой для размышлений. У тебя аналитический ум
и сильная интуиция. Ты не принимаешь ничего на веру — всё проверяешь сам.

Сильные стороны: мудрость, интуиция, аналитический ум, духовность.
Над чем работать: замкнутость, скептицизм, отстранённость.""",
        },
        "en": {
            "name": "Seeker",
            "short": "Analysis, spirituality, truth-seeking",
            "description": """You are a deep thinker searching for answers to life's big questions.
You need time alone for reflection. You have an analytical mind
and strong intuition. You don't take anything at face value — you verify everything yourself.

Strengths: wisdom, intuition, analytical mind, spirituality.
Areas to work on: isolation, skepticism, detachment.""",
        },
    },
    8: {
        "ru": {
            "name": "Достигатор",
            "short": "Власть, успех, материальное благополучие",
            "description": """Ты амбициозный человек с сильным стремлением к успеху и материальному благополучию.
У тебя отличные организаторские способности и деловая хватка. Ты умеешь видеть
возможности там, где другие их не замечают, и превращать идеи в реальность.

Сильные стороны: амбициозность, практичность, лидерство, стратегическое мышление.
Над чем работать: материализм, властность, трудоголизм.""",
        },
        "en": {
            "name": "Achiever",
            "short": "Power, success, material abundance",
            "description": """You are an ambitious person with a strong drive for success and material wealth.
You have excellent organizational skills and business acumen. You see opportunities
where others don't and turn ideas into reality.

Strengths: ambition, practicality, leadership, strategic thinking.
Areas to work on: materialism, dominance, workaholism.""",
        },
    },
    9: {
        "ru": {
            "name": "Гуманист",
            "short": "Мудрость, сострадание, служение",
            "description": """Ты мудрая душа с широким взглядом на мир. Тебе важно делать что-то значимое
для человечества. У тебя большое сердце и способность понимать людей разных культур.
Ты часто выступаешь в роли учителя или наставника.

Сильные стороны: мудрость, сострадание, щедрость, творческий талант.
Над чем работать: идеализм, эмоциональная отстранённость, рассеянность.""",
        },
        "en": {
            "name": "Humanitarian",
            "short": "Wisdom, compassion, service",
            "description": """You are a wise soul with a broad worldview. Making a meaningful difference
matters to you. You have a big heart and understand people from different cultures.
You often take on the role of teacher or mentor.

Strengths: wisdom, compassion, generosity, creative talent.
Areas to work on: idealism, emotional detachment, scatter-mindedness.""",
        },
    },
    # Master numbers
    11: {
        "ru": {
            "name": "Мастер интуиции",
            "short": "Духовное озарение, вдохновение, высшая чувствительность",
            "description": """Ты носитель мастер-числа 11 — это особый дар и ответственность.
У тебя сильнейшая интуиция и способность вдохновлять других. Ты можешь быть
духовным лидером или творцом, несущим свет людям. Но этот путь требует работы над собой.

Сильные стороны: интуиция, вдохновение, духовность, харизма.
Над чем работать: нервозность, неуверенность, непрактичность.""",
        },
        "en": {
            "name": "Master Intuitive",
            "short": "Spiritual illumination, inspiration, heightened sensitivity",
            "description": """You carry master number 11 — a special gift and responsibility.
You have powerful intuition and the ability to inspire others. You can be
a spiritual leader or creator bringing light to people. But this path requires self-work.

Strengths: intuition, inspiration, spirituality, charisma.
Areas to work on: nervousness, self-doubt, impracticality.""",
        },
    },
    22: {
        "ru": {
            "name": "Мастер-строитель",
            "short": "Великие достижения, практическая мудрость, глобальное видение",
            "description": """Ты носитель мастер-числа 22 — самого могущественного числа в нумерологии.
У тебя способность воплощать грандиозные мечты в реальность. Ты можешь построить
что-то великое, что останется после тебя и принесёт пользу многим людям.

Сильные стороны: видение, практичность, лидерство, созидательная сила.
Над чем работать: перфекционизм, давление, склонность брать слишком много.""",
        },
        "en": {
            "name": "Master Builder",
            "short": "Great achievements, practical wisdom, global vision",
            "description": """You carry master number 22 — the most powerful number in numerology.
You can turn grand dreams into reality. You can build something great
that will outlast you and benefit many people.

Strengths: vision, practicality, leadership, creative power.
Areas to work on: perfectionism, pressure, tendency to take on too much.""",
        },
    },
    33: {
        "ru": {
            "name": "Мастер-учитель",
            "short": "Бескорыстное служение, духовное учительство, целительство",
            "description": """Ты носитель редкого мастер-числа 33 — числа Мастера-Учителя.
Твоё призвание — бескорыстное служение и помощь другим в их духовном развитии.
Ты способен нести исцеление и мудрость в мир через любовь и сострадание.

Сильные стороны: мудрость, бескорыстие, целительство, духовная сила.
Над чем работать: самопожертвование, чрезмерная ответственность.""",
        },
        "en": {
            "name": "Master Teacher",
            "short": "Selfless service, spiritual teaching, healing",
            "description": """You carry rare master number 33 — the Master Teacher number.
Your calling is selfless service and helping others in their spiritual development.
You can bring healing and wisdom to the world through love and compassion.

Strengths: wisdom, selflessness, healing, spiritual power.
Areas to work on: self-sacrifice, excessive responsibility.""",
        },
    },
}

# Personal Year meanings
PERSONAL_YEAR_MEANINGS: Dict[int, Dict[str, str]] = {
    1: {
        "ru": "Год новых начинаний. Отличное время для старта проектов, смены работы, новых знакомств.",
        "en": "Year of new beginnings. Great time for starting projects, changing jobs, new connections.",
    },
    2: {
        "ru": "Год партнёрства и терпения. Фокус на отношениях, сотрудничестве, не торопи события.",
        "en": "Year of partnership and patience. Focus on relationships, cooperation, don't rush things.",
    },
    3: {
        "ru": "Год творчества и общения. Выражай себя, общайся, развлекайся — энергия на твоей стороне.",
        "en": "Year of creativity and communication. Express yourself, socialize, have fun — energy is on your side.",
    },
    4: {
        "ru": "Год строительства фундамента. Работа, дисциплина, порядок — заложи основу для будущего.",
        "en": "Year of building foundations. Work, discipline, order — lay the groundwork for the future.",
    },
    5: {
        "ru": "Год перемен и свободы. Ожидай неожиданностей, будь гибким, пробуй новое.",
        "en": "Year of change and freedom. Expect the unexpected, be flexible, try new things.",
    },
    6: {
        "ru": "Год семьи и ответственности. Фокус на доме, близких, возможны важные семейные события.",
        "en": "Year of family and responsibility. Focus on home, loved ones, important family events possible.",
    },
    7: {
        "ru": "Год самопознания и отдыха. Время для учёбы, медитации, анализа своей жизни.",
        "en": "Year of self-discovery and rest. Time for learning, meditation, analyzing your life.",
    },
    8: {
        "ru": "Год достижений и финансов. Карьерный рост, финансовые возможности, признание.",
        "en": "Year of achievements and finances. Career growth, financial opportunities, recognition.",
    },
    9: {
        "ru": "Год завершения цикла. Отпусти старое, прости, подготовься к новому девятилетнему циклу.",
        "en": "Year of cycle completion. Let go of the old, forgive, prepare for a new nine-year cycle.",
    },
}

# Matrix position meanings (Pythagoras)
MATRIX_MEANINGS: Dict[int, Dict[str, str]] = {
    1: {
        "ru": {
            "name": "Характер, воля, эго",
            "0": "Слабая воля, зависимость от других",
            "1": "Мягкий характер, дипломатичность",
            "2": "Здоровая самооценка, уверенность",
            "3": "Сильный характер, лидерство",
            "4+": "Деспотичность, эгоцентризм",
        },
        "en": {
            "name": "Character, will, ego",
            "0": "Weak will, dependency on others",
            "1": "Soft character, diplomacy",
            "2": "Healthy self-esteem, confidence",
            "3": "Strong character, leadership",
            "4+": "Despotism, egocentrism",
        },
    },
    2: {
        "ru": {
            "name": "Энергия, здоровье",
            "0": "Низкая энергия, нужна подзарядка от других",
            "1": "Чувствительность к энергии",
            "2": "Достаточно энергии для себя",
            "3": "Хорошая энергетика, можешь делиться",
            "4+": "Очень сильная энергия, целительские способности",
        },
        "en": {
            "name": "Energy, health",
            "0": "Low energy, needs recharging from others",
            "1": "Sensitivity to energy",
            "2": "Enough energy for yourself",
            "3": "Good energy, can share with others",
            "4+": "Very strong energy, healing abilities",
        },
    },
    3: {
        "ru": {
            "name": "Интерес, познание",
            "0": "Гуманитарный склад ума",
            "1": "Интересуешься всем понемногу",
            "2": "Сильный интерес к наукам",
            "3": "Технический склад ума",
            "4+": "Может быть разбросанность интересов",
        },
        "en": {
            "name": "Interest, cognition",
            "0": "Humanitarian mindset",
            "1": "Interested in a bit of everything",
            "2": "Strong interest in sciences",
            "3": "Technical mindset",
            "4+": "May have scattered interests",
        },
    },
    4: {
        "ru": {
            "name": "Здоровье, физическое тело",
            "0": "Нужно следить за здоровьем",
            "1": "Обычное здоровье",
            "2": "Хорошее здоровье",
            "3": "Крепкое здоровье",
            "4+": "Отличное здоровье, выносливость",
        },
        "en": {
            "name": "Health, physical body",
            "0": "Need to monitor health",
            "1": "Average health",
            "2": "Good health",
            "3": "Strong health",
            "4+": "Excellent health, endurance",
        },
    },
    5: {
        "ru": {
            "name": "Логика, интуиция",
            "0": "Больше интуиции, чем логики",
            "1": "Развитая интуиция",
            "2": "Баланс логики и интуиции",
            "3": "Сильная логика",
            "4+": "Очень сильная логика, аналитик",
        },
        "en": {
            "name": "Logic, intuition",
            "0": "More intuition than logic",
            "1": "Developed intuition",
            "2": "Balance of logic and intuition",
            "3": "Strong logic",
            "4+": "Very strong logic, analyst",
        },
    },
    6: {
        "ru": {
            "name": "Труд, мастерство",
            "0": "Не любит физический труд",
            "1": "Может работать по необходимости",
            "2": "Любит работать руками",
            "3": "Мастер на все руки",
            "4+": "Трудоголик",
        },
        "en": {
            "name": "Work, craftsmanship",
            "0": "Doesn't like physical work",
            "1": "Can work when necessary",
            "2": "Likes working with hands",
            "3": "Jack of all trades",
            "4+": "Workaholic",
        },
    },
    7: {
        "ru": {
            "name": "Удача, талант",
            "0": "Удачу нужно создавать самому",
            "1": "Есть везение в жизни",
            "2": "Заметное везение",
            "3": "Сильная удача, талант",
            "4+": "Особый дар, таланты",
        },
        "en": {
            "name": "Luck, talent",
            "0": "Need to create your own luck",
            "1": "Some luck in life",
            "2": "Noticeable luck",
            "3": "Strong luck, talent",
            "4+": "Special gift, talents",
        },
    },
    8: {
        "ru": {
            "name": "Долг, ответственность",
            "0": "Свободен от чувства долга",
            "1": "Развитое чувство долга",
            "2": "Сильное чувство долга",
            "3": "Очень ответственный",
            "4+": "Гиперответственность",
        },
        "en": {
            "name": "Duty, responsibility",
            "0": "Free from sense of duty",
            "1": "Developed sense of duty",
            "2": "Strong sense of duty",
            "3": "Very responsible",
            "4+": "Hyper-responsibility",
        },
    },
    9: {
        "ru": {
            "name": "Память, ум",
            "0": "Память нужно тренировать",
            "1": "Хорошая память",
            "2": "Отличная память",
            "3": "Феноменальная память",
            "4+": "Возможна перегрузка информацией",
        },
        "en": {
            "name": "Memory, intelligence",
            "0": "Memory needs training",
            "1": "Good memory",
            "2": "Excellent memory",
            "3": "Phenomenal memory",
            "4+": "Possible information overload",
        },
    },
}


def get_life_path_meaning(number: int, lang: str = "ru") -> dict:
    """Get Life Path number meaning."""
    if number in LIFE_PATH_MEANINGS:
        return LIFE_PATH_MEANINGS[number][lang]
    return LIFE_PATH_MEANINGS[reduce_number(number)][lang]


def get_personal_year_meaning(number: int, lang: str = "ru") -> str:
    """Get Personal Year meaning."""
    return PERSONAL_YEAR_MEANINGS.get(number, PERSONAL_YEAR_MEANINGS[1])[lang]


def get_matrix_meaning(position: int, count: int, lang: str = "ru") -> dict:
    """Get Pythagoras matrix position meaning."""
    if position not in MATRIX_MEANINGS:
        return {}

    meanings = MATRIX_MEANINGS[position][lang]
    result = {"name": meanings["name"]}

    if count == 0:
        result["interpretation"] = meanings["0"]
    elif count == 1:
        result["interpretation"] = meanings["1"]
    elif count == 2:
        result["interpretation"] = meanings["2"]
    elif count == 3:
        result["interpretation"] = meanings["3"]
    else:
        result["interpretation"] = meanings["4+"]

    return result


def reduce_number(num: int) -> int:
    """Reduce to single digit."""
    while num > 9 and num not in (11, 22, 33):
        num = sum(int(d) for d in str(num))
    return num
