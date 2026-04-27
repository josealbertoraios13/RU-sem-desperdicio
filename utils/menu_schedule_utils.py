from curses import window
import datetime
import curses

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
class MenuSchuduleUtils:

    @staticmethod
    def format_time_tuple(h: int, m: int) -> str:
        # Formata inteiros de horas e minutos para a string HH:MM.
        return f"{h:02d}:{m:02d}"

    @staticmethod
    def format_date_input(raw: str) -> str:
        # Formata string numérica para DD/MM/AAAA conforme o usuário digita.
        raw = raw[:8]
        if len(raw) <= 2:
            return raw
        if len(raw) <= 4:
            return f"{raw[:2]}/{raw[2:]}"
        return f"{raw[:2]}/{raw[2:4]}/{raw[4:]}"

    @staticmethod
    def format_time_input(raw: str) -> str:
        # Formata string numérica para HH:MM conforme o usuário digita.
        raw = raw[:4]
        if len(raw) <= 2:
            return raw
        return f"{raw[:2]}:{raw[2:]}"

    @staticmethod
    def validate_date(text: str) -> str:
        # Retorna mensagem de erro se a data for inválida, ou string vazia se OK.
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
        
        if (date.month, date.day) in FERIADOS_FIXOS:
            return "Esta data é um feriado nacional"
        
        return ""

    @staticmethod
    def validate_time(time_str: str, opening: tuple, closing: tuple) -> str:
        # Retorna mensagem de erro caso o horário esteja fora dos limites.
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
            opening_str = MenuSchuduleUtils.format_time_tuple(*opening)
            closing_str = MenuSchuduleUtils.format_time_tuple(*closing)
            return f"Fora do horário permitido ({opening_str} às {closing_str})"
            
        return ""

    @staticmethod
    def draw_section_label(box: window, row: int, text: str) -> None:
        box.attron(curses.color_pair(2))
        box.addstr(row, 5, text)
        box.attroff(curses.color_pair(2))

    @staticmethod
    def draw_selectable(box: window, row: int, col: int, text: str, is_selected: bool, color_pair: int = 2) -> None:
        if is_selected:
            box.attron(curses.color_pair(color_pair) | curses.A_REVERSE)
            box.addstr(row, col, text)
            box.attroff(curses.color_pair(color_pair) | curses.A_REVERSE)
        else:
            box.addstr(row, col, text)

    @staticmethod
    def draw_text_field(box: window, row: int, label: str, value: str, is_selected: bool, x_max: int) -> None:
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
            return
        
        box.addstr(row, col, content[:field_w])

    @staticmethod
    def draw_error(box: curses.window, row: int, msg: str, x_max: int) -> None:
        box.attron(curses.color_pair(3))
        box.addstr(row, 7, f"^ {msg}"[:x_max - 8])
        box.attroff(curses.color_pair(3))

    @staticmethod
    def draw_info(box: curses.window, row: int, msg: str, x_max: int) -> None:
        box.attron(curses.color_pair(1))
        box.addstr(row, 5, msg[:x_max - 8])
        box.attroff(curses.color_pair(1))

    @staticmethod
    def clear_line(box: curses.window, row: int, x_max: int) -> None:
        box.addstr(row, 7, " " * (x_max - 10))