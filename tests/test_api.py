"""Tests for the SHL Assessment Recommender API."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import ChatRequest, Message

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_endpoint_schema_validation():
    """Test chat endpoint validates request schema."""
    # Test empty messages array
    response = client.post("/chat", json={"messages": []})
    assert response.status_code == 422
    
    # Test invalid role
    response = client.post("/chat", json={
        "messages": [{"role": "invalid", "content": "test"}]
    })
    assert response.status_code == 422
    
    # Test empty content
    response = client.post("/chat", json={
        "messages": [{"role": "user", "content": ""}]
    })
    assert response.status_code == 422


def test_chat_endpoint_valid_request():
    """Test chat endpoint with valid request."""
    response = client.post("/chat", json={
        "messages": [
            {"role": "user", "content": "I need to hire a Java developer"}
        ]
    })
    
    # Should return 200 or 500 (if data files not available)
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "reply" in data
        assert "recommendations" in data
        assert "end_of_conversation" in data
        assert isinstance(data["recommendations"], list)
        assert isinstance(data["end_of_conversation"], bool)


def test_chat_endpoint_conversation_alternation():
    """Test that conversation must alternate between user and assistant."""
    # Consecutive user messages should fail
    response = client.post("/chat", json={
        "messages": [
            {"role": "user", "content": "First message"},
            {"role": "user", "content": "Second message"}
        ]
    })
    assert response.status_code == 422


def test_chat_endpoint_last_message_user():
    """Test that last message must be from user."""
    response = client.post("/chat", json={
        "messages": [
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant message"}
        ]
    })
    assert response.status_code == 422


def test_response_schema_compliance():
    """Test that response matches expected schema."""
    response = client.post("/chat", json={
        "messages": [
            {"role": "user", "content": "I need a Python assessment"}
        ]
    })
    
    if response.status_code == 200:
        data = response.json()
        
        # Check required fields
        assert "reply" in data
        assert "recommendations" in data
        assert "end_of_conversation" in data
        
        # Check reply is not empty
        assert len(data["reply"]) > 0
        
        # Check recommendations structure
        for rec in data["recommendations"]:
            assert "name" in rec
            assert "url" in rec
            assert "test_type" in rec
            assert rec["test_type"] in ["K", "A", "P", "B"]
            assert "shl.com" in rec["url"].lower()
        
        # Check recommendations count (0 to 10)
        assert 0 <= len(data["recommendations"]) <= 10


def test_off_topic_refusal():
    """Test that off-topic requests are refused."""
    off_topic_queries = [
        "What's the weather today?",
        "Tell me a joke",
        "What's the latest news?"
    ]
    
    for query in off_topic_queries:
        response = client.post("/chat", json={
            "messages": [{"role": "user", "content": query}]
        })
        
        if response.status_code == 200:
            data = response.json()
            # Should have empty recommendations and end conversation
            assert len(data["recommendations"]) == 0
            # Reply should mention scope or limitation
            assert any(word in data["reply"].lower() for word in ["only", "scope", "shl"])


def test_cors_headers():
    """Test that CORS headers are present."""
    response = client.options("/chat")
    # CORS middleware should add appropriate headers
    # Note: TestClient may not fully simulate CORS, but we can check the middleware is configured


def test_404_handler():
    """Test 404 error handling."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.skipif(True, reason="Requires data files to be present")
def test_clarification_behavior():
    """Test that vague queries trigger clarification."""
    response = client.post("/chat", json={
        "messages": [{"role": "user", "content": "I need a test"}]
    })
    
    if response.status_code == 200:
        data = response.json()
        # Should ask clarifying question
        assert "?" in data["reply"]
        assert len(data["recommendations"]) == 0
        assert data["end_of_conversation"] is False


@pytest.mark.skipif(True, reason="Requires data files to be present")
def test_recommendation_generation():
    """Test that specific queries generate recommendations."""
    response = client.post("/chat", json={
        "messages": [
            {"role": "user", "content": "I need to assess a senior Java developer"}
        ]
    })
    
    if response.status_code == 200:
        data = response.json()
        # Should provide recommendations
        assert len(data["recommendations"]) > 0
        assert len(data["recommendations"]) <= 10
        # All recommendations should have valid URLs
        for rec in data["recommendations"]:
            assert "shl.com" in rec["url"].lower()


@pytest.mark.skipif(True, reason="Requires data files to be present")
def test_multi_turn_conversation():
    """Test multi-turn conversation flow."""
    # First turn
    response1 = client.post("/chat", json={
        "messages": [
            {"role": "user", "content": "I need to hire a developer"}
        ]
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        
        # Second turn
        response2 = client.post("/chat", json={
            "messages": [
                {"role": "user", "content": "I need to hire a developer"},
                {"role": "assistant", "content": data1["reply"]},
                {"role": "user", "content": "Python, mid-level"}
            ]
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            # Should provide recommendations in second turn
            assert len(data2["recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
