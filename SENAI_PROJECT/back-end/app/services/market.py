from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.domain import (
    bad_request,
    conflict,
    format_datetime,
    market_value,
    now_brasilia,
    parse_brasilia_datetime,
    penalty_rate,
    remaining_days,
    round_money,
)
from app.entidades import Contrato as Contract
from app.entidades import Transacao as Transaction
from app.repositories import (
    active_contract,
    club_players,
    club_transactions,
    get_player,
    player_has_sold_for_club,
)
from app.services.common import (
    remove_from_lineup,
    require_club,
    require_player,
)


def buy_player(
    session: Session, player_id: int, body: dict[str, Any]
) -> dict[str, Any]:
    club_id_value = body.get("club_id")
    if club_id_value is None:
        bad_request("club_id é obrigatório.")
    if isinstance(club_id_value, bool) or not isinstance(club_id_value, (int, float)):
        bad_request("club_id deve ser um inteiro positivo.")
    if isinstance(club_id_value, float) and not club_id_value.is_integer():
        bad_request("club_id deve ser um inteiro positivo.")
    club_id = int(club_id_value)
    if not 1 <= club_id <= 2_147_483_647:
        bad_request("club_id deve ser um inteiro positivo.")
    loyalty_until = parse_brasilia_datetime(body.get("loyalty_until"))
    now = now_brasilia()
    duration = loyalty_until - now
    if duration.total_seconds() <= 0 or duration.total_seconds() > 1095 * 86400:
        bad_request("loyalty_until deve estar no futuro e em até 1.095 dias.")
    player = require_player(session, player_id, lock=True)
    club = require_club(session, club_id, lock=True)
    if player.clube_id is not None:
        conflict("O jogador não está livre.")
    if player_has_sold_for_club(session, club.id, player.id):
        conflict("O clube não pode recomprar um jogador que já vendeu.")
    if len(club_players(session, club.id)) >= 12:
        conflict("O clube já atingiu o limite de 12 jogadores.")
    value = market_value(player)
    fee = (
        round_money(value * Decimal("0.05"))
        if value > Decimal("30.00")
        else Decimal("0.00")
    )
    total_cost = value + fee
    if total_cost > club.caixa / Decimal("2"):
        conflict("O custo da compra excede 50% do caixa do clube.")
    club.caixa -= total_cost
    player.clube_id = club.id
    player.atualizado_em = now
    contract = Contract(
        jogador_id=player.id,
        clube_id=club.id,
        valor_compra=value,
        fidelidade_ate=loyalty_until,
        situacao="ATIVO",
        iniciado_em=now,
        encerrado_em=None,
    )
    transaction = Transaction(
        clube_id=club.id,
        jogador_id=player.id,
        nome_jogador=player.nome,
        tipo="COMPRA",
        valor=value,
        taxa=fee,
        multa=Decimal("0.00"),
        lucro=None,
        variacao_caixa=-total_cost,
        criado_em=now,
    )
    session.add_all((contract, transaction))
    session.flush()
    return {
        **transaction_payload(transaction),
        "contract": {
            "purchase_value": value,
            "loyalty_until": format_datetime(loyalty_until),
            "status": "ATIVO",
        },
        "club_cash": club.caixa,
    }


def sell_player(session: Session, player_id: int) -> dict[str, Any]:
    player = require_player(session, player_id, lock=True)
    if player.clube_id is None:
        conflict("Jogador livre não pode ser vendido.")
    club = require_club(session, player.clube_id, lock=True)
    contract = active_contract(session, player.id)
    if contract is None:
        conflict("O jogador não possui contrato ativo.")
    now = now_brasilia()
    value = market_value(player)
    days = remaining_days(contract.fidelidade_ate, now)
    rate = penalty_rate(days)
    penalty = (
        min(round_money(value * Decimal(rate) / Decimal("100")), Decimal("10.00"))
        if rate
        else Decimal("0.00")
    )
    profit = value - contract.valor_compra
    if profit > 0:
        commission = round_money(
            min(profit, Decimal("10.00")) * Decimal("0.10")
            + max(Decimal("0.00"), profit - Decimal("10.00")) * Decimal("0.20")
        )
    else:
        commission = Decimal("0.00")
    credit = value - penalty - commission
    club.caixa += credit
    player.clube_id = None
    player.atualizado_em = now
    contract.situacao = "RESCINDIDO" if penalty > 0 else "ENCERRADO"
    contract.encerrado_em = now
    remove_from_lineup(session, club.id, player.id)
    transaction = Transaction(
        clube_id=club.id,
        jogador_id=player.id,
        nome_jogador=player.nome,
        tipo="VENDA",
        valor=value,
        taxa=commission,
        multa=penalty,
        lucro=profit,
        variacao_caixa=credit,
        criado_em=now,
    )
    session.add(transaction)
    session.flush()
    return {
        **transaction_payload(transaction),
        "purchase_value": contract.valor_compra,
        "remaining_days": days,
        "penalty_rate": rate,
        "contract_status": contract.situacao,
        "club_cash": club.caixa,
    }


