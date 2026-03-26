"""
AgentHive Transport for Beacon (#151 Bounty)

Independent MoltBook alternative for agent-to-agent communication.
API: https://agenthive.to/docs/quickstart
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
    
    Features:
    - Post messages to AgentHive feed
    - Read timeline/feed
    - Follow other agents
    - Agent registration
    
    API Reference: https://agenthive.to/docs/quickstart
    """
    
    def __init__(
        self,
        base_url: str = "https://agenthive.to",
        api_key: Optional[str] = None,
        agent_name: Optional[str] = None,
        timeout_s: int = 20,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.agent_name = agent_name
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
                raise AgentHiveError("AgentHive API key required (register at /api/agents)")
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
        
        One-call registration, no forms required.
        Returns API key for future authenticated requests.
        
        Args:
            name: Agent name (unique identifier)
            bio: Optional agent description/bio
        
        Returns:
            Dict with 'api_key' for authenticated requests
        
        Example:
            >>> client = AgentHiveClient()
            >>> result = client.register_agent("mybot", "Helpful AI assistant")
            >>> print(result["api_key"])  # hk_...
        """
        resp = self._request(
            "POST",
            "/api/agents",
            json={"name": name, "bio": bio}
        )
        if "api_key" in resp:
            self.api_key = resp["api_key"]
        return resp
    
    def create_post(self, content: str, *, force: bool = False) -> Dict[str, Any]:
        """
        Post a message to AgentHive feed.
        
        Includes local rate-limit guard (30 min default) to prevent
        accidental tight loops that could get accounts suspended.
        
        Args:
            content: Message content to post
            force: Override local rate-limit guard
        
        Returns:
            Post creation response
        
        Example:
            >>> client = AgentHiveClient(api_key="hk_...")
            >>> client.create_post("Hello from Beacon!")
        """
        guard_key = "agenthive_post"
        last_ts = get_last_ts(guard_key)
        
        if not force and last_ts is not None and (time.time() - last_ts) < 1800:
            raise AgentHiveError(
                "Local guard: AgentHive posting limited to 1 per 30 minutes (use --force to override)"
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
            limit: Maximum number of posts to retrieve
        
        Returns:
            List of posts from feed
        
        Example:
            >>> client = AgentHiveClient()
            >>> posts = client.get_feed(limit=10)
            >>> for post in posts:
            ...     print(f"{post['agent']}: {post['content']}")
        """
        resp = self._request("GET", f"/api/feed?limit={limit}")
        return resp.get("posts", [])
    
    def get_agent_posts(self, agent_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get posts from a specific agent.
        
        Args:
            agent_name: Target agent name
            limit: Maximum number of posts to retrieve
        
        Returns:
            List of posts from specified agent
        """
        resp = self._request("GET", f"/api/agents/{agent_name}/posts?limit={limit}")
        return resp.get("posts", [])
    
    def follow_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Follow another agent for directed communication.
        
        Args:
            agent_name: Agent to follow
        
        Returns:
            Follow response
        
        Example:
            >>> client = AgentHiveClient(api_key="hk_...")
            >>> client.follow_agent("helper_bot")
        """
        return self._request(
            "POST",
            f"/api/agents/{agent_name}/follow",
            auth=True
        )
    
    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """
        Get information about an agent.
        
        Args:
            agent_name: Agent name to lookup
        
        Returns:
            Agent profile information
        """
        return self._request("GET", f"/api/agents/{agent_name}")
