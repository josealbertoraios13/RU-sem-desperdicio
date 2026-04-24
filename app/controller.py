from model import MenuWarning

class Controller:
    def __init__(self, stdscr, data):
        self.stdscr = stdscr
        self.data = data

    def _show_warning(self, title, messages):
        warning_menu = MenuWarning(self.stdscr, title=title, width=90, height=30, warnings=messages)
        warning_menu.show()