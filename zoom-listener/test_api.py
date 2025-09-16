#!/usr/bin/env python3
"""
Test script for the Zoom Meeting Recorder API
"""

import requests
import time
import json

API_BASE_URL = "http://localhost:8000"

def test_start_meeting():
    """Test the /start endpoint"""
    print("Testing /start endpoint...")
    
    # Test data
    meeting_data = {
        "meeting_id": "83300774340",
        "meeting_password": "N69MNbM6P45bERruycF7kpm5ZPXNXg.1"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/start", json=meeting_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_recording(meeting_id):
    """Test the /record endpoint"""
    print(f"\nTesting /record endpoint for meeting {meeting_id}...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/record/{meeting_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_status(meeting_id):
    """Test the /status endpoint"""
    print(f"\nTesting /status endpoint for meeting {meeting_id}...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/status/{meeting_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("Testing root endpoint...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("Zoom Meeting Recorder API Test Suite")
    print("=" * 40)
    
    # Test root endpoint
    test_root_endpoint()
    
    # Test meeting ID
    meeting_id = "83300774340"
    
    # Test status before starting
    test_get_status(meeting_id)
    
    # Test starting a meeting
    if test_start_meeting():
        print("\nMeeting started successfully!")
        
        # Wait a bit for the meeting to initialize
        print("Waiting 5 seconds for meeting to initialize...")
        time.sleep(5)
        
        # Test status after starting
        test_get_status(meeting_id)
        
        # Test getting recording (might not exist yet)
        test_get_recording(meeting_id)
        
        print("\nTest completed!")
        print("Note: The meeting bot will continue running in the background.")
        print("You can check the status and recordings using the API endpoints.")
    else:
        print("Failed to start meeting. Check the API server and configuration.")

if __name__ == "__main__":
    main()
