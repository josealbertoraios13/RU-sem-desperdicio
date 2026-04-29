from datetime import datetime
from .controller import Controller
from model import MenuScheduling
from curses import window
from database import DataBase

class ScheduleMealController(Controller):
    def __init__(self, stdscr : window, data : tuple, user_id : str, database : DataBase):
        super().__init__(stdscr, data)
        self.user_id = user_id
        self.database = database

    def run(self) -> None:
        menu_scheduling = MenuScheduling(
            box=self.stdscr, title="Agendar", width=70, height=30
        )

        menu_scheduling.show()

        if menu_scheduling.selected == menu_scheduling._BTN_IDX:
            menu_result = menu_scheduling.result
            lunch = (str)(menu_result.get("almoco"))
            dinner = (str)(menu_result.get("jantar"))
            date = (str)(menu_result.get("data"))
            lunch_time = (str)(menu_result.get("horario_almoco"))
            dinner_time = (str)(menu_result.get("horario_jantar"))

            if date:
                date = datetime.strptime(date, "%d/%m/%Y").date()

            h, w = self.stdscr.getmaxyx()

            if lunch and dinner:
                lunch_result = self.database.schedule_meal(
                    date=date, meal_type="almoco", user_id=self.user_id, time=lunch_time
                )
                dinner_result = self.database.schedule_meal(
                    date=date, meal_type="jantar", user_id=self.user_id, time=dinner_time,
                )

                self._show_warning("Agendamento Realizado", [lunch_result, dinner_result])

                return
            
            if lunch:
                lunch_result = self.database.schedule_meal(
                    date=date, meal_type="almoco", user_id=self.user_id, time=lunch_time
                )

                self._show_warning("Agendamento Realizado", [lunch_result])
                return
            
            if dinner:
                dinner_result = self.database.schedule_meal(
                    date=date, meal_type="jantar", user_id=self.user_id, time=dinner_time,
                )
                self._show_warning("Agendamento Realizado", [dinner_result])
