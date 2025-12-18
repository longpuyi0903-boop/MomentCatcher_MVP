
import React, { useState } from 'react';
import { UserConfig } from '../types';

interface LandingPageProps {
  onStart: (config: UserConfig) => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onStart }) => {
  const [travelerName, setTravelerName] = useState('');
  const [companionName, setCompanionName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStart({ 
      travelerName: travelerName || 'COOPER', 
      companionName: companionName || 'CASE' 
    });
  };

  return (
    <div className="z-10 w-full max-w-md px-8 flex flex-col items-center">
      {/* Title Section - Reduced size and muted colors for cinematic depth */}
      <div className="mb-24 text-center select-none">
        <h1 className="dreamy-font text-3xl md:text-4xl text-white/60 animate-reveal uppercase leading-tight glow-text-dreamy">
          Moment
        </h1>
        <h1 className="dreamy-font text-3xl md:text-4xl text-white/60 animate-reveal uppercase leading-tight glow-text-dreamy [animation-delay:0.8s]">
          Catcher
        </h1>
        <div className="w-12 h-[0.5px] bg-white/10 mx-auto mt-12 transition-all duration-[4000ms] scale-x-150 animate-pulse"></div>
      </div>

      {/* Form Section */}
      <form onSubmit={handleSubmit} className="w-full space-y-12 animate-[fadeInForm_3s_ease-out]">
        <div className="space-y-4 group">
          <label className="block text-[10px] tracking-[0.3em] text-white/30 mono-font uppercase transition-colors group-focus-within:text-white/70">
            Traveler ID
          </label>
          <input
            type="text"
            value={travelerName}
            onChange={(e) => setTravelerName(e.target.value)}
            placeholder="COOPER"
            className="w-full bg-transparent border-b border-white/10 py-2 text-xl tracking-[0.2em] text-white/80 focus:outline-none focus:border-white/40 transition-all placeholder:text-white/5 dreamy-font italic font-light"
            required
          />
        </div>

        <div className="space-y-4 group">
          <label className="block text-[10px] tracking-[0.3em] text-white/30 mono-font uppercase transition-colors group-focus-within:text-white/70">
            Companion ID
          </label>
          <input
            type="text"
            value={companionName}
            onChange={(e) => setCompanionName(e.target.value)}
            placeholder="TARS / CASE / BRAND"
            className="w-full bg-transparent border-b border-white/10 py-2 text-xl tracking-[0.2em] text-white/80 focus:outline-none focus:border-white/40 transition-all placeholder:text-white/5 dreamy-font italic font-light"
            required
          />
        </div>

        <button
          type="submit"
          className="w-full mt-12 py-5 border border-white/5 bg-white/[0.02] hover:bg-white/[0.06] transition-all group relative overflow-hidden"
        >
          <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-[2000ms]"></div>
          <span className="relative z-10 text-[11px] tracking-[0.7em] text-white/40 mono-font uppercase">
            Initiate Link
          </span>
        </button>
      </form>

      {/* Footer / Aesthetic Details */}
      <div className="mt-20 flex flex-col items-center opacity-20">
        <div className="text-[8px] tracking-[0.2em] mono-font uppercase text-white/60 mb-2">
          Endurance Mission Control // Sector 04
        </div>
        <div className="flex space-x-4">
          <div className="w-1 h-1 bg-white/50 rounded-full animate-pulse"></div>
          <div className="w-1 h-1 bg-white/50 rounded-full animate-pulse delay-75"></div>
          <div className="w-1 h-1 bg-white/50 rounded-full animate-pulse delay-150"></div>
        </div>
      </div>

      <style>{`
        @keyframes fadeInForm {
          from { opacity: 0; transform: translateY(15px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default LandingPage;