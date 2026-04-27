from .controller import Controller
from database import DataBase
from model import MenuAccount, MenuModal, MenuWarning
from curses import window

class AccountController(Controller):
    def __init__(self, stdscr : window, data : tuple):
        super().__init__(stdscr, data)
        self.user_id, self.name, self.typed, self.email, self.cpf, self.matricula, self.codigo_funcionario = data

    def run(self) -> None:
        extra_map = {
            "estudante":   ("Matricula",        self.matricula if self.matricula else "N/A"),
            "funcionario": ("Cod. Funcionario", self.codigo_funcionario if self.codigo_funcionario else "N/A"),
        }
        extra_label, extra_value = extra_map.get(self.typed, (None, None))

        menu_account = MenuAccount(
            box=self.stdscr, 
            title="SmartRU", 
            width=70, height=30,
            options=["[ Voltar ]", "[ Deletar conta ]"],
            role=self.typed.capitalize(), # papel
            occupant=self.name, # agente do papel
            email=self.email,
            cpf=self.cpf,
            extra_label=extra_label,
            extra_value=extra_value,
        )

        menu_account.show()

        if menu_account.cancelled or menu_account.selected == 0:
            return
        
        if menu_account.selected == 1:
            self._delete()

    def _delete(self) -> None:
        if self._can_delete():
            db = DataBase()
            result = db.delete_user(cpf=self.cpf)

            if "Sucesso" in result:
                success_menu = MenuWarning(
                    self.stdscr,
                    title="Conta Excluída",
                    width=90,
                    height=30,
                    warnings=[
                        "Sua conta foi excluída com sucesso!",
                        "Você será redirecionado para o menu principal."
                    ]
                )
                success_menu.show()
                return
            
            error_menu = MenuWarning(
                self.stdscr,
                title="Erro na Exclusão",
                width=90,
                height=30,
                warnings=[result]
            )
            error_menu.show()

    def _can_delete(self) -> bool:
        self._show_warning(
            title="Importante!", 
            messages=["ATENÇÃO: Esta ação é irreversível!", "Todos os seus dados serão permanentemente excluídos.",]
            )

        menu_modal = MenuModal(
            box=self.stdscr,
            title="Alerta!",
            width=60, height=30,
            options=["[ Não ]", "[ Sim ]"],
            message="Você realmente deseja apagar sua conta? "
        )
        menu_modal.show()

        if menu_modal.selected == 0:
            return False
        
        return True