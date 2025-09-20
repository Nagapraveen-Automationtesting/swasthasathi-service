# 🎯 Signup Service Endpoint Documentation

## 📋 Overview

A dedicated signup service endpoint has been created in the People Cost Dashboard API that provides comprehensive confirmation responses after successfully creating users in the database.

## 🚀 New Endpoint

### `POST /user/signup`

**Purpose:** User registration with detailed confirmation response  
**Authentication:** None required  
**Response Model:** `Dict[str, Any]`

## 📊 Request Payload

The signup endpoint accepts the same payload as the existing register endpoint:

```json
{
    "user_name": "Alice Johnson",
    "gender": "Female",
    "dob": "1988-07-12",
    "mobile_num": "+1555123456",
    "email_id": "alice.johnson@example.com",
    "address": "456 Signup Street",
    "city": "Boston",
    "blood_group": "A-",
    "height": 165.0,
    "weight": 58.5,
    "diabetics": false,
    "bp": "115/75",
    "password": "securesignup456"
}
```

## ✅ Response Structure

### Successful Signup (200 OK)
```json
{
    "success": true,
    "message": "User account created successfully",
    "status": "ACCOUNT_CREATED",
    "user_details": {
        "user_id": 123,
        "user_name": "Alice Johnson",
        "email_id": "alice.johnson@example.com",
        "mobile_num": "+1555123456",
        "city": "Boston",
        "gender": "Female",
        "status": true,
        "created_on": "2024-09-16T12:00:00Z",
        "account_type": "STANDARD",
        "profile_completion": "BASIC"
    },
    "next_steps": [
        "Verify your email address",
        "Complete your profile information", 
        "Login to access your dashboard"
    ],
    "additional_info": {
        "health_profile_status": "CREATED",
        "total_users_in_system": 156,
        "registration_timestamp": "2024-09-16T12:00:00Z",
        "account_activation": "ACTIVE"
    }
}
```

### Error Responses

#### Duplicate Email (409 Conflict)
```json
{
    "detail": {
        "error": "User already exists",
        "message": "An account with email alice@example.com already exists",
        "suggestion": "Please use a different email or try logging in"
    }
}
```

#### Duplicate Mobile (409 Conflict)
```json
{
    "detail": {
        "error": "Mobile number already registered",
        "message": "An account with mobile number +1555123456 already exists",
        "suggestion": "Please use a different mobile number"
    }
}
```

#### Validation Error (400 Bad Request)
```json
{
    "detail": "Email and password are required"
}
```

## 🔧 Key Features

### ✅ Database Integration
- **User Creation**: Creates user record in `Users` MongoDB collection
- **Auto-increment ID**: Generates sequential user_id automatically
- **Password Hashing**: Securely hashes passwords using bcrypt
- **Timestamp Tracking**: Records creation timestamp

### ✅ Validation & Security
- **Email Uniqueness**: Prevents duplicate email addresses
- **Mobile Uniqueness**: Prevents duplicate mobile numbers
- **Required Fields**: Validates email and password presence
- **Data Sanitization**: Removes sensitive data from responses

### ✅ Rich Response Data
- **User Details**: Complete user information (without sensitive data)
- **Health Profile Status**: Indicates if health data was provided
- **System Statistics**: Total active users count
- **Account Status**: Confirmation of account activation
- **Next Steps**: Guidance for user onboarding

### ✅ Error Handling
- **Structured Errors**: Consistent error response format
- **Helpful Messages**: Clear error descriptions and suggestions
- **HTTP Status Codes**: Proper status codes (409 for conflicts, etc.)
- **Logging**: Comprehensive logging for debugging

## 🧪 Testing

### Manual Testing
Use the provided demo script:
```bash
python signup_endpoint_demo.py
```

### Postman Testing
The updated Postman collection includes:
- **"Signup User (With Confirmation)"** request
- Auto-saves user_id and email to environment variables
- Validates response structure in test scripts

### cURL Testing
```bash
curl -X POST http://localhost:8000/user/signup \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "Test User",
    "gender": "Other",
    "dob": "1990-01-01",
    "mobile_num": "+1234567890",
    "email_id": "test@example.com",
    "address": "123 Test St",
    "city": "Test City",
    "password": "testpass123"
  }'
```

## 📋 Differences from /register Endpoint

| Feature | /register | /signup |
|---------|-----------|---------|
| Response Format | Simple success/error | Detailed confirmation |
| User Details | Basic response | Complete user profile |
| System Info | None | User count, timestamps |
| Next Steps | None | Onboarding guidance |
| Health Status | None | Health profile assessment |
| Error Format | Simple messages | Structured with suggestions |

## 🎯 Use Cases

### Frontend Integration
Perfect for applications that need:
- **Rich signup confirmations** with user details
- **Onboarding flows** with next step guidance
- **Dashboard statistics** (total users, etc.)
- **Health profile tracking** from registration

### Mobile Applications
Ideal for mobile apps requiring:
- **Complete user data** after registration
- **Account status confirmation**
- **Profile completion indicators**
- **User engagement metrics**

## 🔄 Workflow Integration

### Typical Usage Flow
1. **Frontend Form** → Collect user registration data
2. **POST /user/signup** → Create account with confirmation
3. **Display Confirmation** → Show success with user details
4. **Guide Next Steps** → Direct user to email verification/login
5. **Update UI** → Show profile completion status

### Error Handling Flow
1. **Validation Error** → Show field-specific errors
2. **Duplicate User** → Suggest login or different email/mobile
3. **Server Error** → Show retry option with support contact

## 📊 Monitoring & Analytics

The endpoint provides data for:
- **Registration Success Rate** via response logging
- **Total User Growth** via system user count
- **Health Profile Adoption** via health_profile_status
- **Error Pattern Analysis** via structured error responses

---

🎉 **Your signup service is ready!** The endpoint provides comprehensive confirmation after database updates, exactly as requested.

**Test it now:** Use the Postman collection or run `python signup_endpoint_demo.py`
