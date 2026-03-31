import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: start each test from a clean snapshot
    original = {
        activity: data.copy()
        for activity, data in {
            k: {
                "description": v["description"],
                "schedule": v["schedule"],
                "max_participants": v["max_participants"],
                "participants": list(v["participants"]),
            }
            for k, v in activities.items()
        }.items()
    }

    yield

    # Teardown: restore in-memory data
    activities.clear()
    for name, data in original.items():
        activities[name] = {
            "description": data["description"],
            "schedule": data["schedule"],
            "max_participants": data["max_participants"],
            "participants": list(data["participants"]),
        }


client = TestClient(app)


def test_get_activities_returns_data():
    # Arrange
    # (fixture has already prepared activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["max_participants"] == 12


def test_signup_new_participant_succeeds_and_refreshes():
    # Arrange
    payload_email = "newstudent@mergington.edu"
    activity = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity}/signup?email={payload_email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {payload_email} for {activity}"
    assert payload_email in activities[activity]["participants"]


def test_signup_duplicate_participant_returns_400():
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_unregister_participant_succeeds():
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"

    # Act
    response = client.delete(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity}"
    assert email not in activities[activity]["participants"]


def test_unregister_missing_participant_returns_400():
    # Arrange
    email = "notthere@mergington.edu"
    activity = "Chess Club"

    # Act
    response = client.delete(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert "Not signed up" in response.json()["detail"]
