import re
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import Request

from app.domain import (
    CONDITIONS,
    POSITIONS,
    DomainError,
    bad_request,
    normalize_search,
    parse_enum,
    parse_integer,
)

PATH_ID_PATTERN = re.compile(r"[1-9][0-9]*\Z")
QUERY_INT_PATTERN = re.compile(r"[1-9][0-9]*\Z")
MONEY_PATTERN = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?\Z")
PLAYER_SORTS = ("name", "value_asc", "value_desc", "age_asc", "age_desc", "position")


def path_id(raw: str) -> int:
    if not PATH_ID_PATTERN.fullmatch(raw):
        raise DomainError(404, "Recurso não encontrado.")
    value = int(raw)
    if value > 2_147_483_647:
        raise DomainError(404, "Recurso não encontrado.")
    return value


def body_integer(body: dict[str, Any], field: str, minimum: int, maximum: int) -> int:
    return parse_integer(body.get(field), field, minimum, maximum)


def query_values(request: Request, known: set[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key in known:
        values = request.query_params.getlist(key)
        if len(values) > 1:
            bad_request(f"O parâmetro {key} não pode ser repetido.")
        if values:
            result[key] = values[0]
    return result


def query_int(
    values: dict[str, str],
    field: str,
    minimum: int,
    maximum: int,
    default: int | None = None,
) -> int | None:
    raw = values.get(field)
    if raw is None:
        return default
    if not QUERY_INT_PATTERN.fullmatch(raw):
        bad_request(f"{field} deve ser um inteiro positivo sem zeros à esquerda.")
    value = int(raw)
    if value > 2_147_483_647 or not minimum <= value <= maximum:
        bad_request(f"{field} está fora dos limites aceitos.")
    return value


def player_filters(request: Request) -> dict[str, Any]:
    known = {
        "search",
        "position",
        "condition",
        "free",
        "club_id",
        "min_age",
        "max_age",
        "min_value",
        "max_value",
        "sort",
        "page",
        "limit",
    }
    values = query_values(request, known)
    search = normalize_search(values["search"]) if "search" in values else None
    position = (
        parse_enum(values["position"], "position", POSITIONS)
        if "position" in values
        else None
    )
    condition = (
        parse_enum(values["condition"], "condition", CONDITIONS)
        if "condition" in values
        else None
    )
    free: bool | None = None
    if "free" in values:
        if values["free"] not in ("true", "false"):
            bad_request("free deve ser true ou false.")
        free = values["free"] == "true"
    club_id = query_int(values, "club_id", 1, 2_147_483_647)
    min_age = query_int(values, "min_age", 16, 45)
    max_age = query_int(values, "max_age", 16, 45)
    min_value = _query_money(values, "min_value")
    max_value = _query_money(values, "max_value")
    if min_age is not None and max_age is not None and min_age > max_age:
        bad_request("min_age não pode ser maior que max_age.")
    if min_value is not None and max_value is not None and min_value > max_value:
        bad_request("min_value não pode ser maior que max_value.")
    if free is True and club_id is not None:
        bad_request("free=true não pode ser combinado com club_id.")
    raw_sort = values.get("sort", "name")
    sorts = raw_sort.split(",")
    if (
        len(sorts) > 2
        or any(sort not in PLAYER_SORTS for sort in sorts)
        or len(set(sorts)) != len(sorts)
    ):
        bad_request("sort contém um critério inválido.")
    return {
        "search": search,
        "position": position,
        "condition": condition,
        "free": free,
        "club_id": club_id,
        "min_age": min_age,
        "max_age": max_age,
        "min_value": min_value,
        "max_value": max_value,
        "sorts": sorts,
        "page": query_int(values, "page", 1, 2_147_483_647, 1),
        "limit": query_int(values, "limit", 1, 50, 10),
    }


def club_sort(request: Request) -> str:
    values = query_values(request, {"sort"})
    sort = values.get("sort", "name")
    if sort not in ("name", "net_worth_asc", "net_worth_desc"):
        bad_request("sort contém um critério inválido.")
    return sort


def transaction_filters(request: Request) -> dict[str, Any]:
    values = query_values(request, {"type", "player_id"})
    types: list[str] | None = None
    if "type" in values:
        types = values["type"].split(",")
        if (
            not types
            or any(value not in ("COMPRA", "VENDA") for value in types)
            or len(set(types)) != len(types)
        ):
            bad_request("type contém um valor inválido.")
    return {
        "types": types,
        "player_id": query_int(values, "player_id", 1, 2_147_483_647),
    }


def match_filters(request: Request) -> int | None:
    values = query_values(request, {"club_id"})
    return query_int(values, "club_id", 1, 2_147_483_647)


def _query_money(values: dict[str, str], field: str) -> Decimal | None:
    raw = values.get(field)
    if raw is None:
        return None
    if not MONEY_PATTERN.fullmatch(raw):
        bad_request(f"{field} deve ser um decimal sem sinal, com até duas casas.")
    try:
        value = Decimal(raw)
    except InvalidOperation:
        bad_request(f"{field} contém um valor inválido.")
    if value > Decimal("550"):
        bad_request(f"{field} deve estar entre 0 e 550.")
    return value
