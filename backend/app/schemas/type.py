from pydantic import BaseModel, ConfigDict


class TypeBase(BaseModel):
    name: str


class TypeCreate(TypeBase):
    pass


class TypeUpdate(BaseModel):
    name: str | None = None


class TypeRead(TypeBase):
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
