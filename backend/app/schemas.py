from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SearchRequest(BaseModel):
    prompt: str
    limit: int = 10
    campaign_id: int | None = None


class LeadOut(BaseModel):
    id: int
    full_name: str
    role: str
    company: str
    company_size: str
    country: str
    linkedin_url: str
    email: str
    email_status: str
    score: int
    score_reasons: list
    crm_status: str
    source: str

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    name: str
    prompt: str = ""


class SequenceStepIn(BaseModel):
    day_offset: int
    channel: str
    condition: str = "always"
    template: str = ""
