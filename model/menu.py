from abc import ABC, abstractmethod
from pyfiglet import figlet_format
from utils import Utils
from curses import window
import curses

class Menu(ABC):

    def __init__(self, box : window, title : str, width : int, height : int, options : list) -> None:
        self.box = box
        self.title = figlet_format(title)
        self.width = width
        self.height = height
        self.options = options
        self.selected = 0
        self.initialize()

    def initialize(self) -> None:
        self.box = curses.newwin(self.height, self.width, 1, 5)
        self.box.keypad(True)
        self.box.attron(curses.color_pair(1))
        self.box.box()
        self._draw_title()
        self.box.attroff(curses.color_pair(1))
        self.box.refresh()

    def _draw_title(self) -> None:
        y, x = self.box.getmaxyx()
        lines = self.title.splitlines()
        for i, line in enumerate(lines):
            mid = Utils.get_mid(line, self.box)
            self.box.attron(curses.color_pair(1))
            self.box.addstr(1 + i, mid, line[:58])
            self.box.attroff(curses.color_pair(1))

    def _draw_hint(self) -> None:
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

    def _next(self) -> None:
        self.selected += 1
        if self.selected >= len(self.options):
            self.selected = 0

    def _previous(self) -> None:
        self.selected -= 1
        if self.selected < 0:
            self.selected = len(self.options) - 1