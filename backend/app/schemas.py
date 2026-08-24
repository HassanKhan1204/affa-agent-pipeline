from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# Kept in sync with what the pipeline actually writes (build_crm.py defaults
# new leads to 'new'; outreach_agent.py marks drafted ones 'drafted') plus
# the two states a human moves a lead through by hand once they've reached
# out to it in the UI.
LeadStatus = Literal["new", "drafted", "contacted", "responded", "declined"]


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    name: str
    subtype: str | None = ""
    focus_area: str | None = ""
    fit_reason: str | None = ""
    url: str | None = ""
    contact_name: str | None = ""
    contact_email: str | None = ""
    contact_phone: str | None = ""
    contact_page: str | None = ""
    outreach_message: str | None = ""
    status: str
    updated_at: datetime


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class StatsOut(BaseModel):
    total: int
    funders: int
    partners: int
    by_status: dict[str, int]
