import locale
from curses import wrapper
from app import App

def main(stdscr):
    app = App()
    app.run(stdscr=stdscr)

locale.setlocale(locale.LC_ALL, '')

wrapper(main)