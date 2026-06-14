from pydantic import BaseModel


class StatsResponse(BaseModel):
    total: int
    urgent_open: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
