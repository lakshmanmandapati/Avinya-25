import React, { useState } from 'react';
import LandingPage from './LandingPage';
import App from './App';
import SignupForm from './components/ui/registration';
import { SignIn2 } from './components/ui/clean-minimal-sign-in';
import LoadingSpinner from './components/LoadingSpinner';
import { useAuth } from './contexts/AuthContext';

export default function MainApp() {
  const [currentView, setCurrentView] = useState('landing'); // 'landing', 'signup', 'signin', 'chat'
  const { currentUser, loading } = useAuth();

  const handleSignUp = () => {
    setCurrentView('signup');
  };

  const handleSignIn = () => {
    setCurrentView('signin');
  };

  const handleAuthSuccess = () => {
    setCurrentView('chat');
  };

  const handleBackToLanding = () => {
    setCurrentView('landing');
  };

  // Show loading spinner while checking authentication
  if (loading) {
    return <LoadingSpinner />;
  }

  // If user is authenticated, show the chat app
  if (currentUser && (currentView === 'chat' || currentView === 'landing')) {
    return <App />;
  }

  if (currentView === 'signup') {
    return (
      <div className="min-h-screen bg-background">
        <div className="absolute top-4 left-4">
          <button 
            onClick={handleBackToLanding}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            ← Back to Home
          </button>
        </div>
        <SignupForm onSuccess={handleAuthSuccess} onSignIn={() => setCurrentView('signin')} />
      </div>
    );
  }

  if (currentView === 'signin') {
    return (
      <div className="min-h-screen bg-background">
        <div className="absolute top-4 left-4">
          <button 
            onClick={handleBackToLanding}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            ← Back to Home
          </button>
        </div>
        <SignIn2 onSuccess={handleAuthSuccess} onSignUp={() => setCurrentView('signup')} />
      </div>
    );
  }

  return <LandingPage onSignUp={handleSignUp} onSignIn={handleSignIn} />;
}
