from datetime import datetime
from .controller import Controller
from database import DataBase
from model import MenuHistory, MenuModal
from curses import window

class HistoryController(Controller):
    def __init__(self, stdscr : window, data : DataBase, typed : str, user_id : str):
        super().__init__(stdscr, data)
        self.data = data
        self.typed = typed
        self.user_id = user_id

    def run(self) -> None:
        # Lista de dicionários inicialmente vazia
        schedules : list = []
        if self.typed == "funcionario":
            schedules_tuples = self.data.get_all_meal_history()
        else:
            schedules_tuples = self.data.get_meal_history(user_id=self.user_id)

        for schedule_tuple in schedules_tuples:
            scheduler_id, schedule_type, schedule_date, schedule_time = schedule_tuple

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

    def _delete(self, item : dict) -> None:

        if self._can_delete():
            date_str = item.get("data")

            if not date_str:
                return
            
            date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
            result = self.data.delete_schedule(
                user_id=self.user_id,
                meal_type=(str)(item.get("refeicao")),
                date=date_obj,
            )

            if "Sucesso" in result:
                self._show_warning(
                    title="Agendamento Excluído", 
                    messages=["Agendamento cancelado com sucesso", "Você será redirecionado para o menu principal."]
                    )
                return

            self._show_warning(title="Erro na Exclusão", messages=[result])
                

    def _can_delete(self) -> bool:

        self._show_warning(
            title="Importante!", 
            messages=["ATENÇÃO: Esta ação é irreversível!", "Seu agendamento será cancelado e você não poderá entrar no RU"]
            )

        menu_modal = MenuModal(
            box=self.stdscr,
            title="Alerta!",
            width=60, height=30,
            options=["[ Não ]", "[ Sim ]"],
            message="Você realmente deseja cancelar este agendamento?"
        )
        menu_modal.show()

        if menu_modal.selected == 0 or menu_modal.cancelled:
            return False
        
        return True