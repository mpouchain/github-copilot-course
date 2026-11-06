import pytest

from src.app import activities

EXPECTED_ACTIVITY_COUNT = 9
REQUIRED_FIELDS = {"description", "schedule", "max_participants", "participants"}
EXISTING_ACTIVITY = "Chess Club"
EXISTING_PARTICIPANT = "michael@mergington.edu"
NEW_EMAIL = "new.student@mergington.edu"


def test_root_redirects_to_static_index(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities_with_fields(client):
    # Arrange
    expected_names = set(activities.keys())

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == EXPECTED_ACTIVITY_COUNT
    assert set(data.keys()) == expected_names
    for details in data.values():
        assert REQUIRED_FIELDS <= details.keys()


def test_signup_adds_participant(client):
    # Arrange
    params = {"email": NEW_EMAIL}

    # Act
    response = client.post(f"/activities/{EXISTING_ACTIVITY}/signup", params=params)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {NEW_EMAIL} for {EXISTING_ACTIVITY}"}
    assert NEW_EMAIL in activities[EXISTING_ACTIVITY]["participants"]


def test_signup_unknown_activity_returns_404(client):
    # Arrange
    unknown_activity = "Unknown Club"
    params = {"email": NEW_EMAIL}

    # Act
    response = client.post(f"/activities/{unknown_activity}/signup", params=params)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_duplicate_returns_400(client):
    # Arrange
    params = {"email": EXISTING_PARTICIPANT}

    # Act
    response = client.post(f"/activities/{EXISTING_ACTIVITY}/signup", params=params)

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_unregister_removes_participant(client):
    # Arrange
    params = {"email": EXISTING_PARTICIPANT}

    # Act
    response = client.delete(f"/activities/{EXISTING_ACTIVITY}/participants", params=params)

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {EXISTING_PARTICIPANT} from {EXISTING_ACTIVITY}"
    }
    assert EXISTING_PARTICIPANT not in activities[EXISTING_ACTIVITY]["participants"]


def test_unregister_unknown_activity_returns_404(client):
    # Arrange
    unknown_activity = "Unknown Club"
    params = {"email": EXISTING_PARTICIPANT}

    # Act
    response = client.delete(f"/activities/{unknown_activity}/participants", params=params)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_student_not_signed_up_returns_404(client):
    # Arrange
    params = {"email": NEW_EMAIL}

    # Act
    response = client.delete(f"/activities/{EXISTING_ACTIVITY}/participants", params=params)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}


def test_signup_then_get_activities_includes_new_participant(client):
    # Arrange
    params = {"email": NEW_EMAIL}
    client.post(f"/activities/{EXISTING_ACTIVITY}/signup", params=params)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert NEW_EMAIL in response.json()[EXISTING_ACTIVITY]["participants"]


def test_signup_rejected_when_activity_is_full(client):
    # Arrange
    max_participants = activities[EXISTING_ACTIVITY]["max_participants"]
    participants = activities[EXISTING_ACTIVITY]["participants"]
    while len(participants) < max_participants:
        participants.append(f"student{len(participants)}@mergington.edu")
    params = {"email": NEW_EMAIL}

    # Act
    response = client.post(f"/activities/{EXISTING_ACTIVITY}/signup", params=params)

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}
