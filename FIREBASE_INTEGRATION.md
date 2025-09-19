# Firebase Authentication Integration

This document outlines the Firebase authentication integration added to the Tensora Ai project.

## Features Added

### 1. Firebase Configuration
- **File**: `src/firebase/config.js`
- **Purpose**: Initializes Firebase app with your provided configuration
- **Services**: Authentication, Analytics

### 2. Authentication Service
- **File**: `src/firebase/auth.js`
- **Functions**:
  - `signUpWithEmail(email, password, displayName)` - Register new users
  - `signInWithEmail(email, password)` - Login existing users
  - `signInWithGoogle()` - Sign in with Google OAuth
  - `logout()` - Sign out current user
  - `resetPassword(email)` - Send password reset email
  - `getCurrentUser()` - Get current authenticated user

### 3. Authentication Context
- **File**: `src/contexts/AuthContext.jsx`
- **Purpose**: Provides authentication state management across the app
- **Hook**: `useAuth()` to access current user and loading state

### 4. Updated Components

#### Sign In Component (`src/components/ui/clean-minimal-sign-in.jsx`)
- Integrated Firebase email/password authentication
- Added Google Sign-In functionality
- Added password reset functionality
- Form validation and error handling
- Loading states during authentication

#### Registration Component (`src/components/ui/registration.jsx`)
- Full Firebase user registration
- Form validation for all fields
- Google Sign-Up option
- Error handling and loading states
- User profile creation with display name

#### Main App (`src/MainApp.jsx`)
- Authentication state management
- Automatic redirection based on auth status
- Loading spinner during auth checks

#### Chat History (`src/ChatHistory.jsx`)
- User profile display in sidebar
- Logout functionality
- User avatar and name display

### 5. Additional Components
- **File**: `src/components/LoadingSpinner.jsx`
- **Purpose**: Loading indicator during authentication state checks

## Dependencies Added
- `firebase` - Firebase SDK for web applications

## How It Works

1. **App Initialization**: 
   - App wraps with `AuthProvider` in `main.jsx`
   - Firebase monitors authentication state changes

2. **User Flow**:
   - Unauthenticated users see the landing page
   - Can sign in or sign up using email/password or Google
   - Successful authentication redirects to chat interface
   - Users can logout from the sidebar

3. **Authentication States**:
   - **Loading**: Showing spinner while checking auth state
   - **Authenticated**: User is logged in, show chat interface
   - **Unauthenticated**: Show landing/sign-in/sign-up pages

## Google Sign-In Setup

To enable Google Sign-In, you need to:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Navigate to your project
3. Go to Authentication > Sign-in method
4. Enable Google as a sign-in provider
5. Configure OAuth consent screen in Google Cloud Console

## Security Features

- Email/password validation
- Secure Firebase authentication
- Password reset functionality
- Form validation and error handling
- Loading states to prevent duplicate submissions

## Usage Examples

### Sign Up
```javascript
const { user, error } = await signUpWithEmail(email, password, displayName);
```

### Sign In
```javascript
const { user, error } = await signInWithEmail(email, password);
```

### Google Sign In
```javascript
const { user, error } = await signInWithGoogle();
```

### Get Current User
```javascript
const { currentUser, loading } = useAuth();
```

### Logout
```javascript
await logout();
```

## Error Handling

All authentication functions return an object with:
- `user`: The authenticated user object (or null if error)
- `error`: Error message string (or null if successful)

This allows for consistent error handling across all authentication operations.
