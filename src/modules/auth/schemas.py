from pydantic import BaseModel, EmailStr


class GoogleLoginRequest(BaseModel):
    id_token: str


class OkResponse(BaseModel):
    ok: bool = True


class SignupRequest(BaseModel):
    email: EmailStr
    signup_secret: str
