"""
Agents Module
Author: Sarath

Exports all agents for the podcast enhancement system.

Available Agents:
- BaseAgent: Abstract base class for all agents
- ScriptDesignerAgent: Transforms transcripts into engaging scripts
- DirectorAgent: Reviews and approves scripts with quality control
- VisualEnhancerAgent: Generates narrative-driven images
- AudioDesignerAgent: Handles all audio processing (TTS, BGM, mixing)

Legacy agents (for backwards compatibility):
- ScriptEnhancer: Original script enhancer
- Director: Original director
- ImageGenerator: Original image generator
- TTSNarrator: Original TTS narrator
- MusicGenerator: Original music generator
"""

# Base agent
from agents.base_agent import BaseAgent

# New refactored agents
from agents.script_designer_agent import ScriptDesignerAgent
from agents.director_agent import DirectorAgent
from agents.visual_enhancer_agent import VisualEnhancerAgent
from agents.audio_designer_agent import AudioDesignerAgent

# Audio submodules (for direct access if needed)
from agents.audio_designer import (
    TTSNarrator,
    BGMGenerator,
    VoiceStyleEngine,
    AudioMixer,
)

# Legacy imports (for backwards compatibility)
from agents.script_enhancer import ScriptEnhancer
from agents.director import Director
from agents.image_generator import ImageGenerator
from agents.tts_narrator import TTSNarrator as LegacyTTSNarrator
from agents.music_generator import MusicGenerator

__all__ = [
    # Base
    'BaseAgent',
    # New agents
    'ScriptDesignerAgent',
    'DirectorAgent',
    'VisualEnhancerAgent',
    'AudioDesignerAgent',
    # Audio submodules
    'TTSNarrator',
    'BGMGenerator',
    'VoiceStyleEngine',
    'AudioMixer',
    # Legacy agents
    'ScriptEnhancer',
    'Director',
    'ImageGenerator',
    'MusicGenerator',
    # Factory function
    'create_agent',
    'get_all_agents',
]


def create_agent(agent_type: str, **kwargs):
    """
    Factory function to create agents by type.

    Args:
        agent_type: Type of agent to create
            - 'script_designer' or 'script_enhancer'
            - 'director'
            - 'visual_enhancer' or 'image_generator'
            - 'audio_designer'
            - 'tts_narrator'
            - 'bgm_generator' or 'music_generator'
        **kwargs: Additional arguments passed to agent constructor

    Returns:
        Agent instance

    Example:
        director = create_agent('director', model='claude-opus-4-5-20250514')
    """
    agent_map = {
        # New agents
        'script_designer': ScriptDesignerAgent,
        'director': DirectorAgent,
        'visual_enhancer': VisualEnhancerAgent,
        'audio_designer': AudioDesignerAgent,

        # Legacy aliases
        'script_enhancer': ScriptDesignerAgent,
        'image_generator': VisualEnhancerAgent,

        # Submodule agents
        'tts_narrator': TTSNarrator,
        'bgm_generator': BGMGenerator,
        'music_generator': BGMGenerator,
        'voice_style_engine': VoiceStyleEngine,
        'audio_mixer': AudioMixer,
    }

    agent_type_lower = agent_type.lower().replace('-', '_')

    if agent_type_lower not in agent_map:
        available = ', '.join(sorted(agent_map.keys()))
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {available}")

    return agent_map[agent_type_lower](**kwargs)


def get_all_agents(model: str = "claude-opus-4-5-20250514") -> dict:
    """
    Create instances of all main agents.

    Args:
        model: LLM model to use for agents that require it

    Returns:
        Dictionary of agent name -> agent instance

    Example:
        agents = get_all_agents()
        script = agents['script_designer'].enhance(transcript)
    """
    return {
        'script_designer': ScriptDesignerAgent(model=model),
        'director': DirectorAgent(model=model),
        'visual_enhancer': VisualEnhancerAgent(),
        'audio_designer': AudioDesignerAgent(),
    }
