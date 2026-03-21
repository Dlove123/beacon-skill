"""
Tests for AgentHive transport
Issue #151 - Bounty: 10 RTC
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from beacon_skill.transports.agenthive import (
    AgentHiveClient,
    AgentHiveError,
    send_beacon,
    receive_beacons,
)


class TestAgentHiveClient:
    """Test AgentHive client."""
    
    def test_init_default_values(self):
        """Test default initialization."""
        client = AgentHiveClient()
        assert client.base_url == "https://agenthive.to"
        assert client.api_key is None
        assert client.timeout_s == 20
    
    def test_init_custom_values(self):
        """Test custom initialization."""
        client = AgentHiveClient(
            base_url="https://test.agenthive.to",
            api_key="hk_test123",
            timeout_s=30
        )
        assert client.base_url == "https://test.agenthive.to"
        assert client.api_key == "hk_test123"
        assert client.timeout_s == 30
    
    def test_register_agent(self):
        """Test agent registration."""
        client = AgentHiveClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"api_key": "hk_new123"}
            result = client.register_agent("testbot", "Test bio")
            
            mock_request.assert_called_once_with(
                "POST",
                "/api/agents",
                json={"name": "testbot", "bio": "Test bio"}
            )
            assert result["api_key"] == "hk_new123"
    
    def test_create_post_requires_api_key(self):
        """Test that creating post requires API key."""
        client = AgentHiveClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.side_effect = AgentHiveError("AgentHive API key required")
            
            with pytest.raises(AgentHiveError):
                client.create_post("Test message")
    
    def test_get_feed(self):
        """Test getting public feed."""
        client = AgentHiveClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"posts": [{"id": 1, "content": "test"}]}
            result = client.get_feed(limit=10)
            
            mock_request.assert_called_once_with(
                "GET",
                "/api/feed",
                params={"limit": 10}
            )
            assert len(result) == 1
            assert result[0]["id"] == 1
    
    def test_get_agent_posts(self):
        """Test getting agent posts."""
        client = AgentHiveClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"posts": [{"id": 1}]}
            result = client.get_agent_posts("testbot", limit=5)
            
            mock_request.assert_called_once_with(
                "GET",
                "/api/agents/testbot/posts",
                params={"limit": 5}
            )
            assert len(result) == 1
    
    def test_follow_agent(self):
        """Test following an agent."""
        client = AgentHiveClient(api_key="hk_test")
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"status": "following"}
            result = client.follow_agent("testbot")
            
            mock_request.assert_called_once_with(
                "POST",
                "/api/agents/testbot/follow",
                auth=True
            )
            assert result["status"] == "following"
    
    def test_get_agent_profile(self):
        """Test getting agent profile."""
        client = AgentHiveClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"name": "testbot", "bio": "Test"}
            result = client.get_agent_profile("testbot")
            
            mock_request.assert_called_once_with(
                "GET",
                "/api/agents/testbot"
            )
            assert result["name"] == "testbot"


class TestSendBeacon:
    """Test send_beacon function."""
    
    @patch('beacon_skill.transports.agenthive.AgentHiveClient')
    def test_send_beacon(self, mock_client_class):
        """Test sending beacon message."""
        mock_client = Mock()
        mock_client.create_post.return_value = {"id": 123, "content": "test"}
        mock_client_class.return_value = mock_client
        
        result = send_beacon(
            message="Test beacon",
            agent_name="testbot",
            api_key="hk_test"
        )
        
        mock_client.create_post.assert_called_once_with(content="Test beacon")
        assert result["id"] == 123


class TestReceiveBeacons:
    """Test receive_beacons function."""
    
    @patch('beacon_skill.transports.agenthive.AgentHiveClient')
    def test_receive_beacons_no_filter(self, mock_client_class):
        """Test receiving beacons without agent filter."""
        mock_client = Mock()
        mock_client.get_feed.return_value = [{"id": 1}, {"id": 2}]
        mock_client_class.return_value = mock_client
        
        result = receive_beacons(limit=10)
        
        mock_client.get_feed.assert_called_once_with(limit=10)
        assert len(result) == 2
    
    @patch('beacon_skill.transports.agenthive.AgentHiveClient')
    def test_receive_beacons_with_filter(self, mock_client_class):
        """Test receiving beacons with agent filter."""
        mock_client = Mock()
        mock_client.get_agent_posts.return_value = [{"id": 1}]
        mock_client_class.return_value = mock_client
        
        result = receive_beacons(agent_name="testbot", limit=5)
        
        mock_client.get_agent_posts.assert_called_once_with("testbot", limit=5)
        assert len(result) == 1


class TestAgentHiveError:
    """Test error handling."""
    
    def test_error_message(self):
        """Test error message."""
        error = AgentHiveError("Test error")
        assert str(error) == "Test error"
    
    def test_error_is_runtime_error(self):
        """Test that AgentHiveError is a RuntimeError."""
        error = AgentHiveError("Test")
        assert isinstance(error, RuntimeError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
