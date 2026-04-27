from model.menu import Menu
from utils import Utils, MenuSchuduleUtils
import curses

# Feriados nacionais fixos (mês, dia)
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

ALMOCO_ABERTURA   = (11, 30)
ALMOCO_FECHAMENTO = (14,  0)
JANTAR_ABERTURA   = (18, 30)
JANTAR_FECHAMENTO = (22,  0)
 
HORARIO_ALMOCO = f"{MenuSchuduleUtils.format_time_tuple(*ALMOCO_ABERTURA)} – {MenuSchuduleUtils.format_time_tuple(*ALMOCO_FECHAMENTO)}"
HORARIO_JANTAR = f"{MenuSchuduleUtils.format_time_tuple(*JANTAR_ABERTURA)} – {MenuSchuduleUtils.format_time_tuple(*JANTAR_FECHAMENTO)}"

class MenuScheduling(Menu):

    def __init__(self, box: curses.window, title, width: int, height: int):
        self.checkboxes         = ["Almoço", "Jantar"]      # índices 0-1
        self.checked            = [False, False]
        self.date_value         = ""
        self.lunch_time_value   = ""
        self.dinner_time_value  = ""
        self.errors             = {
            "checkboxes":  "",
            "date":        "",
            "lunch_time":  "",
            "dinner_time": ""
        }
        self.cancelled          = False
        self.result             = {}

        self._TOTAL_ITEMS     = 6
        self._DATE_IDX        = 2
        self._LUNCH_TIME_IDX  = 3
        self._DINNER_TIME_IDX = 4
        self._BTN_IDX         = 5

        super().__init__(
            box=box,
            title=title,
            width=width,
            height=height,
            options=list(range(self._TOTAL_ITEMS)),
        )

    def show(self):
        self.initialize()
        while True:
            self._draw_main_container()
            self._draw_hint()
            self._draw_title()
            self.box.refresh()

            if not self._poll_events():
                continue
            return

    def _poll_events(self):
        try:
            key = self.box.get_wch()
        except curses.error:
            return False

        if isinstance(key, str) and key in ('\n', '\r'):
            key = 10

        if key == curses.KEY_UP:
            self._previous()
            return False

        elif key == curses.KEY_DOWN:
            self._next()
            return False

        elif key in (curses.KEY_ENTER, 10, 13):
            # Checkboxes – toggle
            if self.selected in (0, 1):
                self.checked[self.selected] = not self.checked[self.selected]
                self.errors["checkboxes"] = ""
                self._next()

                return False

            # Validar e Avançar em Data
            if self.selected == self._DATE_IDX:
                if self.date_value:
                    self.errors["date"] = MenuSchuduleUtils.validate_date(self.date_value)
                self._next()
                return False

            # Validar e Avançar em Horário de Almoço
            if self.selected == self._LUNCH_TIME_IDX:
                if self.lunch_time_value:
                    self.errors["lunch_time"] = MenuSchuduleUtils.validate_time(self.lunch_time_value, ALMOCO_ABERTURA, ALMOCO_FECHAMENTO)
                self._next()

                return False

            # Validar e Avançar em Horário de Jantar
            if self.selected == self._DINNER_TIME_IDX:
                if self.dinner_time_value:
                    self.errors["dinner_time"] = MenuSchuduleUtils.validate_time(self.dinner_time_value, JANTAR_ABERTURA, JANTAR_FECHAMENTO)
                self._next()

                return False

            # Botão confirmar
            if self.selected == self._BTN_IDX:
                if self._validate_all():
                    self._build_result()
                    self.box.clear()
                    self.box.refresh()
                    return True
                
                return False

        elif isinstance(key, str) and key == '\x1b':  # ESC
            self.cancelled = True
            self.box.clear()
            self.box.refresh()
            return True

        # Tratar apagar caracteres (backspace)
        elif key in (curses.KEY_BACKSPACE, '\x7f', '\x08'):
            if self.selected == self._DATE_IDX and self.date_value:
                self.date_value = self.date_value[:-1]
                self.errors["date"] = ""
            elif self.selected == self._LUNCH_TIME_IDX and self.lunch_time_value:
                self.lunch_time_value = self.lunch_time_value[:-1]
                self.errors["lunch_time"] = ""
            elif self.selected == self._DINNER_TIME_IDX and self.dinner_time_value:
                self.dinner_time_value = self.dinner_time_value[:-1]
                self.errors["dinner_time"] = ""

        # Tratar digitação
        elif isinstance(key, str) and key.isprintable():
            if self.selected == self._DATE_IDX:
                raw = self.date_value.replace("/", "")
                if len(raw) < 8:
                    raw += key
                    self.date_value = MenuSchuduleUtils.format_date_input(raw)
                    self.errors["date"] = ""

            elif self.selected == self._LUNCH_TIME_IDX:
                raw = self.lunch_time_value.replace(":", "")
                if len(raw) < 4:
                    raw += key
                    self.lunch_time_value = MenuSchuduleUtils.format_time_input(raw)
                    self.errors["lunch_time"] = ""

            elif self.selected == self._DINNER_TIME_IDX:
                raw = self.dinner_time_value.replace(":", "")
                if len(raw) < 4:
                    raw += key
                    self.dinner_time_value = MenuSchuduleUtils.format_time_input(raw)
                    self.errors["dinner_time"] = ""

        return False

    def _draw_main_container(self):
        self.box.clear()
        self.box.box()
        y, x = self.box.getmaxyx()
        title_lines = len(self.title.splitlines()) + 2
        row = title_lines

        # ---- Checkboxes ----
        MenuSchuduleUtils.draw_section_label(box=self.box, row=row, text="Refeição (selecione ao menos uma):")
        row += 1
        for i, label in enumerate(self.checkboxes):
            mark   = "X" if self.checked[i] else " "
            text   = f"  [{mark}] {label}"
            is_sel = (self.selected == i)
            MenuSchuduleUtils.draw_selectable(box=self.box,row=row, col=5, text=text, is_selected=is_sel, color_pair=curses.color_pair(2))
            row += 1

        if self.errors["checkboxes"]:
            MenuSchuduleUtils.draw_error(box=self.box,row=row, msg=self.errors["checkboxes"], x_max=x)
        else:
            MenuSchuduleUtils.clear_line(box=self.box, row=row, x_max=x)
        row += 1

        # ---- Campo Data ----
        MenuSchuduleUtils.draw_section_label(box=self.box, row=row, text="Data do agendamento (DD/MM/AAAA):")
        row += 1
        MenuSchuduleUtils.draw_text_field(
            box=self.box,
            row=row, label="Data", value=self.date_value,
            is_selected=(self.selected == self._DATE_IDX),
            x_max=x
        )
        row += 1
        if self.errors["date"]:
            MenuSchuduleUtils.draw_error(box=self.box, row=row, msg=self.errors["date"],x_max=x)
        else:
            MenuSchuduleUtils.clear_line(box=self.box, row=row, x_max=x)
        row += 1

        # ---- Aviso de horários ----
        info = self._build_schedule_info()
        MenuSchuduleUtils.draw_info(box=self.box,row=row, msg=info, x_max=x)
        row += 1

        # ---- Campos de Horário Dinâmicos ----
        if any(self.checked):
            MenuSchuduleUtils.draw_section_label(box=self.box, row=row, text="Horário estimado de chegada (HH:MM) – opcional:")
            row += 1
            
            # Campo de Almoço
            if self.checked[0]:
                MenuSchuduleUtils.draw_text_field(
                    box=self.box,
                    row=row, label="Almoço", value=self.lunch_time_value,
                    is_selected=(self.selected == self._LUNCH_TIME_IDX),
                    x_max=x
                )
                row += 1
                if self.errors["lunch_time"]:
                    MenuSchuduleUtils.draw_error(box=self.box, row=row, msg=self.errors["lunch_time"], x_max=x)
                else:
                    MenuSchuduleUtils.clear_line(box=self.box, row=row, x_max=x)
                row += 1
                
            # Campo de Jantar
            if self.checked[1]:
                MenuSchuduleUtils.draw_text_field(
                    box=self.box,
                    row=row, label="Jantar", value=self.dinner_time_value,
                    is_selected=(self.selected == self._DINNER_TIME_IDX),
                    x_max=x
                )
                row += 1
                if self.errors["dinner_time"]:
                    MenuSchuduleUtils.draw_error(box=self.box, row=row, msg=self.errors["dinner_time"], x_max=x)
                else:
                    MenuSchuduleUtils.clear_line(box=self.box, row=row, x_max=x)
                row += 1
                
        row += 1 # Espaçamento antes do botão

        # ---- Botão Confirmar ----
        label = "[ Confirmar Agendamento ]"
        col   = Utils.get_mid(label, self.box)
        if self.selected == self._BTN_IDX:
            self.box.attron(curses.color_pair(2) | curses.A_REVERSE)
            self.box.addstr(row, col, label)
            self.box.attroff(curses.color_pair(2) | curses.A_REVERSE)
        else:
            self.box.attron(curses.color_pair(2))
            self.box.addstr(row, col, label)
            self.box.attroff(curses.color_pair(2))

    def _build_schedule_info(self):
        almoco, jantar = self.checked[0], self.checked[1]
        if almoco and jantar:
            return f"Horários: Almoço {HORARIO_ALMOCO}  |  Jantar {HORARIO_JANTAR}"
        if almoco:
            return f"Horário do almoço: {HORARIO_ALMOCO}"
        if jantar:
            return f"Horário do jantar: {HORARIO_JANTAR}"
        return f"Horários: Almoço {HORARIO_ALMOCO}  |  Jantar {HORARIO_JANTAR}"

    def _validate_all(self):
        ok = True

        # Validação Refeições
        if not any(self.checked):
            self.errors["checkboxes"] = "Selecione ao menos uma refeição"
            self.selected = 0
            ok = False

        # Validação Data
        date_err = MenuSchuduleUtils.validate_date(self.date_value) if self.date_value else "Informe a data"
        self.errors["date"] = date_err
        if date_err:
            if ok:
                self.selected = self._DATE_IDX
            ok = False

        # Validação Horário Almoço
        if self.checked[0] and self.lunch_time_value:
            lunch_err = MenuSchuduleUtils.validate_time(self.lunch_time_value, ALMOCO_ABERTURA, ALMOCO_FECHAMENTO)
            self.errors["lunch_time"] = lunch_err
            if lunch_err:
                if ok:
                    self.selected = self._LUNCH_TIME_IDX
                ok = False
        else:
            self.errors["lunch_time"] = ""

        # Validação Horário Jantar
        if self.checked[1] and self.dinner_time_value:
            dinner_err = MenuSchuduleUtils.validate_time(self.dinner_time_value, JANTAR_ABERTURA, JANTAR_FECHAMENTO)
            self.errors["dinner_time"] = dinner_err
            if dinner_err:
                if ok:
                    self.selected = self._DINNER_TIME_IDX
                ok = False
        else:
            self.errors["dinner_time"] = ""

        return ok

    def _build_result(self):
        self.result = {
            "almoco":  self.checked[0],
            "jantar":  self.checked[1],
            "data":    self.date_value,
            "horario_almoco": self.lunch_time_value if self.checked[0] and self.lunch_time_value else None,
            "horario_jantar": self.dinner_time_value if self.checked[1] and self.dinner_time_value else None,
        }

    def _next(self):
        while True:
            self.selected += 1
            if self.selected >= self._TOTAL_ITEMS:
                self.selected = 0
            
            if self.selected == self._LUNCH_TIME_IDX and not self.checked[0]:
                continue
            if self.selected == self._DINNER_TIME_IDX and not self.checked[1]:
                continue
            break

    def _previous(self):
        while True:
            self.selected -= 1
            if self.selected < 0:
                self.selected = self._TOTAL_ITEMS - 1
            
            if self.selected == self._LUNCH_TIME_IDX and not self.checked[0]:
                continue
            if self.selected == self._DINNER_TIME_IDX and not self.checked[1]:
                continue
            break