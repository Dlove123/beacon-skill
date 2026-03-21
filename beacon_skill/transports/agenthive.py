"""
AgentHive Transport for Beacon
Issue #151 - Bounty: 10 RTC

AgentHive is an independent, open microblogging network for AI agents.
Permanent free API, no corporate ownership, similar agent identity model.

API Reference: https://agenthive.to/docs/quickstart
"""

import time
from typing import Any, Dict, List, Optional

import requests

from ..retry import with_retry
from ..storage import get_last_ts, set_last_ts


class AgentHiveError(RuntimeError):
    """AgentHive API error."""
    pass


class AgentHiveClient:
    """
    AgentHive transport client for Beacon.
    
    Supports:
    - Post messages
    - Read timeline/feed
    - Follow agents
    - Register new agents
    """
    
    def __init__(
        self,
        base_url: str = "https://agenthive.to",
        api_key: Optional[str] = None,
        timeout_s: int = 20,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Beacon/1.0.0 (Elyan Labs)",
            "Content-Type": "application/json",
        })
    
    def _request(
        self,
        method: str,
        path: str,
        auth: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to AgentHive API."""
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        
        if auth:
            if not self.api_key:
                raise AgentHiveError("AgentHive API key required. Register at agenthive.to/api/agents")
            headers = dict(headers)
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        def _do():
            resp = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.timeout_s,
                **kwargs
            )
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            
            if resp.status_code >= 400:
                raise AgentHiveError(data.get("error") or f"HTTP {resp.status_code}")
            
            return data
        
        return with_retry(_do)
    
    def register_agent(self, name: str, bio: str = "") -> Dict[str, Any]:
        """
        Register a new agent on AgentHive.
        
        Args:
            name: Agent name (unique)
            bio: Optional bio/description
        
        Returns:
            Dict with api_key for the new agent
        """
        return self._request(
            "POST",
            "/api/agents",
            json={"name": name, "bio": bio}
        )
    
    def create_post(self, content: str, *, force: bool = False) -> Dict[str, Any]:
        """
        Create a post on AgentHive.
        
        Args:
            content: Post content (message text)
            force: Skip local rate limit guard
        
        Returns:
            Dict with post details
        """
        # Local rate limit guard (30 min default)
        guard_key = "agenthive_post"
        last_ts = get_last_ts(guard_key)
        
        if not force and last_ts is not None and (time.time() - last_ts) < 1800:
            raise AgentHiveError(
                "Local guard: AgentHive posting is limited to 1 per 30 minutes (use --force to override)."
            )
        
        resp = self._request(
            "POST",
            "/api/posts",
            auth=True,
            json={"content": content}
        )
        
        set_last_ts(guard_key)
        return resp
    
    def get_feed(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get public timeline feed.
        
        Args:
            limit: Number of posts to fetch (default: 20)
        
        Returns:
            List of posts
        """
        resp = self._request("GET", "/api/feed", params={"limit": limit})
        return resp.get("posts", [])
    
    def get_agent_posts(self, agent_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get posts by a specific agent.
        
        Args:
            agent_name: Agent name
            limit: Number of posts to fetch
        
        Returns:
            List of posts by the agent
        """
        resp = self._request("GET", f"/api/agents/{agent_name}/posts", params={"limit": limit})
        return resp.get("posts", [])
    
    def follow_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Follow another agent.
        
        Args:
            agent_name: Agent to follow
        
        Returns:
            Dict with follow status
        """
        return self._request(
            "POST",
            f"/api/agents/{agent_name}/follow",
            auth=True
        )
    
    def get_agent_profile(self, agent_name: str) -> Dict[str, Any]:
        """
        Get agent profile.
        
        Args:
            agent_name: Agent name
        
        Returns:
            Dict with agent profile data
        """
        return self._request("GET", f"/api/agents/{agent_name}")


# Beacon transport interface
def send_beacon(
    message: str,
    agent_name: str,
    api_key: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Send a beacon message via AgentHive.
    
    Args:
        message: Beacon message content
        agent_name: Sender agent name
        api_key: AgentHive API key
        **kwargs: Additional options
    
    Returns:
        Dict with post details
    """
    client = AgentHiveClient(api_key=api_key)
    return client.create_post(content=message)


def receive_beacons(
    agent_name: Optional[str] = None,
    limit: int = 20,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Receive beacon messages from AgentHive.
    
    Args:
        agent_name: Optional agent name to filter by
        limit: Number of messages to fetch
    
    Returns:
        List of beacon messages
    """
    client = AgentHiveClient()
    
    if agent_name:
        return client.get_agent_posts(agent_name, limit=limit)
    else:
        return client.get_feed(limit=limit)
