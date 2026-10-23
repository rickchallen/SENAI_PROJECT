from typing import Any

from sqlalchemy.orm import Session

from app.domain import (
    API_ATTRIBUTE_FIELDS,
    CONDITIONS,
    POSITIONS,
    bad_request,
    calculate_base_value,
    calculate_overall,
    conflict,
    fold_accents,
    market_value,
    now_brasilia,
    parse_enum,
    parse_integer,
    required,
    validate_player_name,
)
from app.entidades import Jogador as Player
from app.repositories import all_players, get_club
from app.services.common import (
    compare_players,
    player_payload,
    remove_from_lineup,
    require_player,
)


def create_player(session: Session, body: dict[str, Any]) -> dict[str, Any]:
    name = validate_player_name(required(body, "name"))
    position = parse_enum(required(body, "position"), "position", POSITIONS)
    agility = parse_integer(required(body, "agility"), "agility", 1, 100)
    age = parse_integer(required(body, "age"), "age", 16, 45)
    if age >= 35 and agility > 85:
        bad_request("agility deve ser no máximo 85 a partir dos 35 anos.")
    values = tuple(
        parse_integer(required(body, api_field), api_field, 1, 99)
        for api_field in API_ATTRIBUTE_FIELDS
    )
    if sum(values) > 480:
        bad_request("A soma dos seis atributos não pode passar de 480.")
    potential = parse_integer(required(body, "potential"), "potential", 1, 99)
    maximum_attribute = max(values)
    if potential < maximum_attribute:
        bad_request("potential não pode ser menor que o maior atributo.")
    if age >= 33 and potential != maximum_attribute:
        bad_request("potential deve ser igual ao maior atributo a partir dos 33 anos.")
    overall = calculate_overall(position, values)
    base_value = calculate_base_value(overall, potential, age)
    now = now_brasilia()
    player = Player(
        nome=name,
        posicao=position,
        agilidade=agility,
        idade=age,
        valor_base=base_value,
        condicao="APTO",
        clube_id=None,
        velocidade=values[0],
        finalizacao=values[1],
        passe=values[2],
        drible=values[3],
        defesa=values[4],
        fisico=values[5],
        potencial=potential,
        excluido_em=None,
        criado_em=now,
        atualizado_em=now,
    )
    session.add(player)
    session.flush()
    return player_payload(player)


def get_player_payload(session: Session, player_id: int) -> dict[str, Any]:
    return player_payload(require_player(session, player_id))


def update_player(
    session: Session, player_id: int, body: dict[str, Any]
) -> dict[str, Any]:
    player = require_player(session, player_id, lock=True)
    name = validate_player_name(required(body, "name"))
    position = parse_enum(required(body, "position"), "position", POSITIONS)
    agility = parse_integer(required(body, "agility"), "agility", 1, 100)
    age = parse_integer(required(body, "age"), "age", 16, 45)
    if age < player.idade:
        conflict("A idade não pode ser menor que a idade atual.")
    if player.clube_id is not None and position != player.posicao:
        conflict("A posição de um jogador com clube não pode ser alterada.")
    if age >= 35 and agility > 85:
        bad_request("agility deve ser no máximo 85 a partir dos 35 anos.")
    player.nome = name
    player.posicao = position
    player.agilidade = agility
    player.idade = age
    player.atualizado_em = now_brasilia()
    return player_payload(player)


def update_condition(
    session: Session, player_id: int, body: dict[str, Any]
) -> dict[str, Any]:
    player = require_player(session, player_id, lock=True)
    condition = parse_enum(required(body, "condition"), "condition", CONDITIONS)
    if player.condicao == "DOENTE" and condition == "APTO":
        conflict("Um jogador DOENTE não pode passar diretamente para APTO.")
    if condition != player.condicao:
        if condition == "DOENTE" and player.clube_id is not None:
            remove_from_lineup(session, player.clube_id, player.id)
        player.condicao = condition
        player.atualizado_em = now_brasilia()
    return player_payload(player)


def delete_player(session: Session, player_id: int) -> None:
    player = require_player(session, player_id, lock=True)
    if player.clube_id is not None:
        conflict("Jogador que está no elenco de um clube não pode ser excluído.")
    player.excluido_em = now_brasilia()
    player.atualizado_em = player.excluido_em


def list_players(session: Session, filters: dict[str, Any]) -> dict[str, Any]:
    club_id = filters["club_id"]
    if club_id is not None and get_club(session, club_id) is None:
        from app.domain import not_found

        not_found("Clube não encontrado.")

    players = all_players(session)
    search = filters["search"]
    if search is not None:
        needle = fold_accents(search)
        players = [player for player in players if needle in fold_accents(player.nome)]
    if filters["position"] is not None:
        players = [
            player for player in players if player.posicao == filters["position"]
        ]
    if filters["condition"] is not None:
        players = [
            player for player in players if player.condicao == filters["condition"]
        ]
    if filters["free"] is not None:
        players = [
            player for player in players if (player.clube_id is None) == filters["free"]
        ]
    if club_id is not None:
        players = [player for player in players if player.clube_id == club_id]
    if filters["min_age"] is not None:
        players = [player for player in players if player.idade >= filters["min_age"]]
    if filters["max_age"] is not None:
        players = [player for player in players if player.idade <= filters["max_age"]]
    if filters["min_value"] is not None:
        players = [
            player for player in players if market_value(player) >= filters["min_value"]
        ]
    if filters["max_value"] is not None:
        players = [
            player for player in players if market_value(player) <= filters["max_value"]
        ]

    payloads = [player_payload(player) for player in players]
    payloads.sort(key=compare_players(filters["sorts"]))
    total_items = len(payloads)
    limit = filters["limit"]
    page = filters["page"]
    start = (page - 1) * limit
    return {
        "data": payloads[start : start + limit],
        "meta": {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": (total_items + limit - 1) // limit,
        },
    }
