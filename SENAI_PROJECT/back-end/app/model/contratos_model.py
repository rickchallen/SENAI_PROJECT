from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from clubes_model import SituacaoContrato

class ModelBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

class SituacaoContrato(str, Enum):
    ATIVO = "ATIVO"
    ENCERRADO = "ENCERRADO"
    RESCINDIDO = "RESCINDIDO"

class Contrato(ModelBase):
    id: int | None = None
    jogador_id: int
    clube_id: int
    valor_compra: Decimal = Field(max_digits=6, decimal_places=2)
    fidelidade_ate: datetime
    situacao: SituacaoContrato
    iniciado_em: datetime = Field(default_factory=datetime.now)
    encerrado_em: datetime | None = None
