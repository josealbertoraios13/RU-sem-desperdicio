from .controller import Controller
from .account_controller import AccountController 
from .schedule_meal_controller import ScheduleMealController
from .history_controller import HistoryController

from model import MenuProfile
from database import DataBase

class SessionController(Controller):
    def __init__(self, stdscr, data):
        super().__init__(stdscr, data)
        self.user_id, self.name, self.typed, self.email, self.cpf, self.matricula, self.codigo_funcionario = self.data
        self.database = DataBase()
    
    def run(self):

        while True:
            
            user_exist = self.database._check_user_exists(cpf=self.cpf, email=self.email, enrollment=self.matricula, employee_code=self.codigo_funcionario)
            
            if user_exist is None:
                break

            menu_profile = MenuProfile(
                box=self.stdscr, 
                title="SmartRU",
                width=60, height=30, 
                options=["Agendar Refeição", "Histórico de Agendamentos", "Ver Conta"],
                user=self.data
            )

            menu_profile.show()       
            if menu_profile.selected == 0:
                self.schedule_meal_controller()
            elif menu_profile.selected == 1:
                self._view_meal_history()
            elif menu_profile.selected == 2:
                self.account_controller()
            elif menu_profile.selected == -1:
                break

    def schedule_meal_controller(self):
        schedule_meal_controller = ScheduleMealController(stdscr=self.stdscr, data=self.data, user_id=self.user_id, database=self.database)
        schedule_meal_controller.run()

    def account_controller(self):
        account_controller = AccountController(stdscr=self.stdscr, data=self.data)
        account_controller.run()

    def _view_meal_history(self):
        history_controller = HistoryController(stdscr=self.stdscr, data=self.database, typed=self.typed, user_id=self.user_id)
        history_controller.run()