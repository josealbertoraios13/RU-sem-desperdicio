from pydantic import BaseModel, EmailStr

class UserRequest(BaseModel):
    name : str
    email : EmailStr
    cpf : str
    password : str
    role : str
    enrollment : str
