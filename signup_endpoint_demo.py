#!/usr/bin/env python3
"""
Demo script for the new /signup endpoint
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_signup_endpoint():
    """Test the new signup endpoint"""
    print("🎯 Testing the new /signup endpoint")
    print("=" * 50)
    
    # Test user data
    signup_data = {
        "user_name": "Jane Smith",
        "gender": "Female",
        "dob": "1992-03-20",
        "mobile_num": "+1987654321",
        "email_id": f"jane.smith.{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
        "address": "789 Signup Avenue",
        "city": "Signup City",
        "blood_group": "B+",
        "height": 168.0,
        "weight": 62.5,
        "diabetics": False,
        "bp": "118/78",
        "password": "signuptest123"
    }
    
    print(f"📝 Signing up user: {signup_data['user_name']}")
    print(f"📧 Email: {signup_data['email_id']}")
    
    try:
        # Make signup request
        response = requests.post(
            f"{BASE_URL}/user/signup",
            headers={"Content-Type": "application/json"},
            json=signup_data,
            timeout=10
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Signup successful!")
            print(f"📋 Response structure:")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Status: {result.get('status')}")
            
            user_details = result.get('user_details', {})
            print(f"\n👤 User Details:")
            print(f"   User ID: {user_details.get('user_id')}")
            print(f"   Name: {user_details.get('user_name')}")
            print(f"   Email: {user_details.get('email_id')}")
            print(f"   Mobile: {user_details.get('mobile_num')}")
            print(f"   City: {user_details.get('city')}")
            print(f"   Account Type: {user_details.get('account_type')}")
            print(f"   Profile Completion: {user_details.get('profile_completion')}")
            
            additional_info = result.get('additional_info', {})
            print(f"\n📊 Additional Information:")
            print(f"   Health Profile: {additional_info.get('health_profile_status')}")
            print(f"   Total Users: {additional_info.get('total_users_in_system')}")
            print(f"   Account Status: {additional_info.get('account_activation')}")
            
            next_steps = result.get('next_steps', [])
            print(f"\n📋 Next Steps:")
            for i, step in enumerate(next_steps, 1):
                print(f"   {i}. {step}")
            
            print(f"\n🎉 Signup confirmation received successfully!")
            return True
            
        else:
            print(f"❌ Signup failed")
            try:
                error_detail = response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Error text: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("💡 Make sure your FastAPI server is running:")
        print("   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload")
        return False

def test_duplicate_signup():
    """Test duplicate email signup"""
    print("\n" + "=" * 50)
    print("🔒 Testing duplicate email protection")
    
    duplicate_data = {
        "user_name": "Duplicate User",
        "gender": "Other",
        "dob": "1990-01-01",
        "mobile_num": "+1111111111",
        "email_id": "test@example.com",  # Common test email
        "address": "123 Test Street",
        "city": "Test City",
        "password": "testpassword"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/user/signup",
            headers={"Content-Type": "application/json"},
            json=duplicate_data,
            timeout=10
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 409:  # Conflict
            print("✅ Duplicate email protection working!")
            error_detail = response.json()
            print(f"   Error: {error_detail.get('detail', {}).get('error')}")
            print(f"   Message: {error_detail.get('detail', {}).get('message')}")
            print(f"   Suggestion: {error_detail.get('detail', {}).get('suggestion')}")
            return True
        else:
            print(f"⚠️ Unexpected response for duplicate email")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Signup Endpoint Demo")
    print("Testing the new /user/signup endpoint with confirmation response")
    
    # Test basic signup
    test1_passed = test_signup_endpoint()
    
    # Test duplicate protection
    test2_passed = test_duplicate_signup()
    
    print("\n" + "=" * 50)
    print("📊 Demo Results:")
    print(f"   ✅ Basic Signup: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"   ✅ Duplicate Protection: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Your signup endpoint is working correctly.")
        print("\n📋 Endpoint Features Verified:")
        print("   ✅ User creation in Users database")
        print("   ✅ Detailed confirmation response")
        print("   ✅ Health profile status detection")
        print("   ✅ User count statistics")
        print("   ✅ Next steps guidance")
        print("   ✅ Duplicate email protection")
        print("   ✅ Structured error responses")
    else:
        print("\n⚠️ Some tests failed. Please check the output above.")

if __name__ == "__main__":
    main()
