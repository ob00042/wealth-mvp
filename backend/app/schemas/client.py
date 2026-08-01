from pydantic import BaseModel


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