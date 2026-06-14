from pydantic import BaseModel


class Customer(BaseModel):
    id: int
    name: str
    company: str
    email: str
    phone: str | None = None
    tier: str


class Agent(BaseModel):
    id: int
    name: str
    email: str
    role: str
