from model.menu import Menu
from utils import Utils, MenuInputUtils
from curses import window
import curses

class MenuInput(Menu):

    def __init__(self, 
                box : window, 
                title : 
                str, width : int, height : int, 
                fields : list, 
                button_label : str = "[ Confirmar ]", verify : bool = True
            ):
        super().__init__(
            box=box,
            title=title,
            width=width,
            height=height,
            options=fields,  
        )
        self.fields = fields
        self.values = [""] * len(fields)
        self.errors = [""] * len(fields)
        self.button_label = button_label
        self.verify = verify
        self.cancelled = False 
        
    def show(self) -> None:
        while True:
            self._draw_fields()
            self._draw_main_container()
            self._draw_hint()       
            self.box.refresh()

            if not self._poll_events():
                continue

            return

    def _poll_events(self) -> bool:
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
            if self.selected == len(self.fields):
                self.box.clear()
                self.box.refresh()
                return True
            else:
                if self.verify:
                    MenuInputUtils.validate_field(self.fields, self.values, self.errors, self.selected)
                self._next()
        elif key == '\x1b': # ESC
            self.cancelled = True
            self.box.clear()
            self.box.refresh()
            return True
        elif key in (curses.KEY_BACKSPACE, '\x7f', '\x08'):
            if self.selected < len(self.fields):
                self.values[self.selected] = self.values[self.selected][:-1]
                self.errors[self.selected] = ""

        elif isinstance(key, str) and key.isprintable():

            if self.selected < len(self.fields):

                label, _ = self.fields[self.selected]

                if label == "CPF":
                    raw = self.values[self.selected].replace(".", "").replace("-", "")
                    if len(raw) <= 11:
                        raw += key
                        self.values[self.selected] = MenuInputUtils.format_cpf_input(raw)

                elif len(self.values[self.selected]) < 60: # máximo de caracteres
                    self.values[self.selected] += key
                    self.errors[self.selected] = ""

        return False

    def _draw_main_container(self) -> None:
        y, x = self.box.getmaxyx()
        
        button_y = y - 4 
        
        if self.selected == len(self.fields):
            self.box.attron(curses.color_pair(2) | curses.A_REVERSE)
            self.box.addstr(button_y, Utils.get_mid(self.button_label, self.box), self.button_label)
            self.box.attroff(curses.color_pair(2) | curses.A_REVERSE)
        else:
            self.box.addstr(button_y, Utils.get_mid(self.button_label, self.box), self.button_label)

    def _draw_fields(self) -> None:
        y, x = self.box.getmaxyx()

        title_lines = len(self.title.splitlines()) + 1
        field_w = x - 25 # largura dos campo de entrada

        for i, (label, is_pass) in enumerate(self.fields):
            row = title_lines + 1 + i * 3 # Define qual linha o campo vai ser desenhado

            self.box.attron(curses.color_pair(2))
            self.box.addstr(row, 5, f"{label}:")
            self.box.attroff(curses.color_pair(2))

            # Máscara da senha
            display = ("*" * len(self.values[i])) if is_pass else self.values[i] 
            # "Move" conteúdo da entrada para esquerda scroll-effect
            display = display[-(field_w - 2):] if len(display) >= field_w - 1 else display
            content = f" {display:<{field_w - 2}} "

            if i == self.selected:
                self.box.attron(curses.A_REVERSE)
                self.box.addstr(row, 5 + len(label) + 2, content[:field_w])
                self.box.attroff(curses.A_REVERSE)
            else:
                self.box.addstr(row, 5 + len(label) + 2, content[:field_w])

            if self.errors[i]:
                self.box.attron(curses.color_pair(3))
                self.box.addstr(row + 1, 7, f"^ {self.errors[i]}"[:x - 8])
                self.box.attroff(curses.color_pair(3))
            else:
                self.box.addstr(row + 1, 7, " " * (x - 10))

    # Overrided
    def _next(self) -> None:
        self.selected += 1
        if self.selected > len(self.fields):   
            self.selected = 0

    # Overrrided
    def _previous(self) -> None:
        self.selected -= 1
        if self.selected < 0:
            self.selected = len(self.fields)   

    def get_result(self) -> dict:
        return dict(zip(
            [f[0] for f in self.fields],
            [v.strip() for v in self.values]
        ))