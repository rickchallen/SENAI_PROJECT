from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, PositiveInt

#esboço do modelo de jogador de uma outra tentativa de solução
class Jogador(BaseModel):
    id_jogador: int | None = None
    clube_id: PositiveInt | None = None
    nome: str = Field(max_length=100)
    posicao: Literal["GOL", "ZAG", "LAT", "MEI", "ATA"] | None = None
    agilidade: int = Field(ge=1, le=100)
    idade: int = Field(ge=16, le=45)
    valor_base: Decimal = Field(max_digits=6, decimal_places=2)
    condicao: Literal["APTO", "MAL_CONDICIONADO", "DOENTE"] | None = None
    velocidade: int | None = Field(default=None, ge=1, le=99)
    finalizacao: int | None = Field(default=None, ge=1, le=99)
    passe: int | None = Field(default=None, ge=1, le=99)
    drible: int | None = Field(default=None, ge=1, le=99)
    defesa: int | None = Field(default=None, ge=1, le=99)
    fisico: int | None = Field(default=None, ge=1, le=99)
    potencial: int | None = Field(default=None, ge=1, le=99)
    ativo: bool = True
    excluido_em: datetime | None = None
    criado_em: datetime
    atualizado_em: datetime | None = None
    