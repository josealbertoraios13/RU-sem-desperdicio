from .controller import Controller
from .account_controller import AccountController
from .schedule_meal_controller import ScheduleMealController
from .history_controller import HistoryController

from model import MenuProfile
from database import DataBase
from curses import window

class SessionController(Controller):
    def __init__(self, stdscr : window, data : tuple):
        super().__init__(stdscr, data)
        self.data : tuple
        self.user_id, self.name, self.typed, self.email, self.cpf, self.matricula, self.codigo_funcionario = self.data
        self.database = DataBase()
    
    def run(self) -> None:
        while True:
            # Verifica se esta conta ainda existe 
            # (Caso a conta seja excluída o usuário não vai conseguir acessar este menu).
            user_exist = self.database._check_user_exists(
                cpf=self.cpf, email=self.email, 
                enrollment=self.matricula, employee_code=self.codigo_funcionario
                )
            
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

            if menu_profile.cancelled: # ESC
                break
            
            if menu_profile.selected == 0:
                self._schedule_meal_controller()
            elif menu_profile.selected == 1:
                self._view_meal_history()
            elif menu_profile.selected == 2:
                self._account_controller()


    def _schedule_meal_controller(self) -> None:
        schedule_meal_controller = ScheduleMealController(stdscr=self.stdscr, data=self.data, user_id=self.user_id, database=self.database)
        schedule_meal_controller.run()

    def _view_meal_history(self) -> None:
        history_controller = HistoryController(stdscr=self.stdscr, data=self.database, typed=self.typed, user_id=self.user_id)
        history_controller.run()

    def _account_controller(self) -> None:
        account_controller = AccountController(stdscr=self.stdscr, data=self.data)
        account_controller.run()

