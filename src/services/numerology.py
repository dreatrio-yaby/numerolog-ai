"""Numerology calculation service."""

from datetime import date
from typing import Optional

from src.models.user import NumerologyProfile

# Pythagorean letter-to-number mapping
LETTER_VALUES = {
    # English
    "a": 1,
    "b": 2,
    "c": 3,
    "d": 4,
    "e": 5,
    "f": 6,
    "g": 7,
    "h": 8,
    "i": 9,
    "j": 1,
    "k": 2,
    "l": 3,
    "m": 4,
    "n": 5,
    "o": 6,
    "p": 7,
    "q": 8,
    "r": 9,
    "s": 1,
    "t": 2,
    "u": 3,
    "v": 4,
    "w": 5,
    "x": 6,
    "y": 7,
    "z": 8,
    # Russian (Cyrillic)
    "а": 1,
    "б": 2,
    "в": 3,
    "г": 4,
    "д": 5,
    "е": 6,
    "ё": 7,
    "ж": 8,
    "з": 9,
    "и": 1,
    "й": 2,
    "к": 3,
    "л": 4,
    "м": 5,
    "н": 6,
    "о": 7,
    "п": 8,
    "р": 9,
    "с": 1,
    "т": 2,
    "у": 3,
    "ф": 4,
    "х": 5,
    "ц": 6,
    "ч": 7,
    "ш": 8,
    "щ": 9,
    "ъ": 1,
    "ы": 2,
    "ь": 3,
    "э": 4,
    "ю": 5,
    "я": 6,
}

# Vowels for soul number calculation
VOWELS = set("aeiouаеёиоуыэюя")


def reduce_to_single(num: int, keep_master: bool = True) -> int:
    """Reduce number to single digit (1-9) or master number (11, 22, 33)."""
    while num > 9:
        if keep_master and num in (11, 22, 33):
            return num
        num = sum(int(d) for d in str(num))
    return num


def calculate_life_path(birth_date: date) -> int:
    """
    Calculate Life Path Number (Число Судьбы).
    Sum all digits of birth date and reduce.
    """
    date_str = birth_date.strftime("%d%m%Y")
    total = sum(int(d) for d in date_str)
    return reduce_to_single(total)


def calculate_soul_number(birth_date: date) -> int:
    """
    Calculate Soul Number (Число Души).
    Based on day of birth only.
    """
    day = birth_date.day
    return reduce_to_single(day)


def calculate_expression_number(name: str) -> int:
    """
    Calculate Expression/Destiny Number (Число Имени).
    Sum of all letters in full name.
    """
    name = name.lower().replace(" ", "")
    total = sum(LETTER_VALUES.get(char, 0) for char in name)
    return reduce_to_single(total)


def calculate_soul_urge(name: str) -> int:
    """
    Calculate Soul Urge / Heart's Desire Number.
    Sum of vowels only.
    """
    name = name.lower().replace(" ", "")
    total = sum(LETTER_VALUES.get(char, 0) for char in name if char in VOWELS)
    return reduce_to_single(total)


def calculate_personality_number(name: str) -> int:
    """
    Calculate Personality Number.
    Sum of consonants only.
    """
    name = name.lower().replace(" ", "")
    total = sum(LETTER_VALUES.get(char, 0) for char in name if char not in VOWELS)
    return reduce_to_single(total)


def calculate_birthday_number(birth_date: date) -> int:
    """Calculate Birthday Number (just the day)."""
    return reduce_to_single(birth_date.day, keep_master=False)


def calculate_maturity_number(life_path: int, expression: int) -> int:
    """
    Calculate Maturity Number.
    Life Path + Expression Number.
    """
    return reduce_to_single(life_path + expression)


def calculate_pythagoras_matrix(birth_date: date) -> dict[int, int]:
    """
    Calculate Pythagoras Matrix (Психоматрица).
    Counts occurrences of each digit (1-9) in the birth date calculation.
    """
    # Get all working numbers
    date_str = birth_date.strftime("%d%m%Y")

    # First working number: sum of all digits
    first = sum(int(d) for d in date_str)

    # Second working number: reduce first
    second = reduce_to_single(first, keep_master=False)

    # Third working number: first - (2 * first digit of date)
    first_digit = int(date_str[0]) if date_str[0] != "0" else int(date_str[1])
    third = abs(first - 2 * first_digit)

    # Fourth working number: reduce third
    fourth = reduce_to_single(third, keep_master=False)

    # Combine all numbers for matrix
    all_digits = date_str + str(first) + str(second) + str(third) + str(fourth)
    all_digits = all_digits.replace("0", "")  # Remove zeros

    # Count occurrences
    matrix = {i: 0 for i in range(1, 10)}
    for digit in all_digits:
        d = int(digit)
        if 1 <= d <= 9:
            matrix[d] += 1

    return matrix


