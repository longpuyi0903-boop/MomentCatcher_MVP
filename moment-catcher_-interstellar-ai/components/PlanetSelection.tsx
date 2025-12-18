
import React, { useState } from 'react';
import { PlanetData } from '../types';

interface PlanetSelectionProps {
  onSelect: (planet: PlanetData) => void;
}

export const PLANETS: PlanetData[] = [
  { id: 'miller', name: 'MILLER', description: 'Gravitational Time Dilation: High', color: '#6fb3b8', imageUrl: 'https://images.unsplash.com/photo-1506318137071-a8e063b4bcc0?auto=format&fit=crop&q=80&w=1200' },
  { id: 'venus', name: 'VENUS', description: 'Atmospheric Greenhouse Effect', color: '#ffcc33', imageUrl: 'https://images.unsplash.com/photo-1614314107768-6018061b5b72?auto=format&fit=crop&q=80&w=1200' },
  { id: 'saturn', name: 'SATURN', description: 'The Gateway To Another Galaxy', color: '#e3c6a1', imageUrl: 'https://images.unsplash.com/photo-1614732414444-096e5f1122d5?auto=format&fit=crop&q=80&w=1200' },
  { id: 'mann', name: 'MANN', description: 'Frozen Cloud Formations', color: '#d1d1d1', imageUrl: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&q=80&w=1200' },
  { id: 'edmunds', name: 'EDMUNDS', description: 'Habitable Zone Potential', color: '#b59a7d', imageUrl: 'https://images.unsplash.com/photo-1446941611757-91d2c3bd3d45?auto=format&fit=crop&q=80&w=1200' },
  { id: 'gargantua', name: 'GARGANTUA', description: 'Singularity Event Horizon', color: '#ffffff', imageUrl: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&q=80&w=1200' },
  { id: 'kepler', name: 'KEPLER-186F', description: 'Earth Like Atmosphere Found', color: '#88a070', imageUrl: 'https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?auto=format&fit=crop&q=80&w=1200' },
  { id: 'jupiter', name: 'JUPITER', description: 'Great Red Spot Cyclonic Storm', color: '#e0ae8a', imageUrl: 'https://images.unsplash.com/photo-1630839437035-dac17da580d0?auto=format&fit=crop&q=80&w=1200' },
  { id: 'uranus', name: 'URANUS', description: 'The Tilted Ice Giant', color: '#afeeee', imageUrl: 'https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3?auto=format&fit=crop&q=80&w=1200' },
  { id: 'neptune', name: 'NEPTUNE', description: 'Supersonic Winds of Methane', color: '#4b70dd', imageUrl: 'https://images.unsplash.com/photo-1454789548928-9efd52dc4031?auto=format&fit=crop&q=80&w=1200' },
];

const PlanetSelection: React.FC<PlanetSelectionProps> = ({ onSelect }) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const next = () => setActiveIndex((prev) => (prev + 1) % PLANETS.length);
  const prev = () => setActiveIndex((prev) => (prev - 1 + PLANETS.length) % PLANETS.length);

  return (
    <div className="z-20 w-full h-full flex flex-col items-center justify-center animate-[fadeIn_2s_ease-out]">
      <div className="mb-12 text-center">
        <h2 className="dreamy-font text-xs tracking-[0.8em] text-white/40 uppercase mb-2">Quantum Library</h2>
        <h1 className="dreamy-font text-2xl tracking-[0.4em] text-white/80 uppercase glow-text-dreamy">Select Your Destination</h1>
      </div>

      <div className="relative w-full max-w-4xl h-[450px] flex items-center justify-center perspective-[1200px]">
        {PLANETS.map((planet, index) => {
          const offset = index - activeIndex;
          const isCenter = offset === 0;
          const absOffset = Math.abs(offset);
          
          const rotateY = offset * 25.7; 
          const translateZ = isCenter ? 150 : -200 - absOffset * 80;
          const opacity = isCenter ? 1 : Math.max(0.05, 0.25 - absOffset * 0.05);
          const scale = isCenter ? 1 : 0.8;

          if (absOffset > 4) return null; 

          return (
            <div
              key={planet.id}
              onClick={() => isCenter && onSelect(planet)}
              className="absolute w-[300px] md:w-[450px] aspect-video transition-all duration-1000 ease-out cursor-pointer group"
              style={{
                transform: `rotateY(${rotateY}deg) translateZ(${translateZ}px) scale(${scale})`,
                opacity: opacity,
                filter: isCenter ? 'blur(0px)' : 'blur(4px)',
                zIndex: 10 - absOffset
              }}
            >
              <div className={`relative w-full h-full rounded-sm overflow-hidden border border-white/10 transition-all duration-700 ${isCenter ? 'border-white/30 shadow-[0_0_50px_rgba(255,255,255,0.05)]' : ''}`}>
                <img src={planet.imageUrl} className="w-full h-full object-cover grayscale opacity-60 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-1000" alt={planet.name} />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-80"></div>
                
                <div className={`absolute bottom-6 left-8 transition-all duration-700 ${isCenter ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`}>
                   <div className="mono-font text-[8px] tracking-[0.4em] text-white/40 mb-1">// {planet.id.toUpperCase()}</div>
                   <div className="dreamy-font text-xl tracking-[0.3em] text-white/90">{planet.name}</div>
                   <div className="mono-font text-[7px] tracking-[0.2em] text-white/30 mt-2">{planet.description}</div>
                </div>
              </div>
            </div>
          );
        })}

        <button onClick={prev} className="absolute left-4 z-30 p-4 text-white/20 hover:text-white/60 transition-colors">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={0.5} d="M15 19l-7-7 7-7" /></svg>
        </button>
        <button onClick={next} className="absolute right-4 z-30 p-4 text-white/20 hover:text-white/60 transition-colors">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={0.5} d="M9 5l7 7-7 7" /></svg>
        </button>
      </div>

      <div className="mt-12 flex space-x-2">
        {PLANETS.map((_, i) => (
          <div key={i} className={`h-[1px] transition-all duration-700 ${i === activeIndex ? 'w-6 bg-white/60' : 'w-1 bg-white/10'}`}></div>
        ))}
      </div>

      <div className="mt-8 mono-font text-[7px] tracking-[0.5em] text-white/20 animate-pulse uppercase">
        Identify fragment to initialize link
      </div>
    </div>
  );
};

export default PlanetSelection;
