
import React, { useState } from 'react';
import { DESIGN_PRESETS } from '../constants';
import { DesignConfig } from '../types';

export const LayoutShowcase: React.FC = () => {
  const [activePreset, setActivePreset] = useState<string>('original');
  const config = DESIGN_PRESETS[activePreset];

  return (
    <div className="relative w-full h-[80vh] bg-black overflow-hidden rounded-2xl shadow-2xl border border-white/10">
      {/* Background Image Layer */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-60 transition-all duration-700"
        style={{ backgroundImage: `url('https://images.unsplash.com/photo-1475274047050-1d0c0975c63e?q=80&w=2072&auto=format&fit=crop')` }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/80" />
      </div>

      {/* Central "Star" elements from user image */}
      <div className="absolute left-1/2 top-2/3 -translate-x-1/2 flex flex-col items-center gap-2">
         <div className="w-4 h-4 rounded-full bg-yellow-400 blur-[2px] shadow-[0_0_15px_#facc15]" />
         <div className="w-3 h-3 rounded-full bg-yellow-400 blur-[1px] shadow-[0_0_10px_#facc15]" />
         <div className="w-2 h-2 rounded-full bg-white blur-[1px] shadow-[0_0_8px_#fff]" />
      </div>

      {/* Dynamic Text Layer */}
      <div className={`absolute transition-all duration-1000 ease-in-out ${config.position} ${config.alignment} max-w-2xl`}>
        <h1 
          className={`
            ${config.titleFont} ${config.titleSize} ${config.letterSpacing} text-white mb-2 uppercase
            ${config.glow ? 'drop-shadow-[0_0_10px_rgba(255,255,255,0.8)]' : ''}
          `}
          style={{ opacity: config.opacity }}
        >
          Flight Logs
        </h1>
        <p 
          className={`
            ${config.subtitleFont} text-white/60 tracking-[0.2em] text-xs uppercase mb-1
          `}
        >
          3 Echoes Captured in Streams
        </p>
        <p 
          className={`
            ${config.subtitleFont} text-white/40 tracking-[0.3em] text-[10px] uppercase
          `}
        >
          Sync to recollect...
        </p>
      </div>

      {/* Preset Controls */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-3 p-2 bg-black/40 backdrop-blur-md rounded-full border border-white/10">
        {Object.entries(DESIGN_PRESETS).map(([key, preset]) => (
          <button
            key={key}
            onClick={() => setActivePreset(key)}
            className={`px-4 py-2 rounded-full text-xs transition-all ${
              activePreset === key 
                ? 'bg-white text-black font-bold scale-105' 
                : 'text-white/60 hover:text-white hover:bg-white/10'
            }`}
          >
            {preset.name}
          </button>
        ))}
      </div>

      <div className="absolute top-6 right-6">
         <div className="w-8 h-8 rounded-full border border-white/20 flex items-center justify-center text-white/40 hover:text-white transition-colors cursor-pointer">
            <span className="text-xs">✕</span>
         </div>
      </div>
    </div>
  );
};
