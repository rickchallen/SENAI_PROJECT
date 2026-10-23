from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModelBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class Formacao(str, Enum):
    TRES_UM = "3-1"
    DOIS_DOIS = "2-2"
    DOIS_UM_UM = "2-1-1"
    UM_DOIS_UM = "1-2-1"


class Posicao(str, Enum):
    GOL = "GOL"
    ZAG = "ZAG"
    LAT = "LAT"
    MEI = "MEI"
    ATA = "ATA"


class CondicaoJogador(str, Enum):
    APTO = "APTO"
    MAL_CONDICIONADO = "MAL_CONDICIONADO"
    DOENTE = "DOENTE"


class CondicaoDuelo(str, Enum):
    APTO = "APTO"
    MAL_CONDICIONADO = "MAL_CONDICIONADO"


class SituacaoContrato(str, Enum):
    ATIVO = "ATIVO"
    ENCERRADO = "ENCERRADO"
    RESCINDIDO = "RESCINDIDO"


class TipoTransacao(str, Enum):
    COMPRA = "COMPRA"
    VENDA = "VENDA"


class AtributoDuelo(str, Enum):
    SHOOTING = "shooting"
    PASSING = "passing"
    DRIBBLING = "dribbling"
    DEFENDING = "defending"
    
class Clube(ModelBase):
    id: int | None = None
    nome: str = Field(max_length=60)
    sigla: str = Field(min_length=3, max_length=3)
    caixa: Decimal = Field(default=Decimal("300.00"), max_digits=10, decimal_places=2)
    formacao: Formacao | None = None
    criado_em: datetime = Field(default_factory=datetime.now)
