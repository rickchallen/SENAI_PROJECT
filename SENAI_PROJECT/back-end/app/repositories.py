from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entidades import (
    Clube as Club,
)
from app.entidades import (
    Contrato as Contract,
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
from app.entidades import (
    Transacao as Transaction,
)


def get_player(session: Session, player_id: int, lock: bool = False) -> Player | None:
    statement = select(Player).where(
        Player.id == player_id,
        Player.excluido_em.is_(None),
    )
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)


def get_club(session: Session, club_id: int, lock: bool = False) -> Club | None:
    statement = select(Club).where(Club.id == club_id)
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement)


def all_players(session: Session) -> list[Player]:
    return list(
        session.scalars(select(Player).where(Player.excluido_em.is_(None))).all()
    )


def all_clubs(session: Session) -> list[Club]:
    return list(session.scalars(select(Club)).all())


def active_contract(session: Session, player_id: int) -> Contract | None:
    return session.scalar(
        select(Contract).where(
            Contract.jogador_id == player_id,
            Contract.situacao == "ATIVO",
        )
    )


def club_contracts(session: Session, club_id: int) -> dict[int, Contract]:
    contracts = session.scalars(
        select(Contract).where(
            Contract.clube_id == club_id,
            Contract.situacao == "ATIVO",
        )
    ).all()
    return {contract.jogador_id: contract for contract in contracts}


def club_players(session: Session, club_id: int) -> list[Player]:
    return list(
        session.scalars(
            select(Player).where(
                Player.clube_id == club_id,
                Player.excluido_em.is_(None),
            )
        ).all()
    )


def club_transactions(session: Session, club_id: int) -> list[Transaction]:
    return list(
        session.scalars(
            select(Transaction)
            .where(Transaction.clube_id == club_id)
            .order_by(Transaction.criado_em.desc(), Transaction.id.desc())
        ).all()
    )


def player_has_sold_for_club(session: Session, club_id: int, player_id: int) -> bool:
    return (
        session.scalar(
            select(Transaction.id)
            .where(
                Transaction.clube_id == club_id,
                Transaction.jogador_id == player_id,
                Transaction.tipo == "VENDA",
            )
            .limit(1)
        )
        is not None
    )


def lineup_players(session: Session, club_id: int) -> list[Player]:
    return list(
        session.scalars(
            select(Player)
            .join(LineupPlayer, LineupPlayer.jogador_id == Player.id)
            .where(
                LineupPlayer.clube_id == club_id,
                Player.excluido_em.is_(None),
            )
        ).all()
    )


def matches(session: Session, club_id: int | None = None) -> list[Match]:
    statement = select(Match)
    if club_id is not None:
        statement = statement.where(
            (Match.mandante_id == club_id) | (Match.visitante_id == club_id)
        )
    return list(
        session.scalars(
            statement.order_by(Match.jogada_em.desc(), Match.id.desc())
        ).all()
    )


def match_duels(session: Session, match_id: int) -> list[MatchDuel]:
    return list(
        session.scalars(
            select(MatchDuel)
            .where(MatchDuel.partida_id == match_id)
            .order_by(MatchDuel.ordem)
        ).all()
    )


def now_or(value: datetime | None) -> datetime:
    return value or datetime.now()
