from .greenhouse import fetch_greenhouse
from .lever import fetch_lever
from .ashby import fetch_ashby
from .smartrecruiters import fetch_smartrecruiters

ALL_SCRAPERS = [fetch_greenhouse, fetch_lever, fetch_ashby, fetch_smartrecruiters]
