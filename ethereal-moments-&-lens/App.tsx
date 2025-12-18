
import React, { useState } from 'react';
import { LayoutShowcase } from './components/LayoutShowcase';
import { ImageEditor } from './components/ImageEditor';
import { Info, Layout, Palette, Image as ImageIcon } from 'lucide-react';

const App: React.FC = () => {
  const [view, setView] = useState<'tips' | 'editor'>('tips');

  return (
    <div className="min-h-screen font-sans selection:bg-yellow-500 selection:text-black">
      {/* Decorative Star Background */}
      <div className="star-bg" />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 p-6 flex justify-between items-center bg-gradient-to-b from-black/80 to-transparent">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center">
            <div className="w-5 h-5 bg-black rounded-sm rotate-45" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight">Celestial Design</h1>
            <p className="text-[10px] text-white/40 uppercase tracking-widest">Aesthetics Studio</p>
          </div>
        </div>
        
        <div className="flex items-center gap-1 bg-white/5 border border-white/10 rounded-full p-1">
          <button 
            onClick={() => setView('tips')}
            className={`flex items-center gap-2 px-5 py-2 rounded-full text-sm font-medium transition-all ${
              view === 'tips' ? 'bg-white text-black' : 'text-white/60 hover:text-white'
            }`}
          >
            <Layout size={16} />
            Layout Tips
          </button>
          <button 
            onClick={() => setView('editor')}
            className={`flex items-center gap-2 px-5 py-2 rounded-full text-sm font-medium transition-all ${
              view === 'editor' ? 'bg-white text-black' : 'text-white/60 hover:text-white'
            }`}
          >
            <ImageIcon size={16} />
            AI Image Editor
          </button>
        </div>
      </nav>

      <main className="pt-32 pb-20 px-6 max-w-7xl mx-auto">
        {view === 'tips' ? (
          <div className="space-y-12 animate-in fade-in duration-700">
            <header className="max-w-2xl">
              <h2 className="text-4xl md:text-5xl font-extrabold mb-4 leading-tight">
                Refining Space-Age <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-200 to-orange-400">Typography.</span>
              </h2>
              <p className="text-zinc-400 text-lg">
                In a vast background like space, the secret to beauty is <span className="text-white">Hierarchy</span> and <span className="text-white">White Space</span>. Explore presets below to see how font choice and position change the "soul" of the same message.
              </p>
            </header>

            <LayoutShowcase />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-zinc-900/40 p-6 rounded-2xl border border-white/5 border-l-yellow-500/50 border-l-4">
                <Palette className="text-yellow-400 mb-4" />
                <h3 className="text-white font-bold mb-2">Visual Weight</h3>
                <p className="text-zinc-500 text-sm leading-relaxed">
                  Avoid making everything the same size. Make the primary title (Flight Logs) significantly larger or bolder than the metadata to create a clear focal point.
                </p>
              </div>
              <div className="bg-zinc-900/40 p-6 rounded-2xl border border-white/5 border-l-blue-500/50 border-l-4">
                <Info className="text-blue-400 mb-4" />
                <h3 className="text-white font-bold mb-2">Kerning & Spacing</h3>
                <p className="text-zinc-500 text-sm leading-relaxed">
                  Wide letter spacing feels "technical" and "airy," perfect for space. Tight tracking feels "modern" and "impactful." Use wide for details, tight for headlines.
                </p>
              </div>
              <div className="bg-zinc-900/40 p-6 rounded-2xl border border-white/5 border-l-purple-500/50 border-l-4">
                <Layout className="text-purple-400 mb-4" />
                <h3 className="text-white font-bold mb-2">Anchor Points</h3>
                <p className="text-zinc-500 text-sm leading-relaxed">
                  Don't just stick to the top left. Try centered layouts for cinematic impact, or bottom-right for a data-entry "HUD" feel that mirrors aircraft controls.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="animate-in slide-in-from-bottom-4 duration-700">
             <ImageEditor />
          </div>
        )}
      </main>

      <footer className="py-10 text-center border-t border-white/5">
        <p className="text-zinc-600 text-xs uppercase tracking-[0.4em]">Designed for Celestial Aesthetics &bull; 2024</p>
      </footer>
    </div>
  );
};

export default App;
