import yaml
from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field

class DestinationBase(BaseModel):
    type: str

class DiscordDestination(DestinationBase):
    type: Literal["discord"]
    webhook_url: str

class GistDestination(DestinationBase):
    type: Literal["gist"]
    gist_id: str
    github_token: str

class SqliteDestination(DestinationBase):
    type: Literal["sqlite"]
    table_name: str

DestinationType = Union[DiscordDestination, GistDestination, SqliteDestination]

class Profile(BaseModel):
    name: str
    target_terms: List[str] = Field(default_factory=list)
    target_locations: List[str] = Field(default_factory=list)
    industry_keywords: List[str] = Field(default_factory=list)
    destinations: List[DestinationType] = Field(default_factory=list)

class Config(BaseModel):
    profiles: List[Profile] = Field(default_factory=list)

def load_config(path: str) -> Config:
    import os
    if not os.path.exists(path):
        return Config(profiles=[])
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return Config(**data)
