from model import Menu
from utils import Utils, MenuHistoryUtils

import curses
import datetime


class MenuHistory(Menu):
    def __init__(self, box: curses.window, title: str, width: int, height: int, schedules: list):
        self.cancelled = False
        self.enter = False
        self.selected_schedule = None

        self._sorted_items = MenuHistoryUtils.sort_schedules(schedules)

        self._scroll_offset = 0

        super().__init__(
            box=box,
            title=title,
            width=width,
            height=height,
            options=self._sorted_items,  # cada item == um "botão"
        )

    def show(self):
        self.initialize()
        while True:
            self._draw_main_container()
            self._draw_hint()
            self.box.refresh()
            if not self._poll_events():
                continue
            return

    def _poll_events(self):
        try:
            key = self.box.get_wch()
        except curses.error:
            return False

        if isinstance(key, str) and key in ("\n", "\r"):
            key = 10

        if key == curses.KEY_UP:
            self._previous()
            self._adjust_scroll()
            return False
        elif key == curses.KEY_DOWN:
            self._next()
            self._adjust_scroll()
            return False
        elif key in (curses.KEY_ENTER, 10, 13):
            if self._sorted_items:
                self.selected_schedule = self._sorted_items[self.selected]
            self.box.clear()
            self.box.refresh()
            self.enter = True
            return True
        elif isinstance(key, str) and key == "\x1b":  # ESC
            self.cancelled = True
            self.box.clear()
            self.box.refresh()
            return True

        return False

    # Scroll
    def _visible_rows(self):
        y, _ = self.box.getmaxyx()
        title_lines = len(self.title.splitlines()) + 2
        header_lines = 3  # contador de agendamentos do dia + separador
        footer_lines = 3  # hint + borda inferior
        return max(1, y - title_lines - header_lines - footer_lines)

    def _adjust_scroll(self):
        visible = self._visible_rows()
        if self.selected < self._scroll_offset:
            self._scroll_offset = self.selected
        elif self.selected >= self._scroll_offset + visible:
            self._scroll_offset = self.selected - visible + 1

    def _draw_main_container(self):
        y, x = self.box.getmaxyx()
        title_lines = len(self.title.splitlines()) + 2
        row = title_lines

        # ---- Contador de agendamentos para hoje ----
        today_count = self._count_today()
        counter_text = (
            f"Agendamentos para hoje: {today_count}"
            if today_count > 0
            else "Nenhum agendamento para hoje"
        )
        self.box.attron(curses.color_pair(2))
        self.box.addstr(row, 5, counter_text[: x - 8])
        self.box.attroff(curses.color_pair(2))
        row += 1

        # Linha separadora
        self.box.attron(curses.color_pair(1))
        self.box.addstr(row, 2, "─" * (x - 4))
        self.box.attroff(curses.color_pair(1))
        row += 2

        if not self._sorted_items:
            msg = "Nenhum agendamento encontrado."
            self.box.attron(curses.color_pair(1))
            self.box.addstr(row, Utils.get_mid(msg, self.box), msg[: x - 8])
            self.box.attroff(curses.color_pair(1))
            return

        # ---- Botões com scroll ----
        visible = self._visible_rows()
        now = datetime.datetime.now()
        end_idx = min(self._scroll_offset + visible, len(self._sorted_items))

        for list_pos in range(self._scroll_offset, end_idx):
            item = self._sorted_items[list_pos]
            expired = MenuHistoryUtils.is_expired(item, now)
            label = MenuHistoryUtils.format_label(item, expired, x)

            is_sel = list_pos == self.selected

            if is_sel:
                self.box.attron(curses.color_pair(2) | curses.A_REVERSE)
                self.box.addstr(row, 4, label[: x - 6])
                self.box.attroff(curses.color_pair(2) | curses.A_REVERSE)
            elif expired:
                # Expirados com cor diferenciada (color_pair 3 = vermelho/aviso)
                self.box.attron(curses.color_pair(3))
                self.box.addstr(row, 4, label[: x - 6])
                self.box.attroff(curses.color_pair(3))
            else:
                self.box.addstr(row, 4, label[: x - 6])

            row += 1

        # ---- Indicadores de scroll ----
        if self._scroll_offset > 0:
            indicator = "▲ mais acima"
            self.box.attron(curses.color_pair(1))
            self.box.addstr(title_lines + 3, x - len(indicator) - 3, indicator)
            self.box.attroff(curses.color_pair(1))

        if self._scroll_offset + visible < len(self._sorted_items):
            indicator = "▼ mais abaixo"
            self.box.attron(curses.color_pair(1))
            self.box.addstr(y - 4, x - len(indicator) - 3, indicator)
            self.box.attroff(curses.color_pair(1))

    def _count_today(self) -> int:
        """
        Conta agendamentos do usuário para o dia atual cujo horário
        ainda não passou (horário atual < horário do agendamento).
        """
        now = datetime.datetime.now()
        today = now.date()
        count = 0

        for item in self._sorted_items:
            date_str = item.get("data", "")
            try:
                day, month, year = date_str.split("/")
                ag_date = datetime.date(int(year), int(month), int(day))
            except (ValueError, AttributeError):
                continue

            if ag_date != today:
                continue

            t_str = item.get("horario")
            if not t_str:
                continue
            try:
                hh, mm = t_str.split(":")
                ag_dt = datetime.datetime(
                    today.year, today.month, today.day, int(hh), int(mm)
                )
                if ag_dt > now:
                    count += 1
            except (ValueError, AttributeError):
                pass

        return count

    def _next(self):
        if not self._sorted_items:
            return
        self.selected += 1
        if self.selected >= len(self._sorted_items):
            self.selected = 0

    def _previous(self):
        if not self._sorted_items:
            return
        self.selected -= 1
        if self.selected < 0:
            self.selected = len(self._sorted_items) - 1
