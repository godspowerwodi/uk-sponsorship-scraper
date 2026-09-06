from .greenhouse import fetch_greenhouse
from .lever import fetch_lever
from .ashby import fetch_ashby
from .smartrecruiters import fetch_smartrecruiters
from .tracjobs import fetch_tracjobs

TENANT_SCRAPERS = [fetch_greenhouse, fetch_lever, fetch_ashby, fetch_smartrecruiters]
CENTRALIZED_SCRAPERS = [fetch_tracjobs]
ALL_SCRAPERS = TENANT_SCRAPERS + CENTRALIZED_SCRAPERS
