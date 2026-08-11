from enum import Enum
from typing import Literal

from pydantic import BaseModel


class StatusComponente(str, Enum):
    OK = "ok"
    INDISPONIVEL = "indisponivel"


class HealthResponse(BaseModel):
    aplicacao: Literal[StatusComponente.OK] = StatusComponente.OK
    banco: StatusComponente
