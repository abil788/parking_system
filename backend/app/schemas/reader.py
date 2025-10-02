from pydantic import BaseModel


class ReaderBase(BaseModel):
    reader_id: str
    location: str | None = None


class ReaderCreate(ReaderBase):
    pass


class ReaderResponse(ReaderBase):
    id: int

    class Config:
        orm_mode = True
