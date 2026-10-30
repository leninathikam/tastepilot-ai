from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class Seed(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: Literal['artist', 'movie', 'book', 'brand'] = 'artist'


class Companion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    label: str = Field(min_length=1, max_length=30)
    seeds: list[Seed] = Field(min_length=1, max_length=3)
    interests: list[str] = Field(default_factory=list, max_length=10)
    dietary: Literal['none', 'vegetarian', 'vegan'] = 'none'
    allergies: list[str] = Field(default_factory=list, max_length=10)
    accessible: bool = False
    budget: float | None = Field(default=None, ge=0, le=10000, allow_inf_nan=False)

    @model_validator(mode='after')
    def valid_profile(self):
        self.label = self.label.strip()
        if not self.label or self.label.casefold() == 'you':
            raise ValueError('Companion label must be nonempty and different from You')
        if any(not s.strip() or len(s)>100 for s in self.interests):
            raise ValueError('Companion interests must be nonempty and at most 100 characters')
        if any(not s.strip() or len(s)>100 for s in self.allergies):
            raise ValueError('Companion allergies must be nonempty and at most 100 characters')
        return self


class Intent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    destination: str = Field(default='Chicago', min_length=2, max_length=100)
    date: date
    party_size: int = Field(default=3, ge=1, le=20)
    budget: float = Field(default=150, ge=0, le=10000, allow_inf_nan=False)
    seeds: list[Seed] = Field(default_factory=list, max_length=6)
    interests: list[str] = Field(default_factory=list, max_length=10)
    dietary: Literal['none', 'vegetarian', 'vegan'] = 'none'
    allergies: list[str] = Field(default_factory=list, max_length=10)
    accessible: bool = False
    require_verified_hours: bool = False
    excluded_ids: list[str] = Field(default_factory=list, max_length=50)
    max_stops: int = Field(default=3, ge=1, le=6)
    taste_weight: float = Field(default=.65, ge=0, le=1)
    preference_weight: float = Field(default=.35, ge=0, le=1)
    companions: list[Companion] = Field(default_factory=list, max_length=3)

    @model_validator(mode='after')
    def validate_weights(self):
        if self.taste_weight + self.preference_weight == 0:
            raise ValueError('At least one ranking weight must be positive')
        if any(len(x) > 100 or not x.strip() for x in self.interests):
            raise ValueError('Interests must be nonempty and at most 100 characters')
        if any(len(x) > 100 or not x.strip() for x in self.allergies):
            raise ValueError('Allergies must be nonempty and at most 100 characters')
        if self.companions and self.party_size < len(self.companions)+1:
            raise ValueError('Party size must include you and every companion profile')
        if len({p.label.casefold() for p in self.companions}) != len(self.companions):
            raise ValueError('Companion labels must be unique')
        return self

    @property
    def effective_budget(self):
        return min([self.budget]+[p.budget for p in self.companions if p.budget is not None])


class MemberEvidence(BaseModel):
    label: str
    source: Literal['fixture', 'qloo']
    resolved_ids: list[str]
    returned_rank: int | None
    ordinal_signal: float | None
    explicit_alignment: float
    matched_interests: list[str]
    proxy: float
    raw_query: dict = Field(default_factory=dict)
    note: str


class Candidate(BaseModel):
    id: str
    name: str
    category: str = 'place'
    tags: list[str] = Field(default_factory=list)
    source: Literal['fixture', 'qloo']
    source_url: str | None = None
    address: str | None = None
    taste_rank: int
    taste_score: float
    raw_query: dict = Field(default_factory=dict)
    cost: float | None = None
    accessible: bool | None = None
    dietary: list[str] | None = None
    available_date: date | None = None
    hours: dict | None = None
    price_level: int | None = None
    is_dining: bool = False
    score: float = 0
    preference_score: float = 0
    explanation: str = ''
    warnings: list[str] = Field(default_factory=list)
    member_evidence: list[MemberEvidence] = Field(default_factory=list)


class TextRequest(BaseModel):
    text: str = Field(min_length=5, max_length=2000)
    current: Intent
