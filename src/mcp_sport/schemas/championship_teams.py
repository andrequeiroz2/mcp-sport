"""Pydantic schemas for the get_teams_championship tool (OpenF1 /championship_teams, beta)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class TeamsChampionshipInput(BaseInput):
    """Input filters for the get_teams_championship tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Race session identifier, or 'latest' for the most recent one",
    )
    team_name: str | None = Field(
        default=None, min_length=1, max_length=100, description="e.g., 'McLaren'"
    )


class TeamsChampionshipEntry(BaseModel):
    """Championship standing as returned by /championship_teams (beta)."""

    session_key: int
    meeting_key: int
    team_name: str
    position_current: int | None = Field(
        default=None, description="Championship position during/after the race"
    )
    position_start: int | None = Field(
        default=None, description="Championship position before the race started"
    )
    points_current: float | None = Field(
        default=None, description="Championship points during/after the race"
    )
    points_start: float | None = Field(
        default=None, description="Championship points before the race started"
    )
