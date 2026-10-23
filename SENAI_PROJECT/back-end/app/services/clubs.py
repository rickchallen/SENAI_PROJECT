from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.domain import (
    conflict,
    now_brasilia,
    sort_name,
    validate_acronym,
    validate_club_name,
)
from app.entidades import Clube as Club
from app.repositories import all_clubs, get_club
from app.services.common import club_payload


def create_club(session: Session, body: dict[str, Any]) -> dict[str, Any]:
    name = validate_club_name(body.get("name"))
    acronym = validate_acronym(body.get("acronym"), name)
    clubs = all_clubs(session)
    if len(clubs) >= 20:
        conflict("A liga já atingiu o limite de 20 clubes.")
    if any(existing.nome.lower() == name.lower() for existing in clubs):
        conflict("Já existe um clube com esse nome.")
    if any(existing.sigla == acronym for existing in clubs):
        conflict("Já existe um clube com essa sigla.")
    club = Club(
        nome=name,
        sigla=acronym,
        caixa=Decimal("300.00"),
        formacao=None,
        criado_em=now_brasilia(),
    )
    session.add(club)
    session.flush()
    return club_payload(session, club)


def get_club_payload(session: Session, club_id: int) -> dict[str, Any]:
    club = get_club(session, club_id)
    if club is None:
        from app.domain import not_found

        not_found("Clube não encontrado.")
    return club_payload(session, club, include_players=True)


def list_clubs(session: Session, sort: str) -> list[dict[str, Any]]:
    clubs = all_clubs(session)
    payloads = [club_payload(session, club) for club in clubs]
    if sort == "name":
        payloads.sort(key=lambda item: (sort_name(item["name"]), item["id"]))
    elif sort == "net_worth_asc":
        payloads.sort(
            key=lambda item: (item["net_worth"], sort_name(item["name"]), item["id"])
        )
    else:
        payloads.sort(
            key=lambda item: (-item["net_worth"], sort_name(item["name"]), item["id"])
        )
    return payloads
