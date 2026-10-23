from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Clube(Base):
    __tablename__ = "clubes"
    __table_args__ = (Index("uq_clubes_nome_lower", text("lower(nome)"), unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    sigla: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)
    caixa: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("300.00")
    )
    formacao: Mapped[str | None] = mapped_column(String(5))
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Jogador(Base):
    __tablename__ = "jogadores"
    __table_args__ = (
        CheckConstraint("posicao IN ('GOL', 'ZAG', 'LAT', 'MEI', 'ATA')"),
        CheckConstraint("condicao IN ('APTO', 'MAL_CONDICIONADO', 'DOENTE')"),
        CheckConstraint("agilidade BETWEEN 1 AND 100"),
        CheckConstraint("idade BETWEEN 16 AND 45"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    posicao: Mapped[str] = mapped_column(String(3), nullable=False)
    agilidade: Mapped[int] = mapped_column(Integer, nullable=False)
    idade: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_base: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    condicao: Mapped[str] = mapped_column(String(20), nullable=False)
    clube_id: Mapped[int | None] = mapped_column(ForeignKey("clubes.id"))
    velocidade: Mapped[int] = mapped_column(Integer, nullable=False)
    finalizacao: Mapped[int] = mapped_column(Integer, nullable=False)
    passe: Mapped[int] = mapped_column(Integer, nullable=False)
    drible: Mapped[int] = mapped_column(Integer, nullable=False)
    defesa: Mapped[int] = mapped_column(Integer, nullable=False)
    fisico: Mapped[int] = mapped_column(Integer, nullable=False)
    potencial: Mapped[int] = mapped_column(Integer, nullable=False)
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Contrato(Base):
    __tablename__ = "contratos"
    __table_args__ = (
        CheckConstraint("situacao IN ('ATIVO', 'ENCERRADO', 'RESCINDIDO')"),
        Index(
            "uq_contratos_jogador_ativo",
            "jogador_id",
            unique=True,
            postgresql_where=text("situacao = 'ATIVO'"),
            sqlite_where=text("situacao = 'ATIVO'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jogador_id: Mapped[int] = mapped_column(ForeignKey("jogadores.id"), nullable=False)
    clube_id: Mapped[int] = mapped_column(ForeignKey("clubes.id"), nullable=False)
    valor_compra: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    fidelidade_ate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    situacao: Mapped[str] = mapped_column(String(12), nullable=False)
    iniciado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    encerrado_em: Mapped[datetime | None] = mapped_column(DateTime)


class Transacao(Base):
    __tablename__ = "transacoes"
    __table_args__ = (CheckConstraint("tipo IN ('COMPRA', 'VENDA')"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clube_id: Mapped[int] = mapped_column(ForeignKey("clubes.id"), nullable=False)
    jogador_id: Mapped[int] = mapped_column(ForeignKey("jogadores.id"), nullable=False)
    nome_jogador: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(String(6), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    taxa: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    multa: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    lucro: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    variacao_caixa: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Escalacao(Base):
    __tablename__ = "escalacoes"
    __table_args__ = (UniqueConstraint("jogador_id"),)

    clube_id: Mapped[int] = mapped_column(ForeignKey("clubes.id"), primary_key=True)
    jogador_id: Mapped[int] = mapped_column(
        ForeignKey("jogadores.id"), primary_key=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Partida(Base):
    __tablename__ = "partidas"
    __table_args__ = (
        CheckConstraint("mandante_id <> visitante_id"),
        CheckConstraint("gols_mandante BETWEEN 0 AND 3"),
        CheckConstraint("gols_visitante BETWEEN 0 AND 3"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mandante_id: Mapped[int] = mapped_column(ForeignKey("clubes.id"), nullable=False)
    visitante_id: Mapped[int] = mapped_column(ForeignKey("clubes.id"), nullable=False)
    gols_mandante: Mapped[int] = mapped_column(Integer, nullable=False)
    gols_visitante: Mapped[int] = mapped_column(Integer, nullable=False)
    formacao_mandante: Mapped[str] = mapped_column(String(5), nullable=False)
    formacao_visitante: Mapped[str] = mapped_column(String(5), nullable=False)
    jogada_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class DueloPartida(Base):
    __tablename__ = "duelos_partida"
    __table_args__ = (
        CheckConstraint("ordem BETWEEN 1 AND 6"),
        UniqueConstraint("partida_id", "ordem"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partida_id: Mapped[int] = mapped_column(ForeignKey("partidas.id"), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    clube_atacante_id: Mapped[int] = mapped_column(
        ForeignKey("clubes.id"), nullable=False
    )
    atacante_id: Mapped[int] = mapped_column(ForeignKey("jogadores.id"), nullable=False)
    defensor_id: Mapped[int] = mapped_column(ForeignKey("jogadores.id"), nullable=False)
    nome_atacante: Mapped[str] = mapped_column(String(100), nullable=False)
    nome_defensor: Mapped[str] = mapped_column(String(100), nullable=False)
    posicao_atacante: Mapped[str] = mapped_column(String(3), nullable=False)
    posicao_defensor: Mapped[str] = mapped_column(String(3), nullable=False)
    condicao_atacante: Mapped[str] = mapped_column(String(20), nullable=False)
    condicao_defensor: Mapped[str] = mapped_column(String(20), nullable=False)
    atributo_ataque: Mapped[str] = mapped_column(String(10), nullable=False)
    atributo_defesa: Mapped[str] = mapped_column(String(10), nullable=False)
    valor_ataque: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_defesa: Mapped[int] = mapped_column(Integer, nullable=False)
    gol: Mapped[bool] = mapped_column(Boolean, nullable=False)
