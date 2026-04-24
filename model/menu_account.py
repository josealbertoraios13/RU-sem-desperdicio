from model import Menu
from utils import Utils
import curses

class MenuAccount(Menu):
    def __init__(self, box, title, width, height, options, role, occupant, email, cpf, extra_label=None, extra_value=None):
        self.role        = role
        self.occupant    = occupant
        self.email       = email
        self.cpf         = cpf
        self.extra_label = extra_label
        self.extra_value = extra_value
        super().__init__(box, title, width, height, options)

    def _build_rows(self):
        rows = [
            ("Usuario",  self.occupant),
            ("E-mail",   self.email),
            ("CPF",      self.cpf),
        ]
        if self.extra_label and self.extra_value:
            rows.append((self.extra_label, self.extra_value))
        return rows

    def _draw_main_container(self):
        y, x = self.box.getmaxyx()
        title_lines = len(self.title.splitlines())
        current_y   = 1 + title_lines + 1

        role_mid = Utils.get_mid(self.role, self.box)
        self.box.attron(curses.color_pair(1) | curses.A_BOLD)
        self.box.addstr(current_y, role_mid, self.role[:x - 4])
        self.box.attroff(curses.color_pair(1) | curses.A_BOLD)
        current_y += 2

        col_label = 4
        col_value = 22

        for label, value in self._build_rows():
            self.box.attron(curses.color_pair(1))
            self.box.addstr(current_y, col_label, f"{label}:"[:x - col_label - 1])
            self.box.attroff(curses.color_pair(1))

            self.box.attron(curses.color_pair(2))
            self.box.addstr(current_y, col_value, str(value)[:x - col_value - 2])
            self.box.attroff(curses.color_pair(2))

            current_y += 1

        current_y += 1

        for i, option in enumerate(self.options):
            btn_mid = Utils.get_mid(option, self.box)
            if i == self.selected:
                if option == "[ Deletar conta ]":
                    self.box.attron(curses.color_pair(3) | curses.A_REVERSE)
                    self.box.addstr(current_y, btn_mid, option[:x - 4])
                    self.box.attroff(curses.color_pair(3) | curses.A_REVERSE)
                else:
                    self.box.attron(curses.color_pair(2) | curses.A_REVERSE)
                    self.box.addstr(current_y, btn_mid, option[:x - 4])
                    self.box.attroff(curses.color_pair(2) | curses.A_REVERSE)
            else:
                self.box.attron(curses.color_pair(1))
                self.box.addstr(current_y, btn_mid, option[:x - 4])
                self.box.attroff(curses.color_pair(1))
            current_y += 2

    def show(self):
        while True:
            self.box.clear()
            self.box.attron(curses.color_pair(1))
            self.box.box()
            self._draw_title()
            self.box.attroff(curses.color_pair(1))

            self._draw_main_container()
            self._draw_hint()
            self.box.refresh()

            if not self._poll_event():
                continue

            return

    def _poll_event(self):
        key = self.box.getch()

        if key == curses.KEY_DOWN:
            self._next()
            return False
        elif key == curses.KEY_UP:
            self._previous()
            return False
        elif key == curses.KEY_ENTER or key in [10, 13]:
            self.box.clear()
            self.box.refresh()
            return True
        elif key == 27:
            self.selected = -1
            self.box.clear()
            self.box.refresh()
            return True