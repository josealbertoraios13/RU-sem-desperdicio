import curses
import re
import datetime

class Utils:

    #Validations for MenuINput

    @staticmethod
    def validate_field(fields, values, errors, idx) -> bool:
        label, _ = fields[idx]
        val = values[idx].strip()
        errors[idx] = ""

        if not val:
            errors[idx] = f"{label} é obrigatorio."
            return False

        Validators = {
            "E-mail": Utils._validate_generic_email,
            "E-mail UFRPE": Utils._validate_ufrpe_email,
            "CPF": Utils._validate_cpf,
            "Telefone": Utils._validate_telefone,
            "Senha": Utils._validate_senha,
            "Conf. Senha": Utils._validate_confirmacao_senha,
        }

        if label in Validators:
            return Validators[label](val, errors, idx, fields, values)

        return True

    @staticmethod
    def _validate_generic_email(val, errors, idx, fields=None, values=None) -> bool:
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", val):
            errors[idx] = "E-mail inválido."
            return False
        return True
    
    @staticmethod
    def _validate_ufrpe_email(val, errors, idx, fields=None, values=None) -> bool:
        if not re.match(r"^[\w\.-]+@ufrpe+\.br$", val):
            errors[idx] = "E-mail inválido."
            return False
        return True

    @staticmethod
    def _validate_cpf(val, errors, idx, fields=None, values=None) -> bool:
        if len(re.sub(r"\D", "", val)) != 11:
            errors[idx] = "CPF deve ter 11 dígitos."
            return False
        return True

    @staticmethod
    def _validate_telefone(val, errors, idx, fields=None, values=None) -> bool:
        if len(re.sub(r"\D", "", val)) < 10:
            errors[idx] = "Telefone inválido."
            return False
        return True

    @staticmethod
    def _validate_senha(val, errors, idx, fields=None, values=None) -> bool:
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
    def _validate_confirmacao_senha(val, errors, idx, fields, values) -> bool:
        senha_idx = next(i for i, (label, _) in enumerate(fields) if label == "Senha")
        if val != values[senha_idx]:
            errors[idx] = "As senhas não coincidem."
            return False
        return True

    @staticmethod
    def validate_all(fields, values, errors, idx, box) -> bool:
        ok = all(Utils.validate_field(fields, values, errors, i) for i in range(len(fields)))
        if not ok:
            y, x = box.getmaxyx()

            msg = "!! Corrija os erros antes de cadastrar !!"
            mid = Utils.get_mid(msg, box)

            box.attron(curses.color_pair(3) | curses.A_BOLD)
            box.addstr(y - 3, mid, msg[:x - 4])
            box.attroff(curses.color_pair(3) | curses.A_BOLD)
            box.refresh()
        return ok
    
    # For MenuScheduling
    #================================================================================================================
    # --- Constantes de Regras de Negócio ---
    FERIADOS_FIXOS = {
        (1, 1),   # Ano Novo
        (4, 21),  # Tiradentes
        (5, 1),   # Dia do Trabalho
        (9, 7),   # Independência
        (10, 12), # Nossa Senhora Aparecida
        (11, 2),  # Finados
        (11, 15), # Proclamação da República
        (12, 25), # Natal
    }

    @staticmethod
    def format_time_tuple(h: int, m: int) -> str:
        """Formata inteiros de horas e minutos para a string HH:MM."""
        return f"{h:02d}:{m:02d}"

    @staticmethod
    def format_date_input(raw: str) -> str:
        """Formata string numérica para DD/MM/AAAA conforme o usuário digita."""
        raw = raw[:8]
        if len(raw) <= 2:
            return raw
        if len(raw) <= 4:
            return f"{raw[:2]}/{raw[2:]}"
        return f"{raw[:2]}/{raw[2:4]}/{raw[4:]}"

    @staticmethod
    def format_time_input(raw: str) -> str:
        """Formata string numérica para HH:MM conforme o usuário digita."""
        raw = raw[:4]
        if len(raw) <= 2:
            return raw
        return f"{raw[:2]}:{raw[2:]}"

    @staticmethod
    def validate_date(text: str) -> str:
        """Retorna mensagem de erro se a data for inválida, ou string vazia se OK."""
        try:
            day, month, year = text.split("/")
            date = datetime.date(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            return "Data inválida. Use DD/MM/AAAA"

        today = datetime.date.today()
        if date < today:
            return "A data não pode estar no passado"
        if date.weekday() in (5, 6):
            return "O restaurante não funciona aos fins de semana"
        if (date.month, date.day) in Utils.FERIADOS_FIXOS:
            return "Esta data é um feriado nacional"
        return ""

    @staticmethod
    def validate_time(time_str: str, opening: tuple, closing: tuple) -> str:
        """Retorna mensagem de erro caso o horário esteja fora dos limites."""
        if len(time_str) != 5 or ":" not in time_str:
            return "Formato incompleto ou inválido. Use HH:MM"
            
        try:
            h, m = map(int, time_str.split(":"))
        except ValueError:
            return "Horário inválido"
            
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return "Horário inválido"
            
        # Converter para minutos para facilitar verificação
        time_mins = h * 60 + m
        open_mins = opening[0] * 60 + opening[1]
        close_mins = closing[0] * 60 + closing[1]
        
        if not (open_mins <= time_mins <= close_mins):
            abertura_str = Utils.format_time_tuple(*opening)
            fechamento_str = Utils.format_time_tuple(*closing)
            return f"Fora do horário permitido ({abertura_str} às {fechamento_str})"
            
        return ""

    @staticmethod
    def draw_section_label(box: curses.window, row: int, text: str):
        box.attron(curses.color_pair(2))
        box.addstr(row, 5, text)
        box.attroff(curses.color_pair(2))

    @staticmethod
    def draw_selectable(box: curses.window, row: int, col: int, text: str, is_selected: bool, color_pair: int = 2):
        if is_selected:
            box.attron(curses.color_pair(color_pair) | curses.A_REVERSE)
            box.addstr(row, col, text)
            box.attroff(curses.color_pair(color_pair) | curses.A_REVERSE)
        else:
            box.addstr(row, col, text)

    @staticmethod
    def draw_text_field(box: curses.window, row: int, label: str, value: str, is_selected: bool, x_max: int):
        field_w  = x_max - 25
        display  = value[-(field_w - 2):] if len(value) >= field_w - 1 else value
        content  = f" {display:<{field_w - 2}} "

        box.attron(curses.color_pair(2))
        box.addstr(row, 5, f"{label}:")
        box.attroff(curses.color_pair(2))

        col = 5 + len(label) + 2
        if is_selected:
            box.attron(curses.A_REVERSE)
            box.addstr(row, col, content[:field_w])
            box.attroff(curses.A_REVERSE)
        else:
            box.addstr(row, col, content[:field_w])

    @staticmethod
    def draw_error(box: curses.window, row: int, msg: str, x_max: int):
        box.attron(curses.color_pair(3))
        box.addstr(row, 7, f"^ {msg}"[:x_max - 8])
        box.attroff(curses.color_pair(3))

    @staticmethod
    def draw_info(box: curses.window, row: int, msg: str, x_max: int):
        box.attron(curses.color_pair(1))
        box.addstr(row, 5, msg[:x_max - 8])
        box.attroff(curses.color_pair(1))

    @staticmethod
    def clear_line(box: curses.window, row: int, x_max: int):
        box.addstr(row, 7, " " * (x_max - 10))

    # For MenuHistory
    #=================================================================================================================
    @staticmethod
    def sort_schedules(schedules: list):
        """
        Filtra pelo user_id, separa válidos de expirados e ordena:
        - Válidos: do mais próximo ao mais distante (datetime asc)
        - Expirados: do mais recente ao mais antigo (datetime desc)
        """
        now = datetime.datetime.now()

        valid   = []
        expired = []

        for item in schedules:
            dt = Utils.earliest_datetime(item)
            if dt is None:
                expired.append((datetime.datetime.min, item))
                continue
            if dt < now:
                expired.append((dt, item))
            else:
                valid.append((dt, item))

        valid.sort(key=lambda t: t[0])
        expired.sort(key=lambda t: t[0], reverse=True)

        return [item for _, item in valid] + [item for _, item in expired]

    @staticmethod
    def earliest_datetime(item: dict) -> "datetime.datetime | None":
        """
        Retorna o datetime do horário do agendamento,
        ou None se nenhum horário estiver preenchido.
        """
        date_str = item.get("data", "")
        try:
            day, month, year = date_str.split("/")
            base = datetime.date(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            return None

        candidates = []
        t_str = item.get("horario")
        if t_str:
            try:
                hh, mm = t_str.split(":")
                candidates.append(
                    datetime.datetime(base.year, base.month, base.day, int(hh), int(mm))
                )
            except (ValueError, AttributeError):
                pass

        if not candidates:
            # Sem horário: usa meia-noite do dia
            return datetime.datetime(base.year, base.month, base.day, 0, 0)

        return min(candidates)
    
    @staticmethod
    def is_expired(item: dict, now: datetime.datetime) -> bool:
        """Retorna True se o horário do agendamento já passou."""
        date_str = item.get("data", "")
        try:
            day, month, year = date_str.split("/")
            base = datetime.date(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            return True

        # Procura pelo campo horario (formato HH:MM)
        horario_str = item.get("horario")
        if not horario_str:
            # Se não tem horário, compara apenas pela data
            return datetime.datetime(base.year, base.month, base.day) < now
        
        try:
            hh, mm = horario_str.split(":")
            schedule_datetime = datetime.datetime(
                base.year, base.month, base.day, int(hh), int(mm))
            return schedule_datetime < now
        except (ValueError, AttributeError):
            return True

    @staticmethod
    def format_label(item: dict, expired: bool, x_max: int) -> str:
        """
        Formata a linha do botão:
          [EXPIRADO]  DD/MM/AAAA  Almoço 11:30  Jantar 18:30
        ou
                      DD/MM/AAAA  Almoço 11:30  Jantar 18:30
        """
        parts = []

        if expired:
            parts.append("[EXPIRADO]")

        data = item.get("data", "??/??/????")
        parts.append(data)

        refeicao = "almoco" if item.get("refeicao") == "almoco" else "jantar"
        horario = item.get("horario", "")
        parts.append(f"{refeicao} Horário estimado: {horario}".strip())

        label = "  ".join(parts)
        max_w = x_max - 8
        if len(label) > max_w:
            label = label[:max_w - 1] + "…"
        return label


    # For TUI interface
    #=================================================================================================================
    @staticmethod
    def get_mid(text, box):
        y, x = box.getmaxyx()
        return (x - len(text)) // 2