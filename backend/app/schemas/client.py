from pydantic import BaseModel, EmailStr, Field


class ClientBase(BaseModel):
    first_name: str
    last_name: str
    advisor_id: int


class ClientCreate(ClientBase):
    pass


class ClientRead(ClientBase):
    id: int

    class Config:
        from_attributes = True

class ClientLogin(BaseModel):
    email: EmailStr
    password: str


class ClientCredentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
