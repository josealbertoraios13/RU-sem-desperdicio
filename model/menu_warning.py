from utils import Utils
from model import Menu
from curses import window
import curses
class MenuWarning(Menu):
    def __init__(self, box: window, title : str, width : int, height : int, warnings : list):
        super().__init__(
            box=box, 
            title=title, 
            width=width, 
            height=height, 
            options=warnings
        )

        self.warnings = self.options

    def show(self) -> None:

        while True:
            self._draw_hint()
            self._draw_main_container()
            self.box.refresh()

            if not self._poll_events():
                continue

            return
        
    def _draw_main_container(self) -> None:
        spacing = 2
        max_y, max_x = self.box.getmaxyx()
        
        total_height_of_it = len(self.options) * spacing
        start_y = (max_y // 2) - (total_height_of_it // 2)
        
        if start_y < 6:
            start_y = 6

        for i, option in enumerate(self.options):
            pos_y = start_y + (i * spacing)
            pos_x = Utils.get_mid(option, self.box)

            if 0 <= pos_y < max_y:
                self.box.addstr(pos_y, max(0, pos_x), option[:max_x-1])

        
    def _poll_events(self) -> bool:
        c = self.box.getch()
       
        if c == curses.KEY_ENTER or c in [10, 13]:
            self.box.clear()
            self.box.refresh()

            return True
        
        elif c == 27:
            self.box.clear()
            self.box.refresh()

            return True
       
        return False
        
    