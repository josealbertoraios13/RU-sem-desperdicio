from pydantic import BaseModel


class DeviceTokenRequest(BaseModel):
    user_cpf: str
    token: str
    platform: str = "android"  # 'android' | 'ios'


class RegisterDeviceResponse(BaseModel):
    success: bool
    msg: str
