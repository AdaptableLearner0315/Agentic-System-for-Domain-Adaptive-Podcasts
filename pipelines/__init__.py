"""
Pipelines Module
Author: Sarath

Provides Normal and Pro pipelines for podcast generation.

- NormalPipeline: Fast generation (90-120 seconds target)
- ProPipeline: High-quality generation (5-8 minutes target)
"""

from pipelines.normal_pipeline import NormalPipeline
from pipelines.pro_pipeline import ProPipeline

__all__ = [
    'NormalPipeline',
    'ProPipeline',
]
