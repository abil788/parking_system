from pydantic import BaseModel


class CardBase(BaseModel):
    uid: str
    owner_name: str | None = None
    active: bool = True


class CardCreate(CardBase):
    pass


class CardResponse(CardBase):
    id: int

    class Config:
        orm_mode = True
