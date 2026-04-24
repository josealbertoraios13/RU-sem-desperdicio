from model import Menu
from utils import Utils
import curses

class MenuProfile(Menu):

    def __init__(self, box, title, width, height, options, user):
        _, self.occupant, self.role, self.email, self.cpf, self.matricula, self.codigo_funcionario = user
        super().__init__(box, title, width, height, options)

    def _draw_main_container(self):
        y, x = self.box.getmaxyx()

        title_lines = len(self.title.splitlines())
        subtitle_start = 1 + title_lines + 1   

        margin_left = 8

        self.box.attron(curses.color_pair(1) | curses.A_BOLD)
        self.box.addstr(subtitle_start, margin_left, str.upper(self.role)[:x - 4])
        self.box.attroff(curses.color_pair(1) | curses.A_BOLD)

        self.box.attron(curses.color_pair(2))
        self.box.addstr(subtitle_start + 1, margin_left, self.occupant[:x - 4])
        self.box.attroff(curses.color_pair(2))

        btn_start = subtitle_start + 6
        for i, option in enumerate(self.options):
            btn_mid = Utils.get_mid(option, self.box)
            if i == self.selected:
                self.box.attron(curses.color_pair(2) | curses.A_REVERSE)
                self.box.addstr(btn_start + i * 2, btn_mid, option[:x - 4])
                self.box.attroff(curses.color_pair(2) | curses.A_REVERSE)
            else:
                self.box.attron(curses.color_pair(1))
                self.box.addstr(btn_start + i * 2, btn_mid, option[:x - 4])
                self.box.attroff(curses.color_pair(1))

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

            if not self._poll_events():
                continue

            return

    def _poll_events(self):
        key = self.box.getch()

        if key == curses.KEY_UP:
            self._previous()
            return False
        elif key == curses.KEY_DOWN:
            self._next()
            return False
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return True
        elif key == 27: 
            self.selected = -1
            return True