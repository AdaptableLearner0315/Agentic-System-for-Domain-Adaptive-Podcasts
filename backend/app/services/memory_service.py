"""
Memory service for persistent user personalization.

Manages user profiles, conversation history, and adaptive learning
data with support for consent-based memory storage.
"""

import uuid
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading

from ..models.memory import (
    UserProfile,
    UserMemory,
    MemoryConsent,
    ConversationMemory,
    AdaptiveThresholds,
    CommunicationStyle,
    MemoryContextResponse,
)
from ..logging_config import get_logger
from ..config import get_settings

logger = get_logger("memory_service")

# Memory storage file
MEMORY_FILE = "user_memories.json"

# Maximum conversations to keep per user
MAX_CONVERSATIONS_PER_USER = 50

# Maximum pause samples to keep
MAX_PAUSE_SAMPLES = 50


class MemoryService:
    """
    Service for managing user memory and personalization.

    Provides CRUD operations for user profiles, conversation memories,
    and adaptive thresholds with consent-aware storage.

    Attributes:
        _memories: In-memory cache of user memories
        _storage_path: Path to persistent storage
        _lock: Thread lock for safe concurrent access
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the memory service.

        Args:
            storage_dir: Directory for persistent storage.
                        Uses settings if not provided.
        """
        self._memories: Dict[str, UserMemory] = {}
        self._lock = threading.RLock()

        # Set up storage path
        settings = get_settings()
        base_dir = storage_dir or settings.output_dir
        self._storage_path = Path(base_dir) / MEMORY_FILE

        # Load existing memories
        self._load_memories()

    def _load_memories(self) -> None:
        """Load memories from persistent storage."""
        if not self._storage_path.exists():
            return

        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)

            for user_id, memory_data in data.items():
                try:
                    self._memories[user_id] = UserMemory(**memory_data)
                except Exception as e:
                    logger.warning(
                        "Failed to load memory for user %s: %s", user_id, str(e)
                    )
        except Exception as e:
            logger.error("Failed to load memories: %s", str(e))

    def _save_memories(self) -> None:
        """Save memories to persistent storage."""
        try:
            # Ensure directory exists
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Serialize memories
            data = {}
            for user_id, memory in self._memories.items():
                data[user_id] = json.loads(memory.model_dump_json())

            with open(self._storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save memories: %s", str(e))

    def _get_or_create_user(self, user_id: str) -> UserMemory:
        """Get or create a user memory object."""
        if user_id not in self._memories:
            profile = UserProfile(user_id=user_id)
            consent = MemoryConsent(user_id=user_id)
            self._memories[user_id] = UserMemory(
                user_id=user_id,
                profile=profile,
                consent=consent,
            )
        return self._memories[user_id]

    # =========================================================================
    # Consent Management
    # =========================================================================

    def get_consent(self, user_id: str) -> MemoryConsent:
        """Get consent status for a user.

        Args:
            user_id: User identifier.

        Returns:
            MemoryConsent with current status.
        """
        with self._lock:
            memory = self._get_or_create_user(user_id)
            return memory.consent

    def update_consent(
        self,
        user_id: str,
        granted: bool,
        scope: Optional[List[str]] = None,
    ) -> MemoryConsent:
        """Update consent status for a user.

        Args:
            user_id: User identifier.
            granted: Whether consent is granted.
            scope: Types of memory allowed.

        Returns:
            Updated MemoryConsent.
        """
        with self._lock:
            memory = self._get_or_create_user(user_id)

            memory.consent.granted = granted
            memory.consent.granted_at = datetime.utcnow() if granted else None

            if scope is not None:
                memory.consent.scope = scope

            # If consent revoked, clear sensitive data
            if not granted:
                self._clear_user_data(user_id)

            self._save_memories()
            logger.info(
                "Updated consent for user %s: granted=%s", user_id, granted
            )
            return memory.consent

    def _clear_user_data(self, user_id: str) -> None:
        """Clear user data when consent is revoked."""
        if user_id in self._memories:
            memory = self._memories[user_id]
            memory.conversations = []
            memory.relationship_notes = []
            memory.thresholds = None
            # Keep basic profile but clear personal data
            memory.profile.interests = []
            memory.profile.expertise_areas = []
            memory.profile.preferences = {}

    # =========================================================================
    # Profile Management
    # =========================================================================

    def get_profile(self, user_id: str) -> UserProfile:
        """Get user profile.

        Args:
            user_id: User identifier.

        Returns:
            UserProfile for the user.
        """
        with self._lock:
            memory = self._get_or_create_user(user_id)
            return memory.profile

    def update_profile(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        communication_style: Optional[CommunicationStyle] = None,
        interests: Optional[List[str]] = None,
        expertise_areas: Optional[List[str]] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> UserProfile:
        """Update user profile.

        Args:
            user_id: User identifier.
            display_name: User's preferred name.
            communication_style: Preferred style.
            interests: Topics of interest.
            expertise_areas: Areas of expertise.
            preferences: Additional preferences.

        Returns:
            Updated UserProfile.
        """
        with self._lock:
            memory = self._get_or_create_user(user_id)

            # Check consent
            if not memory.consent.granted:
                logger.warning(
                    "Attempted to update profile without consent: %s", user_id
                )
                return memory.profile

            profile = memory.profile

            if display_name is not None:
                profile.display_name = display_name

            if communication_style is not None:
                profile.communication_style = communication_style

            if interests is not None:
                profile.interests = interests

            if expertise_areas is not None:
                profile.expertise_areas = expertise_areas

            if preferences is not None:
                profile.preferences.update(preferences)

            profile.updated_at = datetime.utcnow()

            self._save_memories()
            logger.info("Updated profile for user %s", user_id)
            return profile

    # =========================================================================
    # Conversation Memory
    # =========================================================================

    def add_conversation_memory(
        self,
        user_id: str,
        session_id: str,
        job_id: str,
        summary: Optional[str] = None,
        topics_discussed: Optional[List[str]] = None,
        user_questions: Optional[List[str]] = None,
        user_reactions: Optional[Dict[str, str]] = None,
        insights: Optional[List[str]] = None,
    ) -> Optional[ConversationMemory]:
        """Add a conversation memory.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            job_id: Associated podcast job ID.
            summary: Conversation summary.
            topics_discussed: Topics covered.
            user_questions: Questions asked.
            user_reactions: User's reactions.
            insights: Insights about user.

        Returns:
            Created ConversationMemory or None if consent not granted.
        """
        with self._lock:
            memory = self._get_or_create_user(user_id)

            if not memory.consent.granted:
                return None

            if "history" not in memory.consent.scope:
                return None

            conv_memory = ConversationMemory(
                session_id=session_id,
                job_id=job_id,
                summary=summary,
                topics_discussed=topics_discussed or [],
                user_questions=user_questions or [],
                user_reactions=user_reactions or {},
                insights=insights or [],
            )

            memory.conversations.append(conv_memory)

            # Trim old conversations
            if len(memory.conversations) > MAX_CONVERSATIONS_PER_USER:
                memory.conversations = memory.conversations[-MAX_CONVERSATIONS_PER_USER:]

            # Add insights to relationship notes
            if insights:
                for insight in insights:
                    if insight not in memory.relationship_notes:
                        memory.relationship_notes.append(insight)

            self._save_memories()
            return conv_memory

    def get_recent_conversations(
        self,
        user_id: str,
        limit: int = 5,
    ) -> List[ConversationMemory]:
        """Get recent conversations for a user.

        Args:
            user_id: User identifier.
            limit: Maximum number to return.

        Returns:
            List of recent ConversationMemory objects.
        """
        with self._lock:
            memory = self._get_or_create_user(user_id)

            if not memory.consent.granted:
                return []

            return memory.conversations[-limit:]

    # =========================================================================
    # Adaptive Thresholds
    # =========================================================================

    def get_thresholds(self, user_id: str) -> AdaptiveThresholds:
        """Get adaptive voice thresholds for a user.

        Args:
            user_id: User identifier.

        Returns:
            AdaptiveThresholds for the user.
        """
        with self._lock:
            memory = self._get_or_create_user(user_id)

            if memory.thresholds is None:
                memory.thresholds = AdaptiveThresholds(user_id=user_id)

            return memory.thresholds

    def update_thresholds(
        self,
        user_id: str,
        silence_threshold_ms: Optional[int] = None,
        pause_sample: Optional[int] = None,
        false_positive: Optional[bool] = None,
    ) -> AdaptiveThresholds:
        """Update adaptive thresholds.

        Args:
            user_id: User identifier.
            silence_threshold_ms: New threshold value.
            pause_sample: New pause duration sample.
            false_positive: Whether last interaction was false positive.

        Returns:
            Updated AdaptiveThresholds.
        """
        with self._lock:
            memory = self._get_or_create_user(user_id)

            if memory.thresholds is None:
                memory.thresholds = AdaptiveThresholds(user_id=user_id)

            thresholds = memory.thresholds

            if silence_threshold_ms is not None:
                thresholds.silence_threshold_ms = silence_threshold_ms

            if pause_sample is not None:
                thresholds.pause_samples.append(pause_sample)
                if len(thresholds.pause_samples) > MAX_PAUSE_SAMPLES:
                    thresholds.pause_samples = thresholds.pause_samples[-MAX_PAUSE_SAMPLES:]

            if false_positive is not None:
                thresholds.total_interactions += 1
                if false_positive:
                    # Recalculate false positive rate
                    current_fps = thresholds.false_positive_rate * (
                        thresholds.total_interactions - 1
                    )
                    thresholds.false_positive_rate = (current_fps + 1) / thresholds.total_interactions
                else:
                    # Decay false positive rate slightly
                    thresholds.false_positive_rate = (
                        thresholds.false_positive_rate
                        * (thresholds.total_interactions - 1)
                        / thresholds.total_interactions
                    )

            thresholds.updated_at = datetime.utcnow()

            self._save_memories()
            return thresholds

    # =========================================================================
    # Memory Context for AI
    # =========================================================================

    def get_memory_context(self, user_id: str) -> Optional[MemoryContextResponse]:
        """Get memory context for AI prompt injection.

        Args:
            user_id: User identifier.

        Returns:
            MemoryContextResponse with relevant context, or None if no consent.
        """
        with self._lock:
            memory = self._get_or_create_user(user_id)

            if not memory.consent.granted:
                return None

            profile = memory.profile

            # Build communication preferences
            comm_prefs = {
                "verbosity": profile.communication_style.verbosity,
                "tone": profile.communication_style.tone,
                "use_analogies": profile.communication_style.use_analogies,
                "technical_depth": profile.communication_style.technical_depth,
            }

            # Get relevant history (recent conversation summaries)
            relevant_history = []
            for conv in memory.conversations[-5:]:
                if conv.summary:
                    relevant_history.append(conv.summary)

            # Add relationship notes
            relevant_history.extend(memory.relationship_notes[-5:])

            return MemoryContextResponse(
                user_id=user_id,
                display_name=profile.display_name,
                communication_preferences=comm_prefs,
                relevant_history=relevant_history,
                known_interests=profile.interests,
                expertise_level=profile.communication_style.technical_depth,
            )

    def build_memory_prompt(self, user_id: str) -> Optional[str]:
        """Build a memory-aware prompt segment for AI.

        Args:
            user_id: User identifier.

        Returns:
            Prompt segment with user context, or None if no consent.
        """
        context = self.get_memory_context(user_id)
        if not context:
            return None

        parts = []

        # User identity
        if context.display_name:
            parts.append(f"The user's name is {context.display_name}.")

        # Communication style
        style = context.communication_preferences
        parts.append(
            f"They prefer {style['verbosity']} responses in a {style['tone']} tone."
        )
        if style["use_analogies"]:
            parts.append("They appreciate analogies and examples.")
        parts.append(f"Their technical expertise is {style['technical_depth']}.")

        # Interests
        if context.known_interests:
            interests_str = ", ".join(context.known_interests[:5])
            parts.append(f"They're interested in: {interests_str}.")

        # History
        if context.relevant_history:
            parts.append("From previous conversations, you know:")
            for note in context.relevant_history[:3]:
                parts.append(f"- {note}")

        return "\n".join(parts)


# =============================================================================
# Singleton Instance
# =============================================================================

_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """Get or create the memory service singleton."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
