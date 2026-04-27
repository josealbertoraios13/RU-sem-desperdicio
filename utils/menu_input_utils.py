from utils import Utils
from curses import window
import re
import curses

class MenuInputUtils:
    @staticmethod
    def validate_field(fields : list, values : list, errors : list, idx : int, *args) -> bool:
        label, _ = fields[idx]
        val = values[idx].strip()
        errors[idx] = ""

        if not val:
            errors[idx] = f"{label} é obrigatorio."
            return False

        Validators = {
            "E-mail": MenuInputUtils._validate_generic_email,
            "E-mail UFRPE": MenuInputUtils._validate_ufrpe_email,
            "CPF": MenuInputUtils._validate_cpf,
            "Telefone": MenuInputUtils._validate_telefone,
            "Senha": MenuInputUtils._validate_senha,
            "Conf. Senha": MenuInputUtils._validate_confirmacao_senha,
        }

        if label in Validators:
            return Validators[label](val, errors, idx, fields, values)

        return True

    @staticmethod
    def _validate_generic_email(val : str, errors : list, idx : int, *args) -> bool:
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", val):
            errors[idx] = "E-mail inválido."
            return False
        
        return True
    
    @staticmethod
    def _validate_ufrpe_email(val : str, errors : list, idx : int, *args) -> bool:
        if not re.match(r"^[\w\.-]+@ufrpe\.br$", val):
            errors[idx] = "E-mail inválido."
            return False
        
        return True

    @staticmethod
    def _validate_cpf(val : str, errors : list, idx: int, *args) -> bool:
        if len(re.sub(r"\D", "", val)) != 11:
            errors[idx] = "CPF deve ter 11 dígitos."
            return False
        
        return True

    @staticmethod
    def _validate_telefone(val : str, errors : list, idx : int, *args) -> bool:
        if len(re.sub(r"\D", "", val)) < 10:
            errors[idx] = "Telefone inválido."
            return False
        
        return True

    @staticmethod
    def _validate_senha(val : str, errors : list, idx : int, *args) -> bool:
        if len(val) < 8:
            errors[idx] = "Deve ter no mínimo 8 caracteres."
            return False
        
        if not re.search(r'[a-z]',val):
            errors[idx] = "Deve ter pelo menos uma letra"
            return False

        if not re.search(r'[A-Z]', val):
            errors[idx] = "Deve ter pelo menos uma letra maiúscula"
            return False

        if not re.search(r'\d', val):
            errors[idx] = "Deve ter pelo menos um número"
            return False

        if not re.search(r'[^a-zA-Z0-9]', val):
            errors[idx] = "Deve ter pelo menos um símbolo"
            return False

        return True

    @staticmethod
    def _validate_confirmacao_senha(val : str, errors : list, idx : int, fields : list, values : list) -> bool:
        senha_idx = next(i for i, (label, _) in enumerate(fields) if label == "Senha")
        if val != values[senha_idx]:
            errors[idx] = "As senhas não coincidem."
            return False
        
        return True

    @staticmethod
    def validate_all(fields : list, values : list, errors : list, box : window) -> bool:
        ok = all(MenuInputUtils.validate_field(fields, values, errors, i) for i in range(len(fields)))
        if not ok:
            y, x = box.getmaxyx()

            msg = "!! Corrija os erros antes de cadastrar !!"
            mid = Utils.get_mid(msg, box)

            box.attron(curses.color_pair(3) | curses.A_BOLD)
            box.addstr(y - 3, mid, msg[:x - 4])
            box.attroff(curses.color_pair(3) | curses.A_BOLD)
            box.refresh()
            
        return ok