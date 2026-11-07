
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class TransportOptionSummary(BaseModel):
    mode: str
    label: str
    estimated_cost_per_person: float
    details: str


class DestinationSummary(BaseModel):
    verdict: str
    verdict_tone: Literal["success", "warning", "info"] = "info"
    benefits: list[str] = []
    cautions: list[str] = []
    origin_city: str | None = None
    estimated_budget_per_person: float | None = None
    budget_status: str | None = None
    weather_summary: str | None = None
    transport_options: list[TransportOptionSummary] = []


class RecommendationItem(BaseModel):
    destination_id: UUID
    name: str
    compatibility_score: float | None
    reasons: list[str]
    metadata_status: Literal[
        "complete",
        "partial",
        "insufficient",
    ]
    missing_attributes: list[str]
    summary: DestinationSummary | None = None
