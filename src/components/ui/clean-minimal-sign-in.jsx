import * as React from "react"
 
import { useState } from "react";

import {LogIn, Lock, Mail} from "lucide-react";
import { signInWithEmail, signInWithGoogle, signInWithGithub, resetPassword } from "../../firebase/auth.js";
 
const SignIn2 = ({ onSuccess, onSignUp }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resetEmailSent, setResetEmailSent] = useState(false);

  const validateEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleSignIn = async () => {
    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }

    if (!validateEmail(email)) {
      setError("Please enter a valid email address");
      return;
    }

    setLoading(true);
    setError("");

    const { user, error: authError } = await signInWithEmail(email, password);
    
    if (authError) {
      setError(authError);
    } else {
      onSuccess && onSuccess();
    }

    setLoading(false);
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError("");

    const { user, error: authError } = await signInWithGoogle();
    
    if (authError) {
      setError(authError);
    } else {
      onSuccess && onSuccess();
    }

    setLoading(false);
  };

  const handleGithubSignIn = async () => {
    setLoading(true);
    setError("");

    const { user, error: authError } = await signInWithGithub();
    
    if (authError) {
      setError(authError);
    } else {
      onSuccess && onSuccess();
    }

    setLoading(false);
  };

  const handleForgotPassword = async () => {
    if (!email) {
      setError("Please enter your email address first");
      return;
    }

    if (!validateEmail(email)) {
      setError("Please enter a valid email address");
      return;
    }

    const { error: resetError } = await resetPassword(email);
    
    if (resetError) {
      setError(resetError);
    } else {
      setResetEmailSent(true);
      setError("");
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleSignIn();
    }
  };
 
  return (
    <div
      className="min-h-screen w-full flex items-center justify-center bg-white rounded-xl  z-1">
      <div
        className="w-full max-w-sm bg-gradient-to-b from-sky-50/50 to-white  rounded-3xl shadow-xl shadow-opacity-10 p-8 flex flex-col items-center border border-blue-100 text-black">
        <div
          className="flex items-center justify-center w-14 h-14 rounded-2xl bg-white mb-6 shadow-lg shadow-opacity-5">
          <LogIn className="w-7 h-7 text-black" />
        </div>
        <h2 className="text-2xl font-semibold mb-2 text-center">
          Welcome back to Tensora Ai
        </h2>
        <p className="text-gray-500 text-sm mb-6 text-center">
          Continue your AI-powered journey across all your connected tools
        </p>
        
        {resetEmailSent && (
          <div className="w-full mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-800 text-sm text-center">
              Password reset email sent! Check your inbox.
            </p>
          </div>
        )}

        <div className="w-full flex flex-col gap-3 mb-2">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              <Mail className="w-4 h-4" />
            </span>
            <input
              placeholder="Email"
              type="email"
              value={email}
              className="w-full pl-10 pr-3 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-200 bg-gray-50 text-black text-sm"
              onChange={(e) => setEmail(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading} />
          </div>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              <Lock className="w-4 h-4" />
            </span>
            <input
              placeholder="Password"
              type="password"
              value={password}
              className="w-full pl-10 pr-10 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-200 bg-gray-50 text-black text-sm"
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading} />
            <span
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 cursor-pointer text-xs select-none"></span>
          </div>
          <div className="w-full flex justify-between items-center">
            {error && (
              <div className="text-sm text-red-500 text-left flex-1">{error}</div>
            )}
            <button 
              onClick={handleForgotPassword}
              className="text-xs hover:underline font-medium text-blue-600 ml-auto"
              disabled={loading}>
              Forgot password?
            </button>
          </div>
        </div>
        <button
          onClick={handleSignIn}
          disabled={loading}
          className="w-full bg-gradient-to-b from-gray-700 to-gray-900 text-white font-medium py-2 rounded-xl shadow hover:brightness-105 cursor-pointer transition mb-4 mt-2 disabled:opacity-50 disabled:cursor-not-allowed">
          {loading ? "Signing In..." : "Get Started"}
        </button>
        <div className="flex items-center w-full my-2">
          <div className="flex-grow border-t border-dashed border-gray-200"></div>
          <span className="mx-2 text-xs text-gray-400">Or sign in with</span>
          <div className="flex-grow border-t border-dashed border-gray-200"></div>
        </div>
        <div className="flex gap-3 w-full justify-center mt-2">
          <button
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="flex items-center justify-center w-12 h-12 rounded-xl border bg-white hover:bg-gray-100 transition grow disabled:opacity-50 disabled:cursor-not-allowed">
            <img
              src="https://www.svgrepo.com/show/475656/google-color.svg"
              alt="Google"
              className="w-6 h-6" />
          </button>
          <button
            className="flex items-center justify-center w-12 h-12 rounded-xl border bg-white hover:bg-gray-100 transition grow">
            <img
              src="https://www.svgrepo.com/show/448224/facebook.svg"
              alt="Facebook"
              className="w-6 h-6" />
          </button>
          <button
            onClick={handleGithubSignIn}
            disabled={loading}
            className="flex items-center justify-center w-12 h-12 rounded-xl border bg-white hover:bg-gray-100 transition grow disabled:opacity-50 disabled:cursor-not-allowed">
            <img
              src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
              alt="GitHub"
              className="w-6 h-6" />
          </button>
        </div>
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-500">
            Don't have an account?{" "}
            <button 
              onClick={onSignUp} 
              className="text-blue-600 hover:underline font-medium"
              disabled={loading}>
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};
 
export { SignIn2 };