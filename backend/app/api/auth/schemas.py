from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    ok: bool = True
    access_token: str
    refresh_token: str
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    ok: bool = True
    user: UserOut


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
