# Firebase Authentication Setup for LOKI AI Tutor

This document provides instructions for setting up Firebase Authentication for the LOKI AI Tutor application.

## Overview

LOKI AI Tutor uses Firebase Authentication for user management. The application supports both:

1. Server-side authentication through Flask and Firebase Admin SDK
2. Client-side authentication through Firebase Auth JavaScript SDK

## Prerequisites

- A Firebase project (create one at [Firebase Console](https://console.firebase.google.com/))
- Firebase project credentials
- Environment variables set up with Firebase configuration

## Configuration Steps

### 1. Firebase Project Setup

1. Create a project in the [Firebase Console](https://console.firebase.google.com/)
2. Enable Email/Password authentication:
   - Go to Authentication > Sign-in method
   - Enable Email/Password provider

### 2. Server-Side Configuration

The server-side uses Firebase Admin SDK for authentication. You need to:

1. Generate a service account key:
   - In Firebase Console, go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file securely

2. Set environment variables in `.env` file:

```
# Firebase Config
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id
FIREBASE_APP_ID=your-app-id
FIREBASE_MEASUREMENT_ID=your-measurement-id
FIREBASE_SERVICE_ACCOUNT_PATH=path/to/your-service-account.json
```

### 3. Client-Side Configuration

The client-side uses Firebase JavaScript SDK. Update the configuration in `static/js/firebase-init.js`:

```javascript
// Replace this with your actual Firebase configuration
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project-id.appspot.com",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID",
  measurementId: "YOUR_MEASUREMENT_ID"
};
```

## Authentication Flow

### Registration

1. User submits registration form
2. Server creates user in Firebase using Admin SDK
3. User is redirected to subscription plans page

### Login

1. User submits login form
2. Server authenticates with Firebase using Admin SDK
3. If successful, user is logged in and redirected to appropriate dashboard

### Alternative Authentication Flow

The application also supports direct Firebase Authentication through the client-side JavaScript SDK:

1. User's credentials are sent to Firebase Auth directly
2. On successful authentication, Firebase returns a token
3. The token is sent to the backend for verification
4. The backend creates a session for the user

## Testing

To verify the authentication setup:

1. Create a test user through the registration form
2. Verify that the user appears in Firebase Console > Authentication > Users
3. Test login with the created user
4. Test password reset functionality

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Check if your Firebase configuration is correct
2. **Token Verification Failed**: Ensure that the service account has proper permissions
3. **CORS Issues**: Ensure that your Firebase project has the appropriate domains added to the allowed list

### Debug Mode

To enable detailed logging for authentication:

1. Add `console.log` statements in the Firebase authentication callbacks
2. Check browser console for client-side errors
3. Check server logs for backend errors

## Security Considerations

1. Keep your Firebase service account key secure
2. Don't commit `.env` files or service account keys to version control
3. Set up Firebase Security Rules to restrict access to your Firebase resources
