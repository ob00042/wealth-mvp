from pydantic import BaseModel, EmailStr


class AdvisorBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class AdvisorCreate(AdvisorBase):
    password: str


class AdvisorRead(AdvisorBase):
    id: int

    class Config:
        from_attributes = True


class AdvisorLogin(BaseModel):
    email: EmailStr
    password: str