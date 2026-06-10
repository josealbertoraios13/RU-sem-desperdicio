import re

from pydantic import BaseModel, field_validator


class QueueCollaborationRequest(BaseModel):
    cpf: str

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)

        if len(digits) != 11:
            raise ValueError("CPF deve ter 11 dígitos.")

        if digits == digits[0] * 11:
            raise ValueError("CPF inválido.")

        def _calc_digit(partial: str, weight: int) -> int:
            total = sum(int(d) * (weight - i) for i, d in enumerate(partial))
            rest = total % 11
            return 0 if rest < 2 else 11 - rest

        if digits[-2:] != f"{_calc_digit(digits[:9], 10)}{_calc_digit(digits[:10], 11)}":
            raise ValueError("CPF inválido.")

        return digits
