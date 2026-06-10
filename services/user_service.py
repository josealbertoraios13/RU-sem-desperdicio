from datetime import datetime

from smartru.model import User
from smartru.repository import UserRepository
from smartru.services.service import Service
from smartru.utils import UserUtils


class UserService(Service):
    def __init__(self) -> None:
        self.repository = UserRepository()

    def create_user(self, user: User) -> dict:
        tmp_cpf = UserUtils.validate_cpf(cpf=user.cpf)

        UserUtils.validate_name(name=user.name)
        UserUtils.validate_password(password=user.password)
        UserUtils.validate_role(role=user.role)
        UserUtils.validate_email(email=user.email, role=user.role)

        date = datetime.now()

        result = self.repository.register_user(
            role=user.role, name=user.name, cpf=tmp_cpf, email=user.email,
            password=user.password, enrollment=user.enrollment, date=date,
        )

        return self.handle_response(response=result)

    def login_user(self, cpf: str, password: str) -> dict:
        tmp_cpf = UserUtils.validate_cpf(cpf=cpf)
        result = self.repository.login(cpf=tmp_cpf, password=password)
        return self.handle_response(response=result)

    def delete_user(self, cpf: str) -> dict:
        tmp_cpf = UserUtils.validate_cpf(cpf)
        result = self.repository.delete_user(cpf=tmp_cpf)
        return self.handle_response(response=result)

    def update_user_password(self, cpf: str, current_password: str, new_password: str) -> dict:
        tmp_cpf = UserUtils.validate_cpf(cpf=cpf)

        UserUtils.validate_password(password=new_password)

        result = self.repository.update_user_password(cpf=tmp_cpf, current=current_password, new=new_password)
        return self.handle_response(result)

    def get_users(self) -> dict:
        result = self.repository.get_users()
        return self.handle_response(response=result)

    def password_recover(self, cpf: str, email: str) -> dict:
        tmp_cpf = UserUtils.validate_cpf(cpf=cpf)

        UserUtils.validate_email(email=email)

        result = self.repository.password_recover(cpf=tmp_cpf, email=email)
        return self.handle_response(response=result)

    def reset_password_with_token(self, token: str, new_password: str) -> dict:
        UserUtils.validate_password(password=new_password)

        result = self.repository.reset_password_with_token(token=token, new_password=new_password)
        return self.handle_response(response=result)
