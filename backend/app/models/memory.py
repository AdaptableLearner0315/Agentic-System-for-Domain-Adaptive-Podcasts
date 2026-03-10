"""
Pydantic models for user memory and personalization.

These models define the structure for persistent user preferences,
conversation history, and adaptive learning data.
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class CommunicationStyle(BaseModel):
    """
    User's preferred communication style.

    Attributes:
        verbosity: How detailed responses should be
        tone: Preferred conversation tone
        use_analogies: Whether to use analogies for explanations
        technical_depth: Level of technical detail
    """
    verbosity: Literal["concise", "balanced", "detailed"] = "balanced"
    tone: Literal["casual", "professional", "friendly"] = "friendly"
    use_analogies: bool = True
    technical_depth: Literal["beginner", "intermediate", "expert"] = "intermediate"


class UserProfile(BaseModel):
    """
    Persistent user profile information.

    Attributes:
        user_id: Unique user identifier
        display_name: User's preferred name
        created_at: When profile was created
        updated_at: Last update timestamp
        communication_style: Preferred communication style
        interests: Topics of interest
        expertise_areas: Areas where user has expertise
        preferences: Additional preferences
    """
    user_id: str = Field(..., description="Unique user identifier")
    display_name: Optional[str] = Field(None, description="User's preferred name")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    communication_style: CommunicationStyle = Field(default_factory=CommunicationStyle)
    interests: List[str] = Field(default_factory=list)
    expertise_areas: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class MemoryConsent(BaseModel):
    """
    User's consent for memory storage.

    Attributes:
        user_id: User identifier
        granted: Whether consent is granted
        granted_at: When consent was given
        scope: What types of memory are allowed
    """
    user_id: str
    granted: bool = False
    granted_at: Optional[datetime] = None
    scope: List[str] = Field(
        default_factory=lambda: ["preferences", "history", "traits"]
    )


class ConversationMemory(BaseModel):
    """
    Memory from a single conversation.

    Attributes:
        session_id: Session identifier
        job_id: Associated podcast job ID
        timestamp: When conversation occurred
        summary: AI-generated summary of conversation
        topics_discussed: Main topics covered
        user_questions: Notable questions asked
        user_reactions: User's reactions/opinions
        insights: Insights learned about user
    """
    session_id: str
    job_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    summary: Optional[str] = None
    topics_discussed: List[str] = Field(default_factory=list)
    user_questions: List[str] = Field(default_factory=list)
    user_reactions: Dict[str, str] = Field(default_factory=dict)
    insights: List[str] = Field(default_factory=list)


class AdaptiveThresholds(BaseModel):
    """
    Learned voice activity thresholds for a user.

    Attributes:
        user_id: User identifier
        silence_threshold_ms: Learned silence threshold
        pause_samples: Historical pause durations
        false_positive_rate: Rate of premature sends
        total_interactions: Total voice interactions
        updated_at: Last update timestamp
    """
    user_id: str
    silence_threshold_ms: int = 1500
    pause_samples: List[int] = Field(default_factory=list, max_length=50)
    false_positive_rate: float = 0.0
    total_interactions: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserMemory(BaseModel):
    """
    Complete user memory container.

    Attributes:
        user_id: User identifier
        profile: User profile information
        consent: Memory consent status
        conversations: Past conversation memories
        thresholds: Adaptive voice thresholds
        relationship_notes: Long-term relationship context
    """
    user_id: str
    profile: UserProfile
    consent: MemoryConsent
    conversations: List[ConversationMemory] = Field(default_factory=list)
    thresholds: Optional[AdaptiveThresholds] = None
    relationship_notes: List[str] = Field(default_factory=list)


# =============================================================================
# Request/Response Models
# =============================================================================

class ConsentRequest(BaseModel):
    """Request to update memory consent."""
    granted: bool
    scope: Optional[List[str]] = None


class ConsentResponse(BaseModel):
    """Response with consent status."""
    user_id: str
    granted: bool
    granted_at: Optional[datetime] = None
    scope: List[str]


class ProfileUpdateRequest(BaseModel):
    """Request to update user profile."""
    display_name: Optional[str] = None
    communication_style: Optional[CommunicationStyle] = None
    interests: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None


class ProfileResponse(BaseModel):
    """Response with user profile."""
    user_id: str
    display_name: Optional[str] = None
    communication_style: CommunicationStyle
    interests: List[str]
    expertise_areas: List[str]
    created_at: datetime
    updated_at: datetime


class MemoryContextResponse(BaseModel):
    """Memory context for AI prompts."""
    user_id: str
    display_name: Optional[str] = None
    communication_preferences: Dict[str, Any]
    relevant_history: List[str]
    known_interests: List[str]
    expertise_level: str


class ThresholdsUpdateRequest(BaseModel):
    """Request to update adaptive thresholds."""
    silence_threshold_ms: Optional[int] = None
    pause_sample: Optional[int] = None
    false_positive: Optional[bool] = None


class ThresholdsResponse(BaseModel):
    """Response with adaptive thresholds."""
    user_id: str
    silence_threshold_ms: int
    false_positive_rate: float
    total_interactions: int
    is_personalized: bool
