
import React, { useState, useCallback } from 'react';
import { AppState, UserConfig, PlanetData } from './types';
import LandingPage from './components/LandingPage';
import ChatPage from './components/ChatPage';
import PlanetSelection from './components/PlanetSelection';
import StarBackground from './components/StarBackground';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppState>(AppState.LANDING);
  const [config, setConfig] = useState<UserConfig>({
    travelerName: '',
    companionName: ''
  });

  const handleLandingStart = useCallback((basicInfo: UserConfig) => {
    setConfig(prev => ({ ...prev, ...basicInfo }));
    setCurrentView(AppState.PLANET_SELECTION);
  }, []);

  const handlePlanetSelect = useCallback((planet: PlanetData) => {
    setConfig(prev => ({ ...prev, selectedPlanet: planet }));
    setCurrentView(AppState.INITIATING);
    
    setTimeout(() => {
      setCurrentView(AppState.CONNECTED);
    }, 2500);
  }, []);

  const handleUpdateConfig = useCallback((newConfig: Partial<UserConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  }, []);

  return (
    <div className="relative w-full h-screen bg-black overflow-hidden flex flex-col items-center justify-center">
      <StarBackground fast={currentView === AppState.INITIATING} />
      
      {currentView === AppState.LANDING && (
        <LandingPage onStart={handleLandingStart} />
      )}

      {currentView === AppState.PLANET_SELECTION && (
        <PlanetSelection onSelect={handlePlanetSelect} />
      )}

      {currentView === AppState.INITIATING && (
        <div className="z-20 text-center">
          <h2 className="text-white/60 mono-font tracking-[0.8em] text-[10px] mb-6 animate-pulse uppercase">
            Initiating Quantum Jump to {config.selectedPlanet?.name}
          </h2>
          <div className="w-48 h-[0.5px] bg-white/10 mx-auto relative overflow-hidden">
             <div className="absolute inset-0 bg-white/40 w-full animate-[warp_1.5s_infinite]" style={{ transform: 'translateX(-100%)' }}></div>
          </div>
          <style>{`
            @keyframes warp {
              0% { transform: translateX(-100%); }
              100% { transform: translateX(100%); }
            }
          `}</style>
        </div>
      )}

      {currentView === AppState.CONNECTED && (
        <ChatPage config={config} onUpdateConfig={handleUpdateConfig} />
      )}
    </div>
  );
};

export default App;
