from app import RegisterController, LoginController, SessionController
from model import MenuButtons
from database import DataBase
from curses import window
import curses

class App():
    def __init__(self):
        curses.curs_set(0)
        curses.use_default_colors()
        
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1) 
        curses.init_pair(3, curses.COLOR_RED, -1)   

        self.data = DataBase()
        self.data.initialize_database()

    def run(self, stdscr : window) -> None:
        while(True):
            main_menu = MenuButtons(stdscr, title="SmartRU", width=60, height=30, options=["[  Login  ]", "[  Register  ]", "[  Exit  ]"])
            main_menu.show()

            if main_menu.selected == -1:
                break
            elif main_menu.selected == 0:
                self._login(stdscr=stdscr)
            elif main_menu.selected == 1:
                self._register(stdscr=stdscr)
            elif main_menu.selected == 2:
                break

    def _register(self, stdscr : window) -> None:
        register_controller = RegisterController(stdscr, self.data)
        register_controller.run()

    def _login(self, stdscr : window) -> None:
        login_controller = LoginController(stdscr, self.data)
        login_controller.run()

        results = login_controller.data_base_message

        is_auth = results.get("success")
        data = results.get("data")

        if is_auth and data:
            session_controller = SessionController(stdscr=stdscr, data=data)
            session_controller.run()
            