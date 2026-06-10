from fastapi import APIRouter

from smartru.model import (
    DeleteRequest,
    LoginRequest,
    PasswordRecoverRequest,
    PasswordResetRequest,
    UpdatePasswordRequest,
    User,
    UserRequest,
)
from smartru.services import UserService

router = APIRouter()
user_services = UserService()

@router.post("/user/register")
def register_user(request : UserRequest) -> dict:
    user = User(
        name=request.name,
        email=request.email,
        cpf=request.cpf,
        password=request.password,
        role=request.role,
        enrollment=request.enrollment
    )

    return user_services.create_user(user=user)

@router.post("/user/login")
def get_user(request : LoginRequest) -> dict:
    cpf = request.cpf
    password = request.password
    return user_services.login_user(cpf=cpf, password=password)

@router.get("/users")
def get_users() -> dict:
    return user_services.get_users()

@router.put("/user/update_password")
def update_user_password(request : UpdatePasswordRequest) -> dict:
    cpf = request.cpf
    current = request.current_password
    new = request.new_password

    return user_services.update_user_password(cpf=cpf, current_password=current, new_password=new)

@router.delete("/user/delete")
def delete_user(request : DeleteRequest) -> dict:
    cpf = request.cpf

    return user_services.delete_user(cpf=cpf)

@router.post("/user/password_recover")
def password_recover(request: PasswordRecoverRequest) -> dict:
    # TODO: Implement rate limiting (e.g., 3 requests per hour per IP/CPF)
    cpf = request.cpf
    email = request.email

    return user_services.password_recover(cpf=cpf, email=email)

@router.post("/user/password_reset")
def password_reset(request: PasswordResetRequest) -> dict:
    token = request.token
    new_password = request.new_password

    return user_services.reset_password_with_token(token=token, new_password=new_password)
