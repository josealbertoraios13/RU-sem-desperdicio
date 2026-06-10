import re

from smartru.utils.util import Util


class UserUtils(Util):
    """
    ========================CPF====================
    """
    @staticmethod
    def _clean_cpf(cpf: str) -> str:
        return cpf.replace(".", "").replace("-", "")

    @staticmethod
    def _is_valid_cpf(cpf: str) -> tuple[bool, str]:
        cpf = re.sub(r"\D", "", cpf or "")

        if len(cpf) != 11:
            return False, "CPF deve ter 11 dígitos."

        if cpf == cpf[0] * 11:
            return False, "CPF inválido."

        def calculate_digit(cpf_partial: str, weight: int) -> int:
            total = sum(int(digit) * (weight - index) for index, digit in enumerate(cpf_partial))
            rest = total % 11
            return 0 if rest < 2 else 11 - rest

        first_digit = calculate_digit(cpf[:9], 10)
        second_digit = calculate_digit(cpf[:10], 11)

        if cpf[-2:] != f"{first_digit}{second_digit}":
            return False, "CPF inválido."

        return True, ""

    @staticmethod
    def validate_cpf(cpf: str) -> str:
        tmp_cpf = UserUtils._clean_cpf(cpf)
        is_valid, error_msg = UserUtils._is_valid_cpf(tmp_cpf)
        if not is_valid:
            Util.return_http_exception(message=error_msg)
        return tmp_cpf

    """
    =========================NAME========================
    """
    @staticmethod
    def _is_valid_name(name: str) -> tuple[bool, str]:
        if not name.strip():
            return False, "Nome não pode ser vazio"

        if len(name) >= 50:
            return False, "Nome muito extenso"

        return True, ""

    @staticmethod
    def validate_name(name: str) -> None:
        is_valid, error_msg = UserUtils._is_valid_name(name)
        if not is_valid:
            Util.return_http_exception(message=error_msg)

    """
    ========================E-MAILs============================
    """
    @staticmethod
    def _is_valid_generic_email(email: str) -> tuple[bool, str]:
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email):
            return False, "E-mail inválido!"
        return True, ""

    @staticmethod
    def _is_valid_ufrpe_email(email: str) -> tuple[bool, str]:
        if not re.match(r"^[\w\.-]+@ufrpe\.br$", email):
            return False, "E-mail inválido."
        return True, ""

    @staticmethod
    def validate_email(email: str, role: str = "generic") -> None:
        if role in ("estudante", "funcionario"):
            is_valid, error_msg = UserUtils._is_valid_ufrpe_email(email)
            if not is_valid:
                Util.return_http_exception(message=error_msg)
        else:
            is_valid, error_msg = UserUtils._is_valid_generic_email(email)
            if not is_valid:
                Util.return_http_exception(message=error_msg)

    """
    ============================ROLE============================
    """
    @staticmethod
    def validate_role(role: str) -> None:
        if role not in ("estudante", "funcionario", "convidado"):
            Util.return_http_exception(message="Tipo de usuário inválido")

    """
    ==========================PASSWORD===========================
    """
    @staticmethod
    def _is_valid_password(password: str) -> tuple[bool, str]:
        if len(password) < 8:
            return False, "Deve ter no mínimo 8 caracteres."

        if not re.search(r'[a-z]', password):
            return False, "Deve ter pelo menos uma letra"

        if not re.search(r'[A-Z]', password):
            return False, "Deve ter pelo menos uma letra maiúscula"

        if not re.search(r'\d', password):
            return False, "Deve ter pelo menos um número"

        if not re.search(r'[^a-zA-Z0-9]', password):
            return False, "Deve ter pelo menos um símbolo"

        return True, ""

    @staticmethod
    def validate_password(password: str) -> None:
        is_valid, error_msg = UserUtils._is_valid_password(password=password)
        if not is_valid:
            Util.return_http_exception(message=error_msg)
