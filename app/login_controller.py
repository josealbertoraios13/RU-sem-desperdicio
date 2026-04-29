from .controller import Controller
from model import MenuInput
from curses import window
from database import DataBase

class LoginController(Controller):
    def __init__(self, stdscr : window, data : DataBase):
        super().__init__(stdscr, data)
        self.data : DataBase
        self.data_base_message = {"success": False, "message": "Login cancelado"}

    def run(self) -> None:
        fields = [
            ("CPF", False),
            ("Senha", True),
        ]

        menu_login = MenuInput(
            self.stdscr, 
            title="Login", 
            width=90, height=30, 
            fields=fields, 
            button_label="[ Entrar ]", 
            verify=False
            )
        
        menu_login.show()

        if menu_login.cancelled: # ESC
            return

        form_data = menu_login.get_result()

        if not form_data:
            self._show_warning("Erros", [
                "Falha no Login!", 
                "Verifique se os campos estao corretos", 
            ])
            return

        cpf = (str)(form_data.get("CPF")).replace(".", "").replace("-", "")
        password = (str)(form_data.get("Senha"))

        self.data_base_message = self.data.login(cpf=cpf, password=password)
        
        messages = [self.data_base_message.get("message")]
        self._show_warning("Avisos", messages=messages)
        

