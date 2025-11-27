import pytest


def test_root_redirect(client):
    """Test that root path redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test retrieving all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert len(data) == 9


def test_get_activities_structure(client):
    """Test that activities have correct structure"""
    response = client.get("/activities")
    data = response.json()
    
    activity = data["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)


def test_signup_new_participant(client, reset_activities):
    """Test signing up a new participant to an activity"""
    response = client.post(
        "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "newstudent@mergington.edu" in data["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_already_registered(client, reset_activities):
    """Test that a student cannot sign up twice for the same activity"""
    # Try to sign up a student who is already registered
    response = client.post(
        "/activities/Chess%20Club/signup?email=michael@mergington.edu"
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_nonexistent_activity(client):
    """Test signing up for a non-existent activity"""
    response = client.post(
        "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_unregister_participant(client, reset_activities):
    """Test unregistering a participant from an activity"""
    response = client.post(
        "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "michael@mergington.edu" in data["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_not_registered(client, reset_activities):
    """Test unregistering a participant who is not registered"""
    response = client.post(
        "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
    )
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]


def test_unregister_nonexistent_activity(client):
    """Test unregistering from a non-existent activity"""
    response = client.post(
        "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_signup_and_unregister_cycle(client, reset_activities):
    """Test signing up and then unregistering"""
    email = "cycletest@mergington.edu"
    activity = "Programming Class"
    
    # Sign up
    signup_response = client.post(
        f"/activities/{activity}/signup?email={email}"
    )
    assert signup_response.status_code == 200
    
    # Verify signed up
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity]["participants"]
    
    # Unregister
    unregister_response = client.post(
        f"/activities/{activity}/unregister?email={email}"
    )
    assert unregister_response.status_code == 200
    
    # Verify unregistered
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity]["participants"]


def test_multiple_participants(client):
    """Test that multiple participants can be registered for same activity"""
    response = client.get("/activities")
    data = response.json()
    
    # Chess Club should have 2 participants
    chess_club = data["Chess Club"]
    assert len(chess_club["participants"]) >= 2


def test_participants_count_vs_max(client):
    """Test that participant count doesn't exceed max"""
    response = client.get("/activities")
    data = response.json()
    
    for activity_name, activity in data.items():
        participants_count = len(activity["participants"])
        max_participants = activity["max_participants"]
        assert participants_count <= max_participants, \
            f"{activity_name} has more participants than allowed"
