from .controller import Controller
from database import DataBase
from model import MenuAccount, MenuModal, MenuWarning

class AccountController(Controller):
    def __init__(self, stdscr, data):
        super().__init__(stdscr, data)
        self.user_id, self.name, self.typed, self.email, self.cpf, self.matricula, self.codigo_funcionario = data

    def run(self):
        extra_map = {
            "estudante":   ("Matricula",        self.matricula if self.matricula else "N/A"),
            "funcionario": ("Cod. Funcionario", self.codigo_funcionario if self.codigo_funcionario else "N/A"),
        }
        extra_label, extra_value = extra_map.get(self.typed, (None, None))

        menu_account = MenuAccount(
            self.stdscr, title="SmartRU", width=70, height=30,
            options=["[ Voltar ]", "[ Deletar conta ]"],
            role=self.typed.capitalize(),
            occupant=self.name,
            email=self.email,
            cpf=self.cpf,
            extra_label=extra_label,
            extra_value=extra_value,
        )

        menu_account.show()

        if menu_account.selected == 0:
            return
        elif menu_account.selected == 1:
            self._delete()

    def _delete(self):
        if self._can_delete():
            data = DataBase()
            result = data.delete_user(cpf=self.cpf)

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
                "Todos os seus dados serão permanentemente excluídos.",
            ]
        )
        warning_menu.show()

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