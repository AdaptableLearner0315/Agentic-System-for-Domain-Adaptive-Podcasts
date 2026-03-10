"""
API routes for user memory and personalization.

Provides endpoints for managing user consent, profiles,
and adaptive voice thresholds.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from ..models.memory import (
    ConsentRequest,
    ConsentResponse,
    ProfileUpdateRequest,
    ProfileResponse,
    ThresholdsUpdateRequest,
    ThresholdsResponse,
    MemoryContextResponse,
)
from ..services.memory_service import get_memory_service
from ..logging_config import get_logger

router = APIRouter(prefix="/api/user", tags=["User Memory"])
logger = get_logger("memory_routes")


def generate_anonymous_id() -> str:
    """Generate an anonymous user ID.

    In a production system, this would use proper authentication.
    For now, we generate a simple anonymous identifier.
    """
    import uuid
    return f"anon-{str(uuid.uuid4())[:8]}"


def get_user_id_or_generate(user_id: Optional[str]) -> str:
    """Get provided user ID or generate an anonymous one."""
    return user_id if user_id else generate_anonymous_id()


# =============================================================================
# Consent Endpoints
# =============================================================================

@router.get("/consent", response_model=ConsentResponse)
async def get_consent(
    user_id: Optional[str] = Query(None, description="User ID (uses cookie if not provided)")
):
    """Get memory consent status for a user.

    Returns the current consent status including whether memory
    storage is enabled and what types of data are allowed.
    """
    uid = get_user_id_or_generate(user_id)
    service = get_memory_service()
    consent = service.get_consent(uid)

    return ConsentResponse(
        user_id=uid,
        granted=consent.granted,
        granted_at=consent.granted_at,
        scope=consent.scope,
    )


@router.post("/consent", response_model=ConsentResponse)
async def update_consent(
    request: ConsentRequest,
    user_id: Optional[str] = Query(None, description="User ID")
):
    """Update memory consent for a user.

    When consent is granted, Nell will remember conversations
    and personalize responses. When revoked, all stored data
    is cleared except basic profile info.
    """
    uid = get_user_id_or_generate(user_id)
    service = get_memory_service()

    consent = service.update_consent(
        user_id=uid,
        granted=request.granted,
        scope=request.scope,
    )

    logger.info("Updated consent for user %s: %s", uid, request.granted)

    return ConsentResponse(
        user_id=uid,
        granted=consent.granted,
        granted_at=consent.granted_at,
        scope=consent.scope,
    )


# =============================================================================
# Profile Endpoints
# =============================================================================

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    user_id: Optional[str] = Query(None, description="User ID")
):
    """Get user profile.

    Returns the user's stored profile including communication
    preferences and interests.
    """
    uid = get_user_id_or_generate(user_id)
    service = get_memory_service()
    profile = service.get_profile(uid)

    return ProfileResponse(
        user_id=uid,
        display_name=profile.display_name,
        communication_style=profile.communication_style,
        interests=profile.interests,
        expertise_areas=profile.expertise_areas,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    user_id: Optional[str] = Query(None, description="User ID")
):
    """Update user profile.

    Requires memory consent to be granted. Updates any provided
    fields while keeping others unchanged.
    """
    uid = get_user_id_or_generate(user_id)
    service = get_memory_service()

    # Check consent
    consent = service.get_consent(uid)
    if not consent.granted:
        raise HTTPException(
            status_code=403,
            detail="Memory consent not granted. Enable memory to save profile."
        )

    profile = service.update_profile(
        user_id=uid,
        display_name=request.display_name,
        communication_style=request.communication_style,
        interests=request.interests,
        expertise_areas=request.expertise_areas,
        preferences=request.preferences,
    )

    return ProfileResponse(
        user_id=uid,
        display_name=profile.display_name,
        communication_style=profile.communication_style,
        interests=profile.interests,
        expertise_areas=profile.expertise_areas,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


# =============================================================================
# Adaptive Thresholds Endpoints
# =============================================================================

@router.get("/thresholds", response_model=ThresholdsResponse)
async def get_thresholds(
    user_id: Optional[str] = Query(None, description="User ID")
):
    """Get adaptive voice thresholds.

    Returns the learned silence detection thresholds for the user's
    speaking patterns.
    """
    uid = get_user_id_or_generate(user_id)
    service = get_memory_service()
    thresholds = service.get_thresholds(uid)

    return ThresholdsResponse(
        user_id=uid,
        silence_threshold_ms=thresholds.silence_threshold_ms,
        false_positive_rate=thresholds.false_positive_rate,
        total_interactions=thresholds.total_interactions,
        is_personalized=len(thresholds.pause_samples) >= 5,
    )


@router.post("/thresholds", response_model=ThresholdsResponse)
async def update_thresholds(
    request: ThresholdsUpdateRequest,
    user_id: Optional[str] = Query(None, description="User ID")
):
    """Update adaptive voice thresholds.

    Records new pause samples and false positive events to
    improve speech detection accuracy over time.
    """
    uid = get_user_id_or_generate(user_id)
    service = get_memory_service()

    thresholds = service.update_thresholds(
        user_id=uid,
        silence_threshold_ms=request.silence_threshold_ms,
        pause_sample=request.pause_sample,
        false_positive=request.false_positive,
    )

    return ThresholdsResponse(
        user_id=uid,
        silence_threshold_ms=thresholds.silence_threshold_ms,
        false_positive_rate=thresholds.false_positive_rate,
        total_interactions=thresholds.total_interactions,
        is_personalized=len(thresholds.pause_samples) >= 5,
    )


@router.delete("/thresholds")
async def reset_thresholds(
    user_id: Optional[str] = Query(None, description="User ID")
):
    """Reset adaptive thresholds to defaults.

    Clears all learned pause data and resets to default thresholds.
    """
    uid = get_user_id_or_generate(user_id)
    service = get_memory_service()

    # Reset by updating with defaults
    from ..models.memory import AdaptiveThresholds
    default = AdaptiveThresholds(user_id=uid)

    service.update_thresholds(
        user_id=uid,
        silence_threshold_ms=default.silence_threshold_ms,
    )

    return {"message": "Thresholds reset to defaults", "user_id": uid}


# =============================================================================
# Memory Context Endpoint
# =============================================================================

@router.get("/memory-context", response_model=Optional[MemoryContextResponse])
async def get_memory_context(
    user_id: Optional[str] = Query(None, description="User ID")
):
    """Get memory context for AI personalization.

    Returns relevant user context for injecting into AI prompts.
    Only returns data if consent is granted.
    """
    uid = get_user_id_or_generate(user_id)
    service = get_memory_service()

    context = service.get_memory_context(uid)
    if not context:
        return None

    return context


# =============================================================================
# Data Management Endpoints
# =============================================================================

@router.delete("/memory")
async def clear_all_memory(
    user_id: Optional[str] = Query(None, description="User ID")
):
    """Clear all stored memory for a user.

    Revokes consent and deletes all stored data including
    conversation history, profile data, and learned thresholds.
    """
    uid = get_user_id_or_generate(user_id)
    service = get_memory_service()

    # Revoking consent clears all data
    service.update_consent(uid, granted=False)

    logger.info("Cleared all memory for user %s", uid)

    return {"message": "All memory cleared", "user_id": uid}