def get_transactions(
    session: Session, club_id: int, filters: dict[str, Any]
) -> dict[str, Any]:
    require_club(session, club_id)
    if filters["player_id"] is not None:
        if get_player(session, filters["player_id"]) is None:
            from app.domain import not_found

            not_found("Jogador não encontrado.")
    transactions = _filtered_transactions(club_transactions(session, club_id), filters)
    total_spent = sum(
        (item.valor + item.taxa for item in transactions if item.tipo == "COMPRA"),
        Decimal("0.00"),
    )
    total_received = sum(
        (item.variacao_caixa for item in transactions if item.tipo == "VENDA"),
        Decimal("0.00"),
    )
    return {
        "data": [transaction_payload(item) for item in transactions],
        "summary": {
            "total_spent": round_money(total_spent),
            "total_received": round_money(total_received),
            "total_fees": round_money(
                sum((item.taxa for item in transactions), Decimal("0.00"))
            ),
            "total_penalties": round_money(
                sum((item.multa for item in transactions), Decimal("0.00"))
            ),
            "total_profit": round_money(
                sum(
                    (
                        item.lucro or Decimal("0.00")
                        for item in transactions
                        if item.tipo == "VENDA"
                    ),
                    Decimal("0.00"),
                )
            ),
        },
    }


def export_transactions(session: Session, club_id: int, filters: dict[str, Any]) -> str:
    require_club(session, club_id)
    player_id = filters["player_id"]
    if player_id is not None and get_player(session, player_id) is None:
        from app.domain import not_found

        not_found("Jogador não encontrado.")
    all_transactions = _filtered_transactions(
        club_transactions(session, club_id), filters
    )
    rows = ["data_hora;tipo;jogador;valor;taxa_ou_comissao;multa;lucro;variacao_caixa"]
    for transaction in all_transactions:
        profit = "" if transaction.lucro is None else _csv_money(transaction.lucro)
        cells = (
            format_datetime(transaction.criado_em),
            transaction.tipo,
            _csv_field(transaction.nome_jogador),
            _csv_money(transaction.valor),
            _csv_money(transaction.taxa),
            _csv_money(transaction.multa),
            profit,
            _csv_money(transaction.variacao_caixa),
        )
        rows.append(";".join(cells))
    return "\n".join(rows) + "\n"


def transaction_payload(transaction: Transaction) -> dict[str, Any]:
    return {
        "id": transaction.id,
        "club_id": transaction.clube_id,
        "player_id": transaction.jogador_id,
        "player_name": transaction.nome_jogador,
        "type": transaction.tipo,
        "value": transaction.valor,
        "fee": transaction.taxa,
        "penalty": transaction.multa,
        "profit": transaction.lucro,
        "cash_change": transaction.variacao_caixa,
        "created_at": format_datetime(transaction.criado_em),
    }


def _filtered_transactions(
    transactions: list[Transaction], filters: dict[str, Any]
) -> list[Transaction]:
    selected = filters["types"]
    player_id = filters["player_id"]
    return [
        item
        for item in transactions
        if (selected is None or item.tipo in selected)
        and (player_id is None or item.jogador_id == player_id)
    ]


def _csv_money(value: Decimal) -> str:
    return f"{value:.2f}".replace(".", ",")


def _csv_field(value: str) -> str:
    if ";" in value or '"' in value:
        return f'"{value.replace(chr(34), chr(34) * 2)}"'
    return value
