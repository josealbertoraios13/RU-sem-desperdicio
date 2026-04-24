from model import Menu
from utils import Utils
import curses

class MenuButtons(Menu):
    def show(self) -> None:
        while True:
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
        elif key == 27: # Tecla ESC
            self.box.clear()
            self.box.refresh()
            self.selected = -1
            return True
                
    def _draw_main_container(self) -> None:
        spacing = 2
        
        y, _ = self.box.getmaxyx()
        
        total_height_of_buttons = len(self.options) * spacing
        start_y = (y // 2) - (total_height_of_buttons // 2)
        
        if start_y < 6:
            start_y = 6

        for i, option in enumerate(self.options):
            pos_y = start_y + (i * spacing) 

            if i == self.selected:
                self.box.attron(curses.color_pair(2) | curses.A_REVERSE)
                self.box.addstr(pos_y, Utils.get_mid(option, self.box), option)
                self.box.attroff(curses.color_pair(2) | curses.A_REVERSE)
            else:
                self.box.addstr(pos_y, Utils.get_mid(option, self.box), option)