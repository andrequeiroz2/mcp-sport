"""Pydantic schemas for the get_session_results tool (OpenF1 /session_result endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class SessionResultsInput(BaseInput):
    """Input filters for the get_session_results tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )
    position: int | None = Field(
        default=None, ge=1, description="Final position in the session (starts at 1)"
    )


class SessionResult(BaseModel):
    """Session result record as returned by the OpenF1 /session_result endpoint."""

    session_key: int
    meeting_key: int
    driver_number: int
    position: int | None = Field(
        default=None, description="Final position at the end of the session"
    )
    number_of_laps: int | None = None
    dnf: bool | None = Field(default=None, description="Did Not Finish")
    dns: bool | None = Field(default=None, description="Did Not Start")
    dsq: bool | None = Field(default=None, description="Disqualified")
    duration: float | list[float] | None = Field(
        default=None,
        description=(
            "Best lap time (practice/qualifying) or total race time, in seconds. "
            "In qualifying, an array of three values for Q1, Q2 and Q3."
        ),
    )
    gap_to_leader: float | str | list[float | str] | None = Field(
        default=None,
        description=(
            "Gap to the session leader in seconds, or '+N LAP(S)' if lapped. "
            "In qualifying, an array of three values for Q1, Q2 and Q3."
        ),
    )
