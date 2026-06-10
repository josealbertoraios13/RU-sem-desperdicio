"""
    Este modelo de objeto serve para manipular/ler e transportar os dados
    do usuário dentro da API
"""

class User:
    def __init__(self, name : str, email : str, cpf : str, password : str, role : str, enrollment : str) -> None:

        self.name = name
        self.email = email
        self.cpf = cpf
        self.password = password
        self.role = role
        self.enrollment = enrollment
