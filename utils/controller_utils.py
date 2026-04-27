
class ControllerUtils:
     @staticmethod
     def _get_fields(user_type : str, email_label : str) -> list:
        enrollment_label = "Matrícula" if user_type == "estudante" else "Código do Funcionário"

        if user_type != "convidado":
            return [
                ("Nome completo", False),
                (email_label,        False),
                ("CPF",           False),
                (enrollment_label, False),
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