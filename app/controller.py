from model import MenuWarning
from database import DataBase
from curses import window

# Classe controller pai
class Controller:
    def __init__(self, stdscr : window, data : tuple | DataBase):
        self.stdscr = stdscr
        self.data = data

    def _show_warning(self, title : str, messages : list) -> None:
        warning_menu = MenuWarning(self.stdscr, title=title, width=90, height=30, warnings=messages)
        warning_menu.show()