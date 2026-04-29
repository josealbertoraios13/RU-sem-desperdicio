from model import Menu
from utils import Utils
from curses import window
import curses

class MenuModal(Menu):
    def __init__(self, box: window, title : str, width : int, height : int, options : list, message : str):
        super().__init__(box, title, width, height, options)
        self.message = message
        self.cancelled = False

    def show(self) -> None:
        while True:
            self._draw_main_container()
            self._draw_hint()
            self.box.refresh()

            if not self._poll_events():
                continue

            return

    def _poll_events(self) -> bool:
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
            self.cancelled = True

            return True
        
        return False

    def _draw_main_container(self) -> None:
        spacing = 2
        
        y, _ = self.box.getmaxyx()
        
        total_height_of_buttons = len(self.options) * spacing
        start_y = (y // 2) - (total_height_of_buttons // 2)

        if start_y < 6:
            start_y = 6

        self.box.addstr(start_y - 5, Utils.get_mid(self.message, self.box), self.message)

        for i, option in enumerate(self.options):
            pos_y = start_y + (i * spacing) 

            if i == self.selected:
                if option == "[ Sim ]":
                    self.box.attron(curses.color_pair(3) | curses.A_REVERSE)
                    self.box.addstr(pos_y, Utils.get_mid(option, self.box), option)
                    self.box.attroff(curses.color_pair(3) | curses.A_REVERSE)
                else:
                    self.box.attron(curses.color_pair(2) | curses.A_REVERSE)
                    self.box.addstr(pos_y, Utils.get_mid(option, self.box), option)
                    self.box.attroff(curses.color_pair(2) | curses.A_REVERSE)
            else:
                self.box.addstr(pos_y, Utils.get_mid(option, self.box), option)