import React from 'react';
import { Hero1 } from './components/ui/hero-with-text-and-two-button';
import { BrandScroller } from './components/ui/brand-scoller';
import { Component as BgGradient } from './components/ui/bg-gredient';
import ZapierEmbed from './components/ZapierEmbed'; // <-- Add this import

export default function LandingPage({ onSignUp, onSignIn }) {
  return (
    <div 
      className="min-h-screen relative" 
      style={{background: 'radial-gradient(125% 125% at 50% 10%, #fff 40%, #6366f1 100%)'}}
    >
      {/* Hero Section */}
      <Hero1 onSignUp={onSignUp} onSignIn={onSignIn} />

      {/* Zapier Section */}
      <div className="mt-12 p-6">
        <h2 className="text-2xl font-bold text-center mb-6">
          Connect Your Tools with Zapier
        </h2>
        
        {/* Example Zap Templates */}
        <div className="flex flex-col items-center gap-6">
          <ZapierEmbed zapId="12345" title="Send Signups to Google Sheets" />
          <ZapierEmbed zapId="67890" title="Get Slack Alerts for New Events" />
        </div>
      </div>
    </div>
  );
}
