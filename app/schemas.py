"""Pydantic schemas for API request and response validation."""

from typing import List, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class Message(BaseModel):
    """A single message in the conversation."""
    
    role: Literal["user", "assistant"] = Field(
        ...,
        description="Role of the message sender"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Content of the message"
    )
    
    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Validate that content is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()


class ChatRequest(BaseModel):
    """Request schema for the chat endpoint."""
    
    messages: List[Message] = Field(
        ...,
        min_length=1,
        description="Conversation history"
    )
    
    @model_validator(mode='after')
    def validate_conversation(self):
        """Validate conversation structure."""
        messages = self.messages
        
        if not messages:
            raise ValueError("Messages array cannot be empty")
        
        # Validate that last message is from user
        if messages[-1].role != "user":
            raise ValueError("Last message must be from user")
        
        # Validate alternating roles
        for i in range(len(messages) - 1):
            current_role = messages[i].role
            next_role = messages[i + 1].role
            
            if current_role == next_role:
                raise ValueError(
                    f"Messages must alternate between user and assistant. "
                    f"Found consecutive {current_role} messages at positions {i} and {i+1}"
                )
        
        # Validate that conversation starts with user
        if messages[0].role != "user":
            raise ValueError("Conversation must start with a user message")
        
        return self


class Recommendation(BaseModel):
    """A single assessment recommendation."""
    
    name: str = Field(
        ...,
        description="Name of the assessment"
    )
    url: str = Field(
        ...,
        description="URL to the assessment on shl.com"
    )
    test_type: str = Field(
        ...,
        description="Type of test (K=Knowledge, A=Ability, P=Personality, B=Behavioral)"
    )


class ChatResponse(BaseModel):
    """Response schema for the chat endpoint."""
    
    reply: str = Field(
        ...,
        description="Natural language response to the user"
    )
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="List of recommended assessments (empty when clarifying or refusing)"
    )
    end_of_conversation: bool = Field(
        ...,
        description="Whether the conversation should end"
    )
    
    @field_validator('recommendations')
    @classmethod
    def validate_recommendations_count(cls, v: List[Recommendation]) -> List[Recommendation]:
        """Validate that recommendations count is between 0 and 10."""
        if len(v) > 10:
            raise ValueError("Cannot return more than 10 recommendations")
        return v


class HealthResponse(BaseModel):
    """Response schema for the health endpoint."""
    
    status: Literal["ok"] = Field(
        default="ok",
        description="Health status of the API"
    )