def calculate_personal_year(birth_date: date, target_date: Optional[date] = None) -> int:
    """
    Calculate Personal Year Number.
    Birth month + Birth day + Current year.
    """
    if target_date is None:
        target_date = date.today()

    total = birth_date.month + birth_date.day + target_date.year
    return reduce_to_single(total)


def calculate_personal_month(personal_year: int, target_date: Optional[date] = None) -> int:
    """
    Calculate Personal Month Number.
    Personal Year + Current month.
    """
    if target_date is None:
        target_date = date.today()

    total = personal_year + target_date.month
    return reduce_to_single(total)


def calculate_personal_day(personal_month: int, target_date: Optional[date] = None) -> int:
    """
    Calculate Personal Day Number.
    Personal Month + Current day.
    """
    if target_date is None:
        target_date = date.today()

    total = personal_month + target_date.day
    return reduce_to_single(total)


def calculate_compatibility(date1: date, date2: date) -> dict:
    """
    Calculate compatibility between two people.
    Returns compatibility scores and analysis points.
    """
    lp1 = calculate_life_path(date1)
    lp2 = calculate_life_path(date2)

    soul1 = calculate_soul_number(date1)
    soul2 = calculate_soul_number(date2)

    # Compatibility matrix (simplified)
    # Higher score = better compatibility
    compatibility_scores = {
        (1, 1): 70,
        (1, 2): 60,
        (1, 3): 85,
        (1, 4): 50,
        (1, 5): 90,
        (1, 6): 65,
        (1, 7): 55,
        (1, 8): 75,
        (1, 9): 80,
        (2, 2): 75,
        (2, 3): 70,
        (2, 4): 85,
        (2, 5): 55,
        (2, 6): 90,
        (2, 7): 65,
        (2, 8): 80,
        (2, 9): 75,
        (3, 3): 80,
        (3, 4): 50,
        (3, 5): 90,
        (3, 6): 85,
        (3, 7): 60,
        (3, 8): 55,
        (3, 9): 95,
        (4, 4): 70,
        (4, 5): 45,
        (4, 6): 75,
        (4, 7): 85,
        (4, 8): 90,
        (4, 9): 55,
        (5, 5): 65,
        (5, 6): 50,
        (5, 7): 80,
        (5, 8): 60,
        (5, 9): 85,
        (6, 6): 85,
        (6, 7): 55,
        (6, 8): 70,
        (6, 9): 90,
        (7, 7): 75,
        (7, 8): 60,
        (7, 9): 65,
        (8, 8): 80,
        (8, 9): 70,
        (9, 9): 85,
    }

    # Get score (order doesn't matter)
    key = tuple(sorted([lp1, lp2]))
    life_path_score = compatibility_scores.get(key, 70)

    soul_key = tuple(sorted([soul1, soul2]))
    soul_score = compatibility_scores.get(soul_key, 70)

    # Calculate overall score
    overall_score = int(life_path_score * 0.6 + soul_score * 0.4)

    return {
        "overall_score": overall_score,
        "life_path_score": life_path_score,
        "soul_score": soul_score,
        "person1": {"life_path": lp1, "soul": soul1},
        "person2": {"life_path": lp2, "soul": soul2},
    }


def get_full_profile(name: str, birth_date: date) -> NumerologyProfile:
    """Calculate complete numerology profile for a user."""
    life_path = calculate_life_path(birth_date)
    expression = calculate_expression_number(name)
    personal_year = calculate_personal_year(birth_date)
    personal_month = calculate_personal_month(personal_year)

    return NumerologyProfile(
        life_path=life_path,
        soul_number=calculate_soul_number(birth_date),
        expression_number=expression,
        personality_number=calculate_personality_number(name),
        matrix=calculate_pythagoras_matrix(birth_date),
        birthday_number=calculate_birthday_number(birth_date),
        maturity_number=calculate_maturity_number(life_path, expression),
        personal_year=personal_year,
        personal_month=personal_month,
        personal_day=calculate_personal_day(personal_month),
    )
