from pydantic import BaseModel


class BankBase(BaseModel):
    name: str
    client_id: int


class BankCreate(BankBase):
    pass


class BankRead(BankBase):
    id: int

    class Config:
        from_attributes = True