# People Cost Dashboard API - Postman Collection Guide

## 📋 Overview

This guide provides comprehensive instructions for using the Postman collection to test the People Cost Dashboard API. The collection includes all endpoints with proper authentication, request examples, and automated token management.

## 📦 Files Included

- `PeopleCostDashboard.postman_collection.json` - Main collection with all API endpoints
- `PeopleCostDashboard.postman_environment.json` - Environment variables for development
- `POSTMAN_GUIDE.md` - This guide

## 🚀 Quick Setup

### 1. Import Collection and Environment

1. Open Postman
2. Click **Import** button
3. Select both JSON files:
   - `PeopleCostDashboard.postman_collection.json`
   - `PeopleCostDashboard.postman_environment.json`
4. Select the **"People Cost Dashboard - Development"** environment from the dropdown

### 2. Configure Base URL

The environment is pre-configured with:
- **base_url**: `http://localhost:8000`

Update this if your server runs on a different port or domain.

### 3. Start Your API Server

```bash
cd /path/to/your/project
source venv/bin/activate  # or activate your virtual environment
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Endpoints Overview

### 🔐 Authentication Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/user/register` | POST | Register new user | ❌ |
| `/user/login` | POST | User login | ❌ |
| `/user/refresh` | POST | Refresh access token | ❌ |
| `/user/logout` | POST | Logout (revoke refresh token) | ✅ |
| `/user/logout-all` | POST | Logout from all devices | ✅ |

### 👤 User Management Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/user/profile` | GET | Get current user profile | ✅ |
| `/user/users` | GET | Get all users (paginated) | ✅ |
| `/user/users/search` | GET | Search users | ✅ |
| `/user/users/{user_id}` | GET | Get specific user by ID | ✅ |
| `/user/users/{user_id}` | PUT | Update user details | ✅ |
| `/user/users/{user_id}` | DELETE | Deactivate user (soft delete) | ✅ |
| `/user/change-password` | POST | Change user password | ✅ |

### 📁 File Upload Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/upload/generate-upload-url` | POST | Generate SAS token for file upload | ✅ |

### 🏥 Health Check

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Check API health status | ❌ |

## 🔄 Automated Features

### Token Management
- **Auto-login**: Tokens are automatically saved after successful login
- **Auto-refresh**: Tokens are refreshed automatically before expiry
- **Auto-cleanup**: Tokens are cleared on authentication failure

### Environment Variables
The collection automatically manages these variables:
- `access_token` - JWT access token
- `refresh_token` - JWT refresh token  
- `user_id` - Current user ID
- `email_id` - Current user email
- `mobile_num` - Current user mobile number

## 📝 Usage Flow

### 1. Register a New User
```
POST /user/register
```
**Body Example:**
```json
{
    "user_name": "John Doe",
    "gender": "Male",
    "dob": "1990-05-15",
    "mobile_num": "+1234567890",
    "email_id": "john.doe@example.com",
    "address": "123 Main Street",
    "city": "New York",
    "blood_group": "O+",
    "height": 175.5,
    "weight": 70.2,
    "diabetics": false,
    "bp": "120/80",
    "password": "securepassword123"
}
```

### 2. Login
```
POST /user/login
```
**Body Example:**
```json
{
    "email": "john.doe@example.com",
    "password": "securepassword123"
}
```

**Response includes:**
- `access_token` (1 hour expiry)
- `refresh_token` (30 days expiry)
- `user_info` with userId, mobile_num, email_id

### 3. Access Protected Endpoints
After login, all subsequent requests automatically include the Bearer token.

## 🔧 Advanced Configuration

### Custom Environment Variables

You can add custom variables for different environments:

1. **Production Environment:**
   ```json
   {
       "base_url": "https://api.yourdomain.com",
       "environment": "production"
   }
   ```

2. **Staging Environment:**
   ```json
   {
       "base_url": "https://staging-api.yourdomain.com",
       "environment": "staging"
   }
   ```

### Environment-Specific Settings

Create separate environments for:
- **Development** (`http://localhost:8000`)
- **Testing** (`http://localhost:8001`)
- **Staging** (`https://staging-api.yourdomain.com`)
- **Production** (`https://api.yourdomain.com`)

## 🧪 Testing Scenarios

### Complete User Lifecycle Test
1. **Register** → New user registration
2. **Login** → Authenticate and get tokens
3. **Get Profile** → Verify user data
4. **Update Profile** → Modify user information
5. **Search Users** → Test search functionality
6. **Change Password** → Update credentials
7. **Logout** → Clean session

### Pagination Testing
Test the user listing with different parameters:
- `skip=0&limit=5` - First 5 users
- `skip=5&limit=5` - Next 5 users
- `skip=0&limit=100` - Large batch

### Search Testing
Test user search with various queries:
- By name: `q=john`
- By email: `q=@example.com`
- By city: `q=new york`
- By mobile: `q=+1234`

## 🛠️ Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Ensure you're logged in
   - Check if token has expired
   - Verify the token is included in headers

2. **404 Not Found**
   - Verify the base URL is correct
   - Check if the server is running
   - Confirm endpoint paths

3. **400 Bad Request**
   - Validate request body format
   - Check required fields
   - Verify data types

### Token Refresh Issues
If automatic token refresh fails:
1. Manually call the **Refresh Token** endpoint
2. Re-login if refresh token is expired
3. Check refresh token validity

## 📊 Response Examples

### Successful Login Response
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user_info": {
        "user_id": 1,
        "user_name": "John Doe",
        "email_id": "john.doe@example.com",
        "mobile_num": "+1234567890",
        "city": "New York",
        "status": true
    }
}
```

### User Profile Response
```json
{
    "user_id": 1,
    "user_name": "John Doe",
    "gender": "Male",
    "dob": "1990-05-15",
    "mobile_num": "+1234567890",
    "email_id": "john.doe@example.com",
    "address": "123 Main Street",
    "city": "New York",
    "status": true,
    "created_on": "2024-09-16T12:00:00Z",
    "blood_group": "O+",
    "height": 175.5,
    "weight": 70.2,
    "diabetics": false,
    "bp": "120/80"
}
```

## 🔒 Security Notes

1. **Never commit tokens** to version control
2. **Use HTTPS** in production environments
3. **Rotate secrets** regularly
4. **Monitor token usage** for suspicious activity
5. **Implement rate limiting** for production

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Verify your server is running correctly
3. Review the API documentation
4. Check server logs for detailed error messages

---

Happy testing! 🎉
