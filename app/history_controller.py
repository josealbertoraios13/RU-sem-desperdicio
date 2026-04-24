from datetime import datetime
from .controller import Controller
from database import DataBase
from model import MenuHistory, MenuModal, MenuWarning

class HistoryController(Controller):
    def __init__(self, stdscr, data, typed, user_id):
        self.database = data
        self.typed = typed
        self.user_id = user_id
        super().__init__(stdscr, data)

    def run(self):
        schedules = []
        if self.typed == "funcionario":
            results = self.database.get_all_meal_history()
        else:
            results = self.database.get_meal_history(user_id=self.user_id)

        for result in results:
            scheduler_id, schedule_type, schedule_date, schedule_time  = result

            # Converte o horário para string no formato HH:MM se for um objeto time
            horario_str = schedule_time.strftime("%H:%M") if schedule_time else None

            m_dict = {
                "refeicao_id" : scheduler_id,
                "data" : schedule_date.strftime("%d/%m/%Y"),
                "refeicao" : schedule_type,
                "horario" : horario_str
            } 

            schedules.append(m_dict)

        menu_history = MenuHistory(
            box=self.stdscr,
            title="Agenda",
            width=60, height=30,
            schedules=schedules
        )

        menu_history.show()

        if menu_history.enter:
            schedule_to_delete = menu_history.selected_schedule
            if schedule_to_delete:
                self._delete(item=schedule_to_delete)

    def _delete(self, item : dict):

        if self._can_delete():
            data = DataBase()
            date_str = item.get("data")
            if not date_str:
                return
            date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
            result = data.delete_schedule(
                user_id=self.user_id,
                date=date_obj,
                meal_type=item.get("refeicao")
            )

            if "Sucesso" in result:
                success_menu = MenuWarning(
                    self.stdscr,
                    title="Agendamento Excluído",
                    width=90,
                    height=30,
                    warnings=[
                        "Agendamento cancelado com sucesso",
                        "Você será redirecionado para o menu principal."
                    ]
                )
                success_menu.show()
                return
            else:
                error_menu = MenuWarning(
                    self.stdscr,
                    title="Erro na Exclusão",
                    width=90,
                    height=30,
                    warnings=[result]
                )
                error_menu.show()

    def _can_delete(self):

        warning_menu = MenuWarning(
            self.stdscr,
            title="Importante!",
            width=90,
            height=30,
            warnings=[
                "ATENÇÃO: Esta ação é irreversível!",
                "Seu agendamento será cancelado e você não poderá entrar no RU",
            ]
        )
        warning_menu.show()

        menu_modal = MenuModal(
            box=self.stdscr,
            title="Alerta!",
            width=60, height=30,
            options=["[ Não ]", "[ Sim ]"],
            message="Você realmente deseja cancelar este agendamento?"
        )
        menu_modal.show()

        if menu_modal.selected == 0:
            return False
        
        return True