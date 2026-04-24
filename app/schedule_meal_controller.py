from datetime import datetime
from .controller import Controller
from model import MenuScheduling, MenuWarning


class ScheduleMealController(Controller):
    def __init__(self, stdscr, data, user_id, database):
        self.user_id = user_id
        self.database = database
        super().__init__(stdscr, data)

    def run(self):
        menu_scheduling = MenuScheduling(
            box=self.stdscr, title="Agendar", width=70, height=30
        )

        menu_scheduling.show()

        if menu_scheduling.selected == menu_scheduling._BTN_IDX:
            menu_result = menu_scheduling.result
            lunch = menu_result.get("almoco")
            dinner = menu_result.get("jantar")
            date = menu_result.get("data")
            lunch_time = menu_result.get("horario_almoco")
            dinner_time = menu_result.get("horario_jantar")

            if date:
                date = datetime.strptime(date, "%d/%m/%Y").date()

            h, w = self.stdscr.getmaxyx()

            result = ""

            if lunch and dinner:
                lunch_result = self.database.schedule_meal(
                    date=date, meal_type="almoco", user_id=self.user_id, time=lunch_time
                )
                dinner_result = self.database.schedule_meal(
                    date=date,
                    meal_type="jantar",
                    user_id=self.user_id,
                    time=dinner_time,
                )

                is_success_menu = MenuWarning(
                    box=self.stdscr,
                    title="Agendamento Realizado",
                    width=90,
                    height=30,
                    warnings=[lunch_result, dinner_result],
                )

                is_success_menu.show()
            elif lunch:
                result = self.database.schedule_meal(
                    date=date, meal_type="almoco", user_id=self.user_id, time=lunch_time
                )

                is_success_menu = MenuWarning(
                    box=self.stdscr,
                    title="Agendamento Realizado",
                    width=90,
                    height=30,
                    warnings=[result],
                )

                is_success_menu.show()
            elif dinner:
                result = self.database.schedule_meal(
                    date=date,
                    meal_type="jantar",
                    user_id=self.user_id,
                    time=dinner_time,
                )

                is_success_menu = MenuWarning(
                    box=self.stdscr,
                    title="Agendamento Realizado",
                    width=90,
                    height=30,
                    warnings=[result],
                )

                is_success_menu.show()
