from curses import window

class Utils:
    @staticmethod
    def get_mid(text : str, box : window) -> int:
        y, x = box.getmaxyx()
        return (x - len(text)) // 2