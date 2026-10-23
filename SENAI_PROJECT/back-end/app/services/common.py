from datetime import datetime
from decimal import Decimal
from functools import cmp_to_key
from typing import Any

from sqlalchemy.orm import Session

from app.domain import (
    POSITION_ORDER,
    format_datetime,
    market_value,
    now_brasilia,
    penalty_rate,
    remaining_days,
    sort_name,
)
from app.entidades import Clube as Club
from app.entidades import Jogador as Player
from app.repositories import (
    club_contracts,
    club_players,
    get_club,
    get_player,
)


def require_player(session: Session, player_id: int, lock: bool = False) -> Player:
    player = get_player(session, player_id, lock)
    if player is None:
        from app.domain import not_found

        not_found("Jogador não encontrado.")
    return player


def require_club(session: Session, club_id: int, lock: bool = False) -> Club:
    club = get_club(session, club_id, lock)
    if club is None:
        from app.domain import not_found

        not_found("Clube não encontrado.")
    return club


def player_order(player: Player) -> tuple[int, str, int]:
    return POSITION_ORDER[player.posicao], sort_name(player.nome), player.id


def ordered_roster(players: list[Player]) -> list[Player]:
    return sorted(players, key=player_order)


def player_payload(player: Player) -> dict[str, Any]:
    from app.domain import API_ATTRIBUTE_FIELDS, ATTRIBUTE_FIELDS, calculate_overall

    values = tuple(getattr(player, field) for field in ATTRIBUTE_FIELDS)
    payload = {
        "id": player.id,
        "name": player.nome,
        "position": player.posicao,
        "agility": player.agilidade,
        "age": player.idade,
        "condition": player.condicao,
        "base_value": player.valor_base,
        "market_value": market_value(player),
        "potential": player.potencial,
        "overall": calculate_overall(player.posicao, values),
        "club_id": player.clube_id,
    }
    payload.update(
        {
            api_name: value
            for api_name, value in zip(API_ATTRIBUTE_FIELDS, values, strict=True)
        }
    )
    return payload


def contract_payload(contract: Any, moment: datetime) -> dict[str, Any]:
    days = remaining_days(contract.fidelidade_ate, moment)
    return {
        "purchase_value": contract.valor_compra,
        "loyalty_until": format_datetime(contract.fidelidade_ate),
        "remaining_days": days,
        "penalty_rate": penalty_rate(days),
    }


def club_payload(
    session: Session, club: Club, include_players: bool = False
) -> dict[str, Any]:
    roster = ordered_roster(club_players(session, club.id))
    values = [market_value(player) for player in roster]
    squad_value = sum(values, Decimal("0.00"))
    payload: dict[str, Any] = {
        "id": club.id,
        "name": club.nome,
        "acronym": club.sigla,
        "cash": club.caixa,
        "squad_value": squad_value,
        "net_worth": club.caixa + squad_value,
    }
    if include_players:
        moment = now_brasilia()
        contracts = club_contracts(session, club.id)
        players = []
        for player in roster:
            serialized = player_payload(player)
            contract = contracts.get(player.id)
            if contract is not None:
                serialized["contract"] = contract_payload(contract, moment)
            players.append(serialized)
        payload["players"] = players
    return payload


def compare_values(left: Any, right: Any) -> int:
    return (left > right) - (left < right)


def compare_players(sorts: list[str]):
    def compare(left: dict[str, Any], right: dict[str, Any]) -> int:
        for sort in sorts:
            if sort == "name":
                result = compare_values(
                    sort_name(left["name"]), sort_name(right["name"])
                )
            elif sort.startswith("value_"):
                result = compare_values(left["market_value"], right["market_value"])
                if sort.endswith("desc"):
                    result *= -1
            elif sort.startswith("age_"):
                result = compare_values(left["age"], right["age"])
                if sort.endswith("desc"):
                    result *= -1
            else:
                result = compare_values(
                    POSITION_ORDER[left["position"]],
                    POSITION_ORDER[right["position"]],
                )
            if result:
                return result
        return compare_values(
            sort_name(left["name"]), sort_name(right["name"])
        ) or compare_values(left["id"], right["id"])

    return cmp_to_key(compare)


def remove_from_lineup(session: Session, club_id: int, player_id: int) -> None:
    from sqlalchemy import delete

    from app.entidades import Escalacao as LineupPlayer

    session.execute(
        delete(LineupPlayer).where(
            LineupPlayer.clube_id == club_id,
            LineupPlayer.jogador_id == player_id,
        )
    )
