import re
import unicodedata
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

BRASIL = timezone(timedelta(hours=-3))
POSITIONS = ("GOL", "ZAG", "LAT", "MEI", "ATA")
CONDITIONS = ("APTO", "MAL_CONDICIONADO", "DOENTE")
FORMATIONS = {
    "3-1": (3, 0, 1),
    "2-2": (2, 0, 2),
    "2-1-1": (2, 1, 1),
    "1-2-1": (1, 2, 1),
}
POSITION_ORDER = {position: index for index, position in enumerate(POSITIONS)}
WEIGHTS = {
    "GOL": (10, 0, 20, 0, 40, 30),
    "ZAG": (10, 0, 15, 0, 45, 30),
    "LAT": (25, 0, 15, 25, 15, 20),
    "MEI": (10, 15, 35, 25, 5, 10),
    "ATA": (20, 40, 10, 20, 0, 10),
}
ATTRIBUTE_FIELDS = (
    "velocidade",
    "finalizacao",
    "passe",
    "drible",
    "defesa",
    "fisico",
)
API_ATTRIBUTE_FIELDS = (
    "pace",
    "shooting",
    "passing",
    "dribbling",
    "defending",
    "physical",
)
ATTACK_ATTRIBUTE = {
    "ATA": ("shooting", "finalizacao"),
    "MEI": ("passing", "passe"),
    "ZAG": ("dribbling", "drible"),
    "LAT": ("dribbling", "drible"),
}


class DomainError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def bad_request(message: str) -> None:
    raise DomainError(400, message)


def not_found(message: str) -> None:
    raise DomainError(404, message)


def conflict(message: str) -> None:
    raise DomainError(409, message)


def now_brasilia() -> datetime:
    return datetime.now(BRASIL).replace(tzinfo=None)


def format_datetime(value: datetime) -> str:
    local = value.replace(tzinfo=None)
    return f"{local:%Y-%m-%dT%H:%M:%S}-03:00"


def round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def market_value(player: Any) -> Decimal:
    discount = {
        "APTO": Decimal("0"),
        "MAL_CONDICIONADO": Decimal("15"),
        "DOENTE": Decimal("30"),
    }[player.condicao]
    if player.condicao != "APTO":
        if player.agilidade >= 80:
            discount /= Decimal("2")
        elif player.agilidade <= 30:
            discount += Decimal("10")
    age_adjustment = (
        Decimal("10")
        if player.idade <= 21
        else Decimal("-10")
        if player.idade >= 32
        else Decimal("0")
    )
    percentage = max(Decimal("-40"), age_adjustment - discount)
    value = round_money(
        Decimal(player.valor_base) * (Decimal("100") + percentage) / Decimal("100")
    )
    return max(Decimal("1.00"), value)


def calculate_overall(position: str, values: tuple[int, ...]) -> int:
    weighted_total = sum(
        value * weight for value, weight in zip(values, WEIGHTS[position], strict=True)
    )
    return int(
        (Decimal(weighted_total) / Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


def calculate_base_value(overall: int, potential: int, age: int) -> Decimal:
    total = (
        Decimal(max(0, min(overall, 60) - 40)) * Decimal("0.50")
        + Decimal(max(0, min(overall, 75) - 60)) * Decimal("2.00")
        + Decimal(max(0, overall - 75)) * Decimal("6.00")
    )
    if age <= 21:
        total *= (Decimal("100") + potential - overall) / Decimal("100")
    return max(Decimal("1.00"), round_money(total))


def normalize_text(value: object, field: str, minimum: int, maximum: int) -> str:
    if not isinstance(value, str):
        bad_request(f"{field} deve ser um texto válido.")
    if any(unicodedata.category(character) == "Cc" for character in value):
        bad_request(f"{field} não pode conter caracteres de controle.")
    result = re.sub(r" {2,}", " ", value.strip(" "))
    if not minimum <= len(result) <= maximum:
        bad_request(f"{field} deve ter entre {minimum} e {maximum} caracteres.")
    return result


def normalize_search(value: str) -> str:
    normalized = normalize_text(value, "search", 2, 100)
    if not normalized:
        bad_request("search não pode ficar vazio.")
    return normalized


def fold_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(
        character for character in decomposed if unicodedata.category(character) != "Mn"
    )


def sort_name(value: str) -> str:
    return fold_accents(value)


def parse_integer(value: object, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        bad_request(f"{field} deve ser um número inteiro.")
    if isinstance(value, float) and (not value.is_integer()):
        bad_request(f"{field} deve ser um número inteiro.")
    result = int(value)
    if not minimum <= result <= maximum:
        bad_request(f"{field} deve estar entre {minimum} e {maximum}.")
    return result


def required(body: dict[str, object], field: str) -> object:
    value = body.get(field)
    if value is None:
        bad_request(f"{field} é obrigatório.")
    return value


def parse_enum(value: object, field: str, accepted: tuple[str, ...]) -> str:
    if not isinstance(value, str) or value not in accepted:
        bad_request(f"{field} possui um valor inválido.")
    return value


def validate_player_name(value: object) -> str:
    name = normalize_text(value, "name", 3, 100)
    words = name.split(" ")
    if sum(
        any(unicodedata.category(char).startswith("L") for char in word)
        for word in words
    ) < 2 or any(char.isdigit() for char in name):
        bad_request("name deve conter ao menos duas palavras e nenhum dígito.")
    return name


def validate_club_name(value: object) -> str:
    name = normalize_text(value, "name", 3, 60)
    words = name.split(" ")
    if not 2 <= len(words) <= 5:
        bad_request("name deve conter de duas a cinco palavras.")
    for character in name:
        category = unicodedata.category(character)
        if not category.startswith("L") and category != "Mn" and character not in " -.":
            bad_request("name contém caracteres não permitidos.")
    return name


def validate_acronym(value: object, name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z]{3}", value):
        bad_request("acronym deve conter três letras maiúsculas sem acento.")
    folded_name = fold_accents(name)
    folded_acronym = value.lower()
    if (
        folded_acronym[0] != folded_name[0]
        or len(set(folded_acronym)) == 1
        or not _is_subsequence(folded_acronym, folded_name)
    ):
        bad_request("acronym não corresponde ao nome do clube.")
    return value


def _is_subsequence(candidate: str, value: str) -> bool:
    position = 0
    for character in value:
        if position < len(candidate) and candidate[position] == character:
            position += 1
    return position == len(candidate)


def parse_brasilia_datetime(value: object) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}-03:00", value
    ):
        bad_request("loyalty_until deve usar o formato AAAA-MM-DDTHH:MM-03:00.")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M-03:00")
    except ValueError:
        bad_request("loyalty_until contém uma data ou hora inexistente.")


def remaining_days(loyalty_until: datetime, moment: datetime) -> int:
    difference = loyalty_until - moment
    if difference.total_seconds() <= 0:
        return 0
    return difference.days + (1 if difference.seconds or difference.microseconds else 0)


def penalty_rate(days: int) -> int:
    if days == 0:
        return 0
    if days <= 30:
        return 5
    if days <= 180:
        return 10
    return 20


def attribute_with_condition(value: int, condition: str) -> int:
    if condition == "APTO":
        return value
    return int(
        (Decimal(value) * Decimal("0.85")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
