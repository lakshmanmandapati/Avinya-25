// Firebase configuration
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from 'firebase/auth';

// Your Firebase config object
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyCJpV-jzhPYkVXD5Q5iYlq4Zx5iBMbjN34",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "tensora-ai-a9fde.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "tensora-ai-a9fde",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "tensora-ai-a9fde.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "70844209351",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:70844209351:web:a1b2c3d4e5f6g7h8i9j0k1l2"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

// Initialize providers
export const googleProvider = new GoogleAuthProvider();
export const githubProvider = new GithubAuthProvider();

// Configure providers
googleProvider.addScope('email');
googleProvider.addScope('profile');

githubProvider.addScope('user:email');

export default app;
