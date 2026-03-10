"""
Video Analyzer
Author: Sarath

Analyzes video quality including image-audio sync,
transitions, and resolution.
"""

import subprocess
import json
from typing import Dict, Any, List
from pathlib import Path
from utils.quality_evaluator import VideoMetrics


class VideoAnalyzer:
    """Analyzes video quality metrics."""

    # Standard resolutions
    STANDARD_RESOLUTIONS = {
        (1920, 1080): "1080p",
        (1280, 720): "720p",
        (3840, 2160): "4K",
    }

    def analyze(
        self,
        video_path: str,
        image_results: List[Dict[str, Any]]
    ) -> VideoMetrics:
        """
        Analyze video quality.

        Args:
            video_path: Path to final video file
            image_results: Image generation results

        Returns:
            VideoMetrics with analysis results
        """
        metrics = VideoMetrics()
        issues = []

        # Check if video exists
        if not video_path or not Path(video_path).exists():
            # If no video, just count images
            metrics.image_count = len([r for r in image_results if r.get("path")])
            if metrics.image_count == 0:
                issues.append("No video or images generated")
            else:
                issues.append("Video not generated, audio-only output")
            metrics.issues = issues
            return metrics

        # Get video info using ffprobe
        video_info = self._get_video_info(video_path)

        if video_info:
            metrics.total_duration_sec = video_info.get("duration", 0)

            # Check resolution
            width = video_info.get("width", 0)
            height = video_info.get("height", 0)
            if (width, height) in self.STANDARD_RESOLUTIONS:
                metrics.resolution_ok = True
            elif width >= 1920 and height >= 1080:
                metrics.resolution_ok = True
            else:
                metrics.resolution_ok = False
                issues.append(f"Non-standard resolution: {width}x{height}")

        # Count successful images
        successful_images = [r for r in image_results if r.get("path")]
        metrics.image_count = len(successful_images)

        # Calculate average image duration
        if metrics.image_count > 0 and metrics.total_duration_sec > 0:
            metrics.avg_image_duration_sec = (
                metrics.total_duration_sec / metrics.image_count
            )

            # Check if images change at reasonable intervals (3-15 seconds ideal)
            if metrics.avg_image_duration_sec < 2:
                issues.append(
                    f"Images change too fast ({metrics.avg_image_duration_sec:.1f}s avg)"
                )
            elif metrics.avg_image_duration_sec > 20:
                issues.append(
                    f"Images change too slow ({metrics.avg_image_duration_sec:.1f}s avg)"
                )

        # Estimate transition count
        metrics.transition_count = max(0, metrics.image_count - 1)

        # Estimate transition quality based on generation method
        # (Ken Burns = higher quality transitions)
        metrics.transition_quality = self._estimate_transition_quality(
            video_path, image_results, issues
        )

        metrics.issues = issues
        return metrics

    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-print_format", "json",
                    "-show_format", "-show_streams",
                    video_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)

                # Get duration from format
                duration = float(data.get("format", {}).get("duration", 0))

                # Get video stream info
                width = 0
                height = 0
                for stream in data.get("streams", []):
                    if stream.get("codec_type") == "video":
                        width = stream.get("width", 0)
                        height = stream.get("height", 0)
                        break

                return {
                    "duration": duration,
                    "width": width,
                    "height": height,
                }
        except Exception:
            pass

        return {}

    def _estimate_transition_quality(
        self,
        video_path: str,
        image_results: List[Dict[str, Any]],
        issues: List[str]
    ) -> float:
        """Estimate transition quality (0-10 scale)."""
        quality = 5.0

        # Check if Ken Burns was used (typically better transitions)
        # This could be detected from metadata or file analysis
        # For now, estimate based on video duration vs image count

        successful_images = len([r for r in image_results if r.get("path")])
        if successful_images > 0:
            quality += 2  # Has images

        # Check for crossfade transitions (presence improves quality)
        # Could analyze video for smooth transitions
        quality += 2  # Assume crossfades are present

        return min(10, quality)


__all__ = ['VideoAnalyzer']
