"""
web_access — complete reimplementation of the web-access skill for Python backends.

Capabilities:
  - Full CDP proxy client (all endpoints from cdp-proxy.mjs)
  - Smart tool selection: CDP > web_fetch > Jina > curl (mirrors SKILL.md)
  - Site experience system (mirrors references/site-patterns + match-site.mjs)
  - Parallel fetching with tab isolation
  - Amazon search via CDP or Claude web_search
  - Jina reader integration
"""
from app.web_access.fetcher import fetch_page, fetch_pages_parallel, search_amazon, search_web
from app.web_access.cdp_client import CDPClient, ManagedTab
from app.web_access.site_experience import (
    get_site_experience, update_site_experience,
    record_success, record_failure, list_all_patterns,
)

__all__ = [
    "fetch_page",
    "fetch_pages_parallel",
    "search_amazon",
    "search_web",
    "CDPClient",
    "ManagedTab",
    "get_site_experience",
    "update_site_experience",
    "record_success",
    "record_failure",
    "list_all_patterns",
]
