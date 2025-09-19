#!/usr/bin/env python3
"""
Test script to demonstrate the background task functionality.
Tests the refactored code with background_tasks and utils modules.
"""

import requests
import json

# Base URL for the data ingestion service
BASE_URL = "http://localhost:8100"

def test_fbref_sync():
    """Test FBref ingestion synchronously"""
    print("Testing FBref sync ingestion...")
    response = requests.post(
        f"{BASE_URL}/sources/fbref",
        json={
            "get_current_season_only": True,
            "use_cache": True,
            "cutoff_days": 7,
            "run_in_background": False
        }
    )
    print(f"Response: {response.status_code}")
    print(f"Body: {json.dumps(response.json(), indent=2)}")
    print()

def test_fbref_background():
    """Test FBref ingestion in background"""
    print("Testing FBref background ingestion...")
    response = requests.post(
        f"{BASE_URL}/sources/fbref",
        json={
            "get_current_season_only": True,
            "use_cache": True,
            "cutoff_days": 7,
            "run_in_background": True
        }
    )
    print(f"Response: {response.status_code}")
    print(f"Body: {json.dumps(response.json(), indent=2)}")
    print()

def test_sofifa_background():
    """Test SOFIFA ingestion in background"""
    print("Testing SOFIFA background ingestion...")
    response = requests.post(
        f"{BASE_URL}/sources/sofifa/team_stats",
        json={
            "use_cache": True,
            "scrap_all": False,
            "run_in_background": True
        }
    )
    print(f"Response: {response.status_code}")
    print(f"Body: {json.dumps(response.json(), indent=2)}")
    print()

def test_odds_background():
    """Test odds ingestion in background"""
    print("Testing odds background ingestion...")
    response = requests.post(
        f"{BASE_URL}/sources/the_odds_api/odds",
        json={
            "run_in_background": True
        }
    )
    print(f"Response: {response.status_code}")
    print(f"Body: {json.dumps(response.json(), indent=2)}")
    print()

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Response: {response.status_code}")
    print(f"Body: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == "__main__":
    print("=== Testing Refactored Background Tasks ===")
    print("Make sure the data-ingestion service is running on port 8100")
    print()
    
    try:
        # Test health check first
        test_health_check()
        
        # Test sync first
        test_fbref_sync()
        
        # Test background tasks
        test_fbref_background()
        test_sofifa_background() 
        test_odds_background()
        
        print("All tests completed! Check the service logs to see background task progress.")
        print("The code is now properly organized with background_tasks.py and utils.py modules.")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the service. Make sure it's running on port 8100")
    except Exception as e:
        print(f"Error: {e}")
