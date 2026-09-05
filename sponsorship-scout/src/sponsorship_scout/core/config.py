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
    target_terms: List[str]
    target_locations: List[str]
    industry_keywords: List[str]
    destinations: List[DestinationType] = []

class Config(BaseModel):
    profiles: List[Profile]

def load_config(path: str) -> Config:
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return Config(**data)
