# 📦 Postman Collection for People Cost Dashboard API

## 🎯 Complete Testing Suite

This directory contains a comprehensive Postman collection and testing suite for the People Cost Dashboard API. All files are ready to import and use immediately.

## 📁 Files Overview

### 🔧 Postman Files
1. **`PeopleCostDashboard.postman_collection.json`**
   - Complete API collection with all endpoints
   - Automated token management
   - Pre-request scripts for token refresh
   - Test scripts for response validation
   - **Import this in Postman to get all API endpoints**

2. **`PeopleCostDashboard.postman_environment.json`**
   - Development environment variables
   - Pre-configured for localhost:8000
   - Auto-managed tokens and user data
   - **Import this to set up your testing environment**

### 📚 Documentation
3. **`POSTMAN_GUIDE.md`**
   - Comprehensive guide for using the collection
   - Step-by-step instructions
   - Troubleshooting tips
   - API endpoint documentation
   - **Read this for detailed usage instructions**

4. **`POSTMAN_FILES_README.md`** (this file)
   - Overview of all files
   - Quick start instructions

### 🧪 Testing Tools
5. **`test_api_demo.py`**
   - Python script for automated API testing
   - Demonstrates complete user lifecycle
   - Can be run independently to verify API
   - **Execute this to test your API programmatically**

## 🚀 Quick Start (3 Steps)

### 1. Import to Postman
```bash
# In Postman:
# 1. Click "Import"
# 2. Select these files:
#    - PeopleCostDashboard.postman_collection.json
#    - PeopleCostDashboard.postman_environment.json
# 3. Select "People Cost Dashboard - Development" environment
```

### 2. Start Your API Server
```bash
cd /path/to/your/project
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Test with Postman
```bash
# In Postman:
# 1. Go to "Authentication" folder
# 2. Run "Register User" request
# 3. Run "Login" request (tokens auto-saved)
# 4. All other requests now have authentication
```

## 🎯 What's Included

### ✅ Complete API Coverage
- **Authentication**: Register, Login, Logout, Token Refresh
- **User Management**: CRUD operations, Search, Profile management
- **File Upload**: SAS token generation for Azure Blob Storage
- **Health Check**: API status verification

### ✅ Advanced Features
- **Auto Token Management**: Tokens saved and refreshed automatically
- **Error Handling**: Automatic token cleanup on auth failures
- **Environment Variables**: Easy switching between dev/staging/prod
- **Request Examples**: Pre-filled with realistic test data
- **Response Validation**: Automated checks for successful responses

### ✅ User Data Fields Tested
```json
{
  "user_id": "Auto-generated",
  "user_name": "Full name",
  "gender": "Male/Female/Other",
  "dob": "Date of birth",
  "mobile_num": "Phone number",
  "email_id": "Email address",
  "address": "Physical address",
  "city": "City name",
  "status": "Active/Inactive",
  "created_on": "Registration timestamp",
  "blood_group": "Blood type",
  "height": "Height in cm",
  "weight": "Weight in kg",
  "diabetics": "Boolean flag",
  "bp": "Blood pressure reading"
}
```

## 🛠️ Alternative Testing Methods

### Option 1: Use Postman (Recommended)
- Import the collection
- Visual interface
- Auto token management
- Easy request modification

### Option 2: Use Python Demo Script
```bash
# Test programmatically
python test_api_demo.py
# or with custom URL
python test_api_demo.py http://your-api-url:8000
```

### Option 3: Use cURL Commands
```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/user/register \
  -H "Content-Type: application/json" \
  -d '{"user_name": "Test User", "email_id": "test@example.com", ...}'
```

## 🎨 Customization

### For Different Environments
1. **Duplicate the environment** in Postman
2. **Update the base_url**:
   - Development: `http://localhost:8000`
   - Staging: `https://staging-api.yourdomain.com`
   - Production: `https://api.yourdomain.com`

### For Custom Data
1. **Modify request examples** in the collection
2. **Update environment variables** as needed
3. **Add custom pre-request scripts** for data generation

## 🔒 Security Notes

### ⚠️ Important for Production
- **Change default passwords** in examples
- **Use HTTPS** for production URLs
- **Don't commit tokens** to version control
- **Rotate JWT secrets** regularly

### 🛡️ Token Security
- Tokens auto-expire (1 hour for access, 30 days for refresh)
- Automatic refresh before expiry
- Secure logout with token revocation
- Multi-device session management

## 📞 Support & Troubleshooting

### Common Issues
1. **401 Unauthorized**: Login again or check token expiry
2. **Connection Refused**: Ensure API server is running
3. **404 Not Found**: Verify the base_url in environment

### Getting Help
1. Check the `POSTMAN_GUIDE.md` for detailed instructions
2. Run the `test_api_demo.py` script to verify API health
3. Check server logs for detailed error messages
4. Verify environment variables are set correctly

## 📊 Testing Checklist

- [ ] Import Postman collection and environment
- [ ] Start API server on correct port
- [ ] Run health check endpoint
- [ ] Register a test user
- [ ] Login and verify token storage
- [ ] Test protected endpoints
- [ ] Verify token refresh functionality
- [ ] Test logout and session cleanup

---

🎉 **You're all set!** Start with the health check endpoint and work your way through the authentication flow. The collection will guide you through testing all features of your People Cost Dashboard API.

**Need help?** Check `POSTMAN_GUIDE.md` for detailed instructions and troubleshooting tips.
