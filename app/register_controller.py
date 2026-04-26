from .controller import Controller
from model import MenuButtons, MenuInput
from utils import Utils
from curses import window
from database import DataBase

class RegisterController(Controller):
    def __init__(self, stdscr : window, data : DataBase):
        super().__init__(stdscr, data)
        self.data = data
        self.cancelled = False

    def run(self)-> None:
        user_type, email_label = self._show_user_type_menu()

        if not user_type and not email_label:
            return
        
        while True:
            form_data = self._show_registration_form(user_type, email_label)

            if form_data is None and self.cancelled:
                return

            # Se validação falhou, tenta novamente
            if form_data is None:
                continue

            data_base_message = self._get_data_message(user_type, email_label, form_data)

            self._show_warning("Avisos", [data_base_message])
            return

    def _show_user_type_menu(self) -> tuple:
        options = ["[   Estudante   ]", "[   Funcionário   ]","[   Convidado   ]",]
        menu_register_type = MenuButtons(self.stdscr, title="Register", width=90, height=30, options=options)
        menu_register_type.show()

        if menu_register_type.selected == 0:
            return "estudante", "E-mail UFRPE"
        elif menu_register_type.selected == 1:
            return "funcionario", "E-mail UFRPE"
        elif menu_register_type.selected == 2:
            return "convidado", "E-mail"
        
        return None, None
    
    def _show_registration_form(self, user_type : str, email_label : str) -> dict | None:
        
        fields = self._get_fields(user_type, email_label)
        
        menu_register_input = MenuInput(
            self.stdscr, 
            title="Register", 
            width=90, height=30, 
            fields=fields, 
            button_label="[ Cadastrar ]"
            )
        
        menu_register_input.show()

        if menu_register_input.cancelled:
            self.cancelled = menu_register_input.cancelled
            return None

        can_save = Utils.validate_all(
            fields=menu_register_input.fields,
            values=menu_register_input.values, 
            errors=menu_register_input.errors, 
            idx=menu_register_input.selected, 
            box=menu_register_input.box
            )
        
        if not can_save:
            self._show_warning("Erros", [
                "Falha no cadastro!", 
                "Verifique se os campos estao corretos", 
                "e se as senhas coincidem."
            ])
            return None
        
        return menu_register_input.get_result()

    def _get_fields(self, user_type : str, email_label : str) -> list:
    
        if user_type == "estudante":
            return [
                ("Nome completo", False),
                (email_label,        False),
                ("CPF",           False),
                ("Matrícula", False),
                ("Senha",         True),
                ("Conf. Senha",   True),
            ]
        
        if user_type == "funcionario":
            return [
                ("Nome completo", False),
                (email_label,        False),
                ("CPF",           False),
                ("Código do Funcionário", False),
                ("Senha",         True),
                ("Conf. Senha",   True),
            ]
        
        return [
            ("Nome completo", False),
            (email_label,        False),
            ("CPF",           False),
            ("Senha",         True),
            ("Conf. Senha",   True),
        ]
        
    def _get_data_message(self, user_type : str, email_label : str, form_data : dict) -> str:
        
        # Método da classe DataBase retorna uma string (user_type) de acordo com o tipo de usuário que foi salvo no banco
        if user_type == "estudante":
            return self.data.register_user(
                user_type=user_type,
                name=form_data.get("Nome completo"),
                email=form_data.get(email_label),
                cpf=form_data.get("CPF"),
                password=form_data.get("Senha"),
                enrollment=form_data.get("Matrícula")
            )
        
        if user_type == "funcionario":
            return self.data.register_user(
                user_type=user_type,
                name=form_data.get("Nome completo"),
                email=form_data.get(email_label),
                cpf=form_data.get("CPF"),
                password=form_data.get("Senha"),
                employee_code=form_data.get("Código do Funcionário")
            )
        
        return self.data.register_user(
            user_type=user_type,
            name=form_data.get("Nome completo"),
            email=form_data.get(email_label),
            cpf=form_data.get("CPF"),
            password=form_data.get("Senha"),
        )