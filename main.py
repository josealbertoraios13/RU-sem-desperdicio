from curses import wrapper 
from app.app import App

def main(stdscr):
    app = App()
    app.run(stdscr=stdscr)

wrapper(main)