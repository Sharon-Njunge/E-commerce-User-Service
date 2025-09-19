from pydantic import BaseModel, EmailStr, constr

class LoginSchema(BaseModel):
    username: str
    password: constr(min_length=6)

class RegisterSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    first_name: str
    last_name: str
