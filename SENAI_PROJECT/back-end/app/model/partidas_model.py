from typing import Literal ,Self

from pydantic import BaseModel, Field, model_validator


Formacao = Literal["3-1", "2-2", "2-1-1", "1-2-1"]


class Partida(BaseModel):
	"""Valida os dados enviados para registrar uma partida."""

	mandante_id: int = Field(gt=0)
	visitante_id: int = Field(gt=0)
	gols_mandante: int = Field(ge=0, le=3)
	gols_visitante: int = Field(ge=0, le=3)
	formacao_mandante: Formacao
	formacao_visitante: Formacao

	@model_validator(mode="after")
	def validar_clubes_diferentes(self) -> Self:
		if self.mandante_id == self.visitante_id:
			raise ValueError("mandante_id e visitante_id devem ser diferentes")
		return self
