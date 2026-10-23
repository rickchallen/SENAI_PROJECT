from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain import (
    ATTACK_ATTRIBUTE,
    FORMATIONS,
    attribute_with_condition,
    bad_request,
    conflict,
    format_datetime,
    now_brasilia,
    parse_integer,
    required,
    sort_name,
)
from app.entidades import (
    Clube as Club,
)
from app.entidades import (
    DueloPartida as MatchDuel,
)
from app.entidades import (
    Escalacao as LineupPlayer,
)
from app.entidades import (
    Jogador as Player,
)
from app.entidades import (
    Partida as Match,
)
from app.repositories import (
    all_clubs,
    get_player,
    lineup_players,
    match_duels,
    matches,
)
from app.services.common import player_order, player_payload, require_club


def get_lineup(session: Session, club_id: int) -> dict[str, Any]:
    club = require_club(session, club_id)
    players = sorted(lineup_players(session, club.id), key=player_order)
    return {
        "club_id": club.id,
        "formation": club.formacao,
        "complete": len(players) == 5,
        "players": [player_payload(player) for player in players],
    }


def set_lineup(session: Session, club_id: int, body: dict[str, Any]) -> dict[str, Any]:
    club = require_club(session, club_id, lock=True)
    formation = required(body, "formation")
    if not isinstance(formation, str) or formation not in FORMATIONS:
        bad_request("formation possui um valor inválido.")
    raw_player_ids = required(body, "player_ids")
    if not isinstance(raw_player_ids, list) or len(raw_player_ids) != 5:
        bad_request("player_ids deve conter exatamente cinco ids.")
    player_ids = [
        parse_integer(value, "player_ids", 1, 2_147_483_647) for value in raw_player_ids
    ]
    if len(set(player_ids)) != 5:
        bad_request("player_ids não pode conter ids repetidos.")
    players = []
    for player_id in player_ids:
        player = get_player(session, player_id)
        if player is None:
            from app.domain import not_found

            not_found("Jogador não encontrado.")
        players.append(player)
    if any(player.clube_id != club.id for player in players):
        conflict("Todos os titulares precisam fazer parte do elenco do clube.")
    if any(player.condicao == "DOENTE" for player in players):
        conflict("Jogador DOENTE não pode ser escalado.")
    defense, midfield, attack = FORMATIONS[formation]
    positions = [player.posicao for player in players]
    if (
        positions.count("GOL") != 1
        or sum(position in ("ZAG", "LAT") for position in positions) != defense
        or positions.count("MEI") != midfield
        or positions.count("ATA") != attack
    ):
        conflict("As posições dos titulares não correspondem à formação.")
    session.execute(delete(LineupPlayer).where(LineupPlayer.clube_id == club.id))
    club.formacao = formation
    now = now_brasilia()
    session.add_all(
        LineupPlayer(clube_id=club.id, jogador_id=player.id, criado_em=now)
        for player in players
    )
    session.flush()
    return get_lineup(session, club.id)


def play_match(session: Session, body: dict[str, Any]) -> dict[str, Any]:
    home_id = parse_integer(
        required(body, "home_club_id"), "home_club_id", 1, 2_147_483_647
    )
    away_id = parse_integer(
        required(body, "away_club_id"), "away_club_id", 1, 2_147_483_647
    )
    if home_id == away_id:
        bad_request("home_club_id e away_club_id devem ser diferentes.")
    home = require_club(session, home_id, lock=True)
    away = require_club(session, away_id, lock=True)
    home_roster = _complete_roster(session, home)
    away_roster = _complete_roster(session, away)
    match = Match(
        mandante_id=home.id,
        visitante_id=away.id,
        gols_mandante=0,
        gols_visitante=0,
        formacao_mandante=home.formacao,
        formacao_visitante=away.formacao,
        jogada_em=now_brasilia(),
    )
    session.add(match)
    session.flush()
    goals = [0, 0]
    duels = []
    pairings = (
        (1, home, home_roster[1][3], away, away_roster[0]),
        (2, home, home_roster[1][2], away, away_roster[1][0]),
        (3, home, home_roster[1][1], away, away_roster[1][1]),
        (4, away, away_roster[1][3], home, home_roster[0]),
        (5, away, away_roster[1][2], home, home_roster[1][0]),
        (6, away, away_roster[1][1], home, home_roster[1][1]),
    )
    for order, attacking_club, attacker, _defending_club, defender in pairings:
        attribute, field = ATTACK_ATTRIBUTE[attacker.posicao]
        attack_value = attribute_with_condition(
            getattr(attacker, field), attacker.condicao
        )
        defense_value = attribute_with_condition(defender.defesa, defender.condicao)
        goal = attack_value > defense_value
        if goal:
            goals[0 if attacking_club.id == home.id else 1] += 1
        duel = MatchDuel(
            partida_id=match.id,
            ordem=order,
            clube_atacante_id=attacking_club.id,
            atacante_id=attacker.id,
            defensor_id=defender.id,
            nome_atacante=attacker.nome,
            nome_defensor=defender.nome,
            posicao_atacante=attacker.posicao,
            posicao_defensor=defender.posicao,
            condicao_atacante=attacker.condicao,
            condicao_defensor=defender.condicao,
            atributo_ataque=attribute,
            atributo_defesa="defending",
            valor_ataque=attack_value,
            valor_defesa=defense_value,
            gol=goal,
        )
        session.add(duel)
        duels.append(duel)
    match.gols_mandante, match.gols_visitante = goals
    session.flush()
    return match_payload(match, home, away, duels)


def _complete_roster(session: Session, club: Club) -> tuple[Player, list[Player]]:
    if not club.formacao:
        conflict("O clube não possui uma escalação completa.")
    players = sorted(lineup_players(session, club.id), key=player_order)
    if len(players) != 5 or any(player.condicao == "DOENTE" for player in players):
        conflict("O clube não possui uma escalação completa.")
    goalkeepers = [player for player in players if player.posicao == "GOL"]
    lines = [player for player in players if player.posicao != "GOL"]
    if len(goalkeepers) != 1 or len(lines) != 4:
        conflict("O clube não possui uma escalação completa.")
    return goalkeepers[0], lines


def list_matches(session: Session, club_id: int | None) -> list[dict[str, Any]]:
    if club_id is not None:
        require_club(session, club_id)
    result = []
    for match in matches(session, club_id):
        home = require_club(session, match.mandante_id)
        away = require_club(session, match.visitante_id)
        result.append(match_payload(match, home, away, None))
    return result


def get_match(session: Session, match_id: int) -> dict[str, Any]:
    match = session.scalar(select(Match).where(Match.id == match_id))
    if match is None:
        from app.domain import not_found

        not_found("Partida não encontrada.")
    home = require_club(session, match.mandante_id)
    away = require_club(session, match.visitante_id)
    return match_payload(match, home, away, match_duels(session, match.id))


def standings(session: Session) -> list[dict[str, Any]]:
    rows = {
        club.id: {
            "position": 0,
            "club_id": club.id,
            "club_name": club.nome,
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0,
        }
        for club in all_clubs(session)
    }
    for match in matches(session):
        home = rows[match.mandante_id]
        away = rows[match.visitante_id]
        home["played"] += 1
        away["played"] += 1
        home["goals_for"] += match.gols_mandante
        home["goals_against"] += match.gols_visitante
        away["goals_for"] += match.gols_visitante
        away["goals_against"] += match.gols_mandante
        if match.gols_mandante > match.gols_visitante:
            home["wins"] += 1
            home["points"] += 3
            away["losses"] += 1
        elif match.gols_mandante < match.gols_visitante:
            away["wins"] += 1
            away["points"] += 3
            home["losses"] += 1
        else:
            home["draws"] += 1
            away["draws"] += 1
            home["points"] += 1
            away["points"] += 1
    ordered = list(rows.values())
    for row in ordered:
        row["goal_difference"] = row["goals_for"] - row["goals_against"]
    ordered.sort(
        key=lambda row: (
            -row["points"],
            -row["goal_difference"],
            -row["goals_for"],
            sort_name(row["club_name"]),
            row["club_id"],
        )
    )
    for position, row in enumerate(ordered, start=1):
        row["position"] = position
    return ordered


def match_payload(
    match: Match,
    home: Club,
    away: Club,
    duels: list[MatchDuel] | None,
) -> dict[str, Any]:
    result = (
        "MANDANTE"
        if match.gols_mandante > match.gols_visitante
        else "VISITANTE"
        if match.gols_mandante < match.gols_visitante
        else "EMPATE"
    )
    payload: dict[str, Any] = {
        "id": match.id,
        "played_at": format_datetime(match.jogada_em),
        "home": {
            "club_id": home.id,
            "club_name": home.nome,
            "formation": match.formacao_mandante,
            "goals": match.gols_mandante,
        },
        "away": {
            "club_id": away.id,
            "club_name": away.nome,
            "formation": match.formacao_visitante,
            "goals": match.gols_visitante,
        },
        "result": result,
    }
    if duels is not None:
        payload["duels"] = [duel_payload(duel) for duel in duels]
    return payload


def duel_payload(duel: MatchDuel) -> dict[str, Any]:
    return {
        "order": duel.ordem,
        "attacking_club_id": duel.clube_atacante_id,
        "attacker": {
            "player_id": duel.atacante_id,
            "player_name": duel.nome_atacante,
            "position": duel.posicao_atacante,
            "condition": duel.condicao_atacante,
            "attribute": duel.atributo_ataque,
            "value": duel.valor_ataque,
        },
        "defender": {
            "player_id": duel.defensor_id,
            "player_name": duel.nome_defensor,
            "position": duel.posicao_defensor,
            "condition": duel.condicao_defensor,
            "attribute": duel.atributo_defesa,
            "value": duel.valor_defesa,
        },
        "goal": duel.gol,
    }
