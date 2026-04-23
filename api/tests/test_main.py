import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Add the api directory to path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def mock_redis():
    with patch("main.r") as mock_r:
        mock_r.ping.return_value = True
        mock_r.lpush.return_value = 1
        mock_r.hset.return_value = 1
        mock_r.hget.return_value = "queued"
        yield mock_r


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_job_returns_job_id(client):
    response = client.post("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert len(data["job_id"]) > 0

def test_create_job_pushes_to_correct_queue(client, mock_redis):
    client.post("/jobs")
    mock_redis.lpush.assert_called_once()
    call_args = mock_redis.lpush.call_args[0]
    assert call_args[0] == "jobs"

def test_get_nonexistent_job_returns_404(client, mock_redis):
    mock_redis.hget.return_value = None
    response = client.get("/jobs/nonexistent-id")
    assert response.status_code == 404
