from abc import ABC, abstractmethod
from pyfiglet import figlet_format
from utils import Utils
import curses

class Menu(ABC):

    # Constructor - Initialize the object with this parameters
    def __init__(self, box : curses.window, title, width, height, options):
        self.box = box
        self.title = figlet_format(title)
        self.width = width
        self.height = height
        self.options = options
        self.selected = 0
        self.initialize()

    def initialize(self):
        self.box = curses.newwin(self.height, self.width, 1, 5)
        self.box.keypad(True)
        self.box.attron(curses.color_pair(1))
        self.box.box()
        self._draw_title()
        self.box.attroff(curses.color_pair(1))
        self.box.refresh()

    def _draw_title(self):
        y, x = self.box.getmaxyx()
        lines = self.title.splitlines()
        for i, line in enumerate(lines):
            mid = Utils.get_mid(line, self.box)
            self.box.attron(curses.color_pair(1))
            self.box.addstr(1 + i, mid, line[:58])
            self.box.attroff(curses.color_pair(1))

    def _draw_hint(self):
        y, x = self.box.getmaxyx()
        hint = "Setas: navegar   Enter: confirmar   Esc: sair"
        mid = Utils.get_mid(hint, self.box)
        self.box.attron(curses.color_pair(1))
        self.box.addstr(y - 2, mid, hint[:x - 4])
        self.box.attroff(curses.color_pair(1))

    @abstractmethod
    def _draw_main_container(self) -> None:
        pass

    @abstractmethod
    def show(self) -> None:
        pass

    def _next(self):
        self.selected += 1
        if self.selected >= len(self.options):
            self.selected = 0

    def _previous(self):
        self.selected -= 1
        if self.selected < 0:
            self.selected = len(self.options) - 1