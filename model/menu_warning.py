import curses
from utils import Utils

from model import Menu

class MenuWarning(Menu):
    def __init__(self, box: curses.window, title, width, height, warnings):
        super().__init__(
            box=box, 
            title=title, 
            width=width, 
            height=height, 
            options=warnings
        )

        self.warnings = self.options
        
    def initialize(self):
        self.box = curses.newwin(self.height, self.width, 1, 5)
        self._draw_title()
        self.box.keypad(True)
        self.box.attron(curses.color_pair(1))
        self.box.box()
        self.box.attroff(curses.color_pair(1))
        self.box.refresh()

        pass

    def show(self) -> None:
        self.initialize()

        while True:
            self._draw_hint()
            self._draw_main_container()
            self.box.refresh()

            if not self._poll_events():
                continue

            return
        
    def _draw_main_container(self) -> None:
        spacing = 2
        y, _ = self.box.getmaxyx()
        
        total_height_of_it = len(self.options) * spacing
        start_y = (y // 2) - (total_height_of_it // 2)
        
        if start_y < 6:
            start_y = 6

        max_y, max_x = self.box.getmaxyx()

        for i, option in enumerate(self.options):
            pos_y = start_y + (i * spacing)
            pos_x = Utils.get_mid(option, self.box)

            if 0 <= pos_y < max_y:
                self.box.addstr(pos_y, max(0, pos_x), option[:max_x-1])

        
    def _poll_events(self):
        c = self.box.getch()
       
        if c == curses.KEY_ENTER or c in [10, 13]:
            self.box.clear()
            self.box.refresh()
            return True
        elif c == 27:
            self.box.clear()
            self.box.refresh()
            return True
       
        
    