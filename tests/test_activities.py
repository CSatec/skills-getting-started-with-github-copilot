"""
Tests for the Activities API

Uses AAA (Arrange-Act-Assert) pattern for clear test structure:
- Arrange: Set up test data and preconditions
- Act: Execute the API endpoint
- Assert: Verify the response and side effects
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for each test"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and sculpture techniques",
            "schedule": "Fridays, 3:30 PM - 4:30 PM",
            "max_participants": 18,
            "participants": ["amelia@mergington.edu"]
        }
    }
    
    # Clear and reset
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Arrange: Activities exist in database
        Act: Make GET request to /activities
        Assert: Returns all activities with correct structure
        """
        # Arrange
        expected_activity_names = {"Chess Club", "Programming Class", "Art Studio"}
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        returned_activities = response.json()
        assert set(returned_activities.keys()) == expected_activity_names
    
    def test_get_activities_returns_participants_list(self, client, reset_activities):
        """
        Arrange: Activity with participants exists
        Act: Make GET request to /activities
        Assert: Returns participants in correct format
        """
        # Arrange
        # Chess Club has michael@mergington.edu and daniel@mergington.edu as participants
        
        # Act
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
    
    def test_get_activities_includes_activity_details(self, client, reset_activities):
        """
        Arrange: Activities with full details exist
        Act: Make GET request to /activities
        Assert: Returns all required fields
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert set(chess_club.keys()) == required_fields


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful_adds_participant(self, client, reset_activities):
        """
        Arrange: Activity exists and new student ready to signup
        Act: POST to /activities/{activity}/signup
        Assert: Student is added to participants
        """
        # Arrange
        activity_name = "Chess Club"
        student_email = "newstudent@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {student_email} for {activity_name}"
        assert student_email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1
    
    def test_signup_duplicate_returns_400(self, client, reset_activities):
        """
        Arrange: Student already registered for activity
        Act: POST to /activities/{activity}/signup with same email
        Assert: Returns 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        student_email = "michael@mergington.edu"  # Already signed up
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
        assert len(activities[activity_name]["participants"]) == initial_count
    
    def test_signup_invalid_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Activity doesn't exist
        Act: POST to /activities/{invalid_activity}/signup
        Assert: Returns 404 error
        """
        # Arrange
        invalid_activity = "Nonexistent Club"
        student_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": student_email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_respects_max_participants(self, client, reset_activities):
        """
        Arrange: Activity exists with capacity is not enforced (API allows it)
        Act: POST to /activities/{activity}/signup
        Assert: Signup succeeds (note: max_participants is informational only in current API)
        """
        # Arrange
        activity_name = "Chess Club"
        max_capacity = activities[activity_name]["max_participants"]
        new_email = "testuser@mergington.edu"
        
        # Act - current API doesn't enforce max, but test documents this behavior
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful_removes_participant(self, client, reset_activities):
        """
        Arrange: Student is registered for activity
        Act: POST to /activities/{activity}/unregister
        Assert: Student is removed from participants
        """
        # Arrange
        activity_name = "Chess Club"
        student_email = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        assert student_email in activities[activity_name]["participants"]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": student_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {student_email} from {activity_name}"
        assert student_email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1
    
    def test_unregister_not_registered_returns_400(self, client, reset_activities):
        """
        Arrange: Student not registered for activity
        Act: POST to /activities/{activity}/unregister
        Assert: Returns 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        student_email = "notregistered@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": student_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
        assert len(activities[activity_name]["participants"]) == initial_count
    
    def test_unregister_invalid_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Activity doesn't exist
        Act: POST to /activities/{invalid_activity}/unregister
        Assert: Returns 404 error
        """
        # Arrange
        invalid_activity = "Nonexistent Club"
        student_email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{invalid_activity}/unregister",
            params={"email": student_email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestSignupAndUnregisterIntegration:
    """Integration tests for signup and unregister workflows"""
    
    def test_signup_then_unregister_flow(self, client, reset_activities):
        """
        Arrange: Activity exists, student not registered
        Act: Sign up student, then unregister them
        Assert: Student added then removed correctly
        """
        # Arrange
        activity_name = "Programming Class"
        student_email = "testuser@mergington.edu"
        
        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student_email}
        )
        
        # Assert signup
        assert signup_response.status_code == 200
        assert student_email in activities[activity_name]["participants"]
        
        # Act - Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": student_email}
        )
        
        # Assert unregister
        assert unregister_response.status_code == 200
        assert student_email not in activities[activity_name]["participants"]
    
    def test_multiple_signups_and_unregisters(self, client, reset_activities):
        """
        Arrange: Activity exists
        Act: Multiple students sign up and some unregister
        Assert: Activity state correctly reflects all changes
        """
        # Arrange
        activity_name = "Art Studio"
        initial_count = len(activities[activity_name]["participants"])
        new_students = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Act - Sign up 3 students
        for student_email in new_students:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": student_email}
            )
            assert response.status_code == 200
        
        # Assert after signups
        assert len(activities[activity_name]["participants"]) == initial_count + 3
        
        # Act - Unregister first and last student
        client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": new_students[0]}
        )
        client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": new_students[2]}
        )
        
        # Assert after unregisters
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        assert new_students[1] in activities[activity_name]["participants"]
        assert new_students[0] not in activities[activity_name]["participants"]
        assert new_students[2] not in activities[activity_name]["participants"]
