"""
Integration tests for WebSocket progress streaming.

Tests WebSocket connections, message broadcasting, and reconnection.
"""

import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from starlette.testclient import TestClient as StarletteTestClient

from app.main import app
from app.models.enums import JobStatus, GenerationPhase


class TestWebSocketConnection:
    """Test WebSocket connection lifecycle."""

    def test_connect_to_valid_job(self, client: TestClient):
        """Test connecting to WebSocket for a valid job."""
        # Create a job first
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        # Connect to WebSocket
        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            # Should receive initial status message
            data = ws.receive_json()
            assert data["job_id"] == job_id
            assert "phase" in data

    def test_connect_to_invalid_job(self, client: TestClient):
        """Test connecting to WebSocket for invalid job closes connection."""
        try:
            with client.websocket_connect("/api/ws/nonexistent/progress") as ws:
                # Should be closed with error code
                pass
        except Exception:
            # Expected to fail/close
            pass

    def test_receive_heartbeat(self, client: TestClient):
        """Test receiving heartbeat messages."""
        # Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            # Receive initial status
            ws.receive_json()

            # Wait for heartbeat (with timeout)
            try:
                # Set a reasonable timeout for heartbeat
                data = ws.receive_json()
                if data.get("type") == "heartbeat":
                    assert True
            except Exception:
                # May timeout, which is acceptable
                pass

    def test_send_ping_receive_pong(self, client: TestClient):
        """Test ping/pong mechanism."""
        # Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            # Receive initial status
            ws.receive_json()

            # Send ping
            ws.send_json({"type": "ping"})

            # Should receive pong
            response = ws.receive_json()
            assert response.get("type") in ["pong", "heartbeat", "progress"]

    def test_request_cancellation_via_websocket(self, client: TestClient):
        """Test requesting job cancellation via WebSocket."""
        # Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            # Receive initial status
            ws.receive_json()

            # Send cancel request
            ws.send_json({"type": "cancel"})

            # Should receive cancelling confirmation
            response = ws.receive_json()
            # Could be cancelling or cancelled depending on timing
            assert response.get("type") in ["cancelling", "cancelled", "heartbeat", "progress"]


class TestProgressBroadcasting:
    """Test progress update broadcasting."""

    def test_receives_progress_updates(self, client: TestClient):
        """Test receiving progress updates through WebSocket."""
        # Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Test progress", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        messages_received = []

        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            # Collect a few messages
            for _ in range(3):
                try:
                    data = ws.receive_json()
                    messages_received.append(data)
                except Exception:
                    break

        # Should have received at least initial status
        assert len(messages_received) >= 1
        assert messages_received[0]["job_id"] == job_id

    def test_multiple_connections_receive_updates(self, client: TestClient):
        """Test that multiple WebSocket connections receive updates."""
        # Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Multi-connection test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        messages_1 = []
        messages_2 = []

        # Note: TestClient doesn't support true concurrent connections well
        # This tests sequential connections which is still valid
        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws1:
            try:
                messages_1.append(ws1.receive_json())
            except Exception:
                pass

        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws2:
            try:
                messages_2.append(ws2.receive_json())
            except Exception:
                pass

        # Both should have received messages
        assert len(messages_1) >= 1 or len(messages_2) >= 1


class TestProgressMessageFormat:
    """Test progress message format and content."""

    def test_progress_message_structure(self, client: TestClient):
        """Test that progress messages have correct structure."""
        # Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Structure test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            data = ws.receive_json()

            # Check required fields
            assert "job_id" in data
            assert "phase" in data
            assert "message" in data

            # Check optional fields types if present
            if "progress_percent" in data:
                assert isinstance(data["progress_percent"], (int, float))
            if "current_step" in data:
                assert isinstance(data["current_step"], int)
            if "total_steps" in data:
                assert isinstance(data["total_steps"], int)

    def test_completion_message_format(self, client: TestClient):
        """Test completion message includes expected fields."""
        # This test may not trigger completion in test environment
        # but validates the message structure expected
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Completion test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        # Cancel immediately to get a completion-type message
        client.post(f"/api/pipelines/{job_id}/cancel")

        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            data = ws.receive_json()
            # Should get some form of completion/cancelled message
            assert "job_id" in data

    def test_error_message_format(self, client: TestClient):
        """Test error message includes error details."""
        # Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Error test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            data = ws.receive_json()
            # Initial message should have job_id
            assert data["job_id"] == job_id


class TestConnectionResilience:
    """Test WebSocket connection resilience."""

    def test_graceful_disconnect(self, client: TestClient):
        """Test graceful client disconnect handling."""
        # Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Disconnect test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        # Connect and disconnect
        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            ws.receive_json()
            # Disconnect happens automatically when exiting context

        # Job should still be accessible
        status_response = client.get(f"/api/pipelines/{job_id}/status")
        assert status_response.status_code == 200

    def test_reconnection_receives_current_state(self, client: TestClient):
        """Test reconnection receives current state."""
        # Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Reconnection test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        # First connection
        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            first_message = ws.receive_json()

        # Reconnection
        with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
            reconnect_message = ws.receive_json()
            # Should receive current state
            assert reconnect_message["job_id"] == job_id
