#!/usr/bin/env python3
"""
Quick API Demo Script
This script demonstrates the API functionality by making sample requests
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_HEADERS = {"Content-Type": "application/json"}

class APIDemo:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        
    def make_request(self, method, endpoint, data=None, auth_required=False):
        """Make HTTP request with optional authentication"""
        url = f"{self.base_url}{endpoint}"
        headers = API_HEADERS.copy()
        
        if auth_required and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def health_check(self):
        """Test the health endpoint"""
        print("🏥 Testing Health Check...")
        response = self.make_request("GET", "/health")
        if response and response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print("❌ Health check failed")
            return False
    
    def register_user(self):
        """Register a test user"""
        print("\n📝 Registering test user...")
        user_data = {
            "user_name": "Test User",
            "gender": "Other",
            "dob": "1995-01-01",
            "mobile_num": "+1234567890",
            "email_id": f"test.user.{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
            "address": "123 Test Street",
            "city": "Test City",
            "blood_group": "A+",
            "height": 170.0,
            "weight": 65.5,
            "diabetics": False,
            "bp": "120/80",
            "password": "testpassword123"
        }
        
        response = self.make_request("POST", "/user/register", user_data)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("success"):
                self.user_id = result.get("user_id")
                self.email = user_data["email_id"]
                self.password = user_data["password"]
                print(f"✅ User registered successfully with ID: {self.user_id}")
                return True
            else:
                print(f"❌ Registration failed: {result.get('message')}")
        else:
            print(f"❌ Registration failed with status: {response.status_code if response else 'No response'}")
        return False
    
    def login(self):
        """Login with the registered user"""
        print("\n🔐 Logging in...")
        login_data = {
            "email": self.email,
            "password": self.password
        }
        
        response = self.make_request("POST", "/user/login", login_data)
        if response and response.status_code == 200:
            result = response.json()
            self.access_token = result.get("access_token")
            self.refresh_token = result.get("refresh_token")
            user_info = result.get("user_info", {})
            print(f"✅ Login successful")
            print(f"   User ID: {user_info.get('user_id')}")
            print(f"   Email: {user_info.get('email_id')}")
            print(f"   Mobile: {user_info.get('mobile_num')}")
            return True
        else:
            print(f"❌ Login failed with status: {response.status_code if response else 'No response'}")
        return False
    
    def get_profile(self):
        """Get user profile"""
        print("\n👤 Getting user profile...")
        response = self.make_request("GET", "/user/profile", auth_required=True)
        if response and response.status_code == 200:
            profile = response.json()
            print("✅ Profile retrieved successfully")
            print(f"   Name: {profile.get('user_name')}")
            print(f"   City: {profile.get('city')}")
            print(f"   Status: {profile.get('status')}")
            return True
        else:
            print(f"❌ Failed to get profile: {response.status_code if response else 'No response'}")
        return False
    
    def get_all_users(self):
        """Get all users with pagination"""
        print("\n📋 Getting all users...")
        response = self.make_request("GET", "/user/users?skip=0&limit=5", auth_required=True)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("success"):
                users = result.get("users", [])
                total = result.get("total_count", 0)
                print(f"✅ Retrieved {len(users)} users out of {total} total")
                for user in users[:3]:  # Show first 3 users
                    print(f"   - {user.get('user_name')} ({user.get('email_id')})")
                return True
            else:
                print(f"❌ Failed to get users: {result.get('message')}")
        else:
            print(f"❌ Failed to get users: {response.status_code if response else 'No response'}")
        return False
    
    def update_profile(self):
        """Update user profile"""
        print("\n✏️ Updating user profile...")
        update_data = {
            "address": "456 Updated Street",
            "city": "Updated City",
            "height": 175.0,
            "weight": 70.0
        }
        
        response = self.make_request("PUT", f"/user/users/{self.user_id}", update_data, auth_required=True)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Profile updated successfully")
                return True
            else:
                print(f"❌ Update failed: {result.get('message')}")
        else:
            print(f"❌ Update failed: {response.status_code if response else 'No response'}")
        return False
    
    def search_users(self):
        """Search users"""
        print("\n🔍 Searching users...")
        response = self.make_request("GET", "/user/users/search?q=test&skip=0&limit=5", auth_required=True)
        if response and response.status_code == 200:
            result = response.json()
            if result.get("success"):
                users = result.get("users", [])
                print(f"✅ Found {len(users)} users matching 'test'")
                return True
            else:
                print(f"❌ Search failed: {result.get('message')}")
        else:
            print(f"❌ Search failed: {response.status_code if response else 'No response'}")
        return False
    
    def refresh_token_test(self):
        """Test token refresh"""
        print("\n🔄 Testing token refresh...")
        refresh_data = {"refresh_token": self.refresh_token}
        
        response = self.make_request("POST", "/user/refresh", refresh_data)
        if response and response.status_code == 200:
            result = response.json()
            new_token = result.get("access_token")
            if new_token:
                self.access_token = new_token
                print("✅ Token refreshed successfully")
                return True
        print("❌ Token refresh failed")
        return False
    
    def logout(self):
        """Logout user"""
        print("\n🚪 Logging out...")
        logout_data = {"refresh_token": self.refresh_token}
        
        response = self.make_request("POST", "/user/logout", logout_data, auth_required=True)
        if response and response.status_code == 200:
            print("✅ Logout successful")
            return True
        else:
            print(f"❌ Logout failed: {response.status_code if response else 'No response'}")
        return False
    
    def run_demo(self):
        """Run the complete demo"""
        print("🚀 Starting People Cost Dashboard API Demo")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.health_check),
            ("User Registration", self.register_user),
            ("User Login", self.login),
            ("Get Profile", self.get_profile),
            ("Get All Users", self.get_all_users),
            ("Update Profile", self.update_profile),
            ("Search Users", self.search_users),
            ("Token Refresh", self.refresh_token_test),
            ("Logout", self.logout)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name} failed with error: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Demo Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your API is working correctly.")
        elif passed >= total * 0.7:
            print("⚠️ Most tests passed. Check failed tests above.")
        else:
            print("💥 Many tests failed. Please check your API configuration.")
        
        return passed == total

def main():
    """Main function"""
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    
    print(f"🌐 Testing API at: {base_url}")
    
    # Check if server is reachable
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding correctly. Status: {response.status_code}")
            return False
    except requests.RequestException:
        print(f"❌ Cannot reach server at {base_url}")
        print("💡 Make sure your FastAPI server is running:")
        print("   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload")
        return False
    
    demo = APIDemo(base_url)
    return demo.run_demo()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
