import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

# Create test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
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
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore various art techniques and create artworks",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["lucas@mergington.edu", "ava@mergington.edu"]
        }
    }
    
    # Reset activities
    activities.clear()
    activities.update(original_activities)
    yield
    # Clean up after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities(self, reset_activities):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Art Club" in data
    
    def test_activities_have_correct_structure(self, reset_activities):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, reset_activities):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, reset_activities):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_already_registered(self, reset_activities):
        """Test signing up when already registered"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_at_max_capacity(self, reset_activities):
        """Test signing up when activity is at max capacity"""
        # Create a small activity with max participants = 2
        activities["Small Club"] = {
            "description": "Small test club",
            "schedule": "Every day",
            "max_participants": 2,
            "participants": ["student1@mergington.edu", "student2@mergington.edu"]
        }
        
        response = client.post(
            "/activities/Small Club/signup?email=student3@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 400
        data = response.json()
        assert "max capacity" in data["detail"]


class TestUnregisterFromActivity:
    """Test the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_participant(self, reset_activities):
        """Test unregistering a participant"""
        # First verify the participant exists
        activities_response = client.get("/activities")
        assert "michael@mergington.edu" in activities_response.json()["Chess Club"]["participants"]
        
        # Unregister the participant
        response = client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert "michael@mergington.edu" not in activities_response.json()["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, reset_activities):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered(self, reset_activities):
        """Test unregistering when not registered"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 404
        data = response.json()
        assert "not registered" in data["detail"]


class TestRootEndpoint:
    """Test the GET / endpoint"""
    
    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Redirect status code
        assert "/static/index.html" in response.headers["location"]
