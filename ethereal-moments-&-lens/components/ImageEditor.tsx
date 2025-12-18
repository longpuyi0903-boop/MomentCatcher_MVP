
import React, { useState, useRef } from 'react';
import { GeminiService } from '../services/geminiService';
import { ImageEditState } from '../types';
import { Loader2, Sparkles, Upload, Download, RotateCcw } from 'lucide-react';

export const ImageEditor: React.FC = () => {
  const [state, setState] = useState<ImageEditState>({
    originalUrl: 'https://images.unsplash.com/photo-1475274047050-1d0c0975c63e?q=80&w=2072&auto=format&fit=crop',
    editedUrl: null,
    isProcessing: false,
    error: null
  });
  const [prompt, setPrompt] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const gemini = new GeminiService();

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const base64 = await GeminiService.fileToBase64(file);
      setState(prev => ({ ...prev, originalUrl: base64, editedUrl: null, error: null }));
    }
  };

  const handleEdit = async () => {
    if (!prompt.trim()) return;
    
    setState(prev => ({ ...prev, isProcessing: true, error: null }));
    try {
      const result = await gemini.editImage(state.originalUrl, prompt);
      setState(prev => ({ ...prev, editedUrl: result, isProcessing: false }));
    } catch (err: any) {
      setState(prev => ({ ...prev, isProcessing: false, error: err.message }));
    }
  };

  const reset = () => {
    setState(prev => ({ ...prev, editedUrl: null, error: null }));
    setPrompt('');
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 bg-zinc-900/50 p-8 rounded-2xl border border-white/5">
      <div className="space-y-4">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="text-yellow-400" size={24} />
          AI Image Reimaginer
        </h2>
        <p className="text-zinc-400 text-sm">
          Use the power of Gemini 2.5 Flash Image to transform your space scenes. Try prompts like "Add a retro nebulae glow", "Make it look like a data terminal", or "Enhance the star cluster".
        </p>

        <div className="relative group overflow-hidden rounded-xl bg-black aspect-video border border-white/10">
          <img 
            src={state.editedUrl || state.originalUrl} 
            alt="Workspace" 
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
          {state.isProcessing && (
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center gap-4">
              <Loader2 className="animate-spin text-white" size={48} />
              <p className="text-white font-medium">Gemini is reimagining your vision...</p>
            </div>
          )}
        </div>

        <div className="flex gap-4">
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white py-3 rounded-xl transition-all"
          >
            <Upload size={18} />
            Upload Base Image
          </button>
          {state.editedUrl && (
            <button 
              onClick={reset}
              className="px-4 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 rounded-xl transition-all"
            >
              <RotateCcw size={18} />
            </button>
          )}
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            accept="image/*" 
            className="hidden" 
          />
        </div>
      </div>

      <div className="flex flex-col justify-between space-y-6">
        <div className="space-y-4">
          <label className="text-sm font-medium text-zinc-300">Prompt Instructions</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe how to edit this image (e.g., 'Add a cosmic dust cloud in purple and gold' or 'Change the background to a deep space nebula')"
            className="w-full h-40 bg-black/40 border border-white/10 rounded-xl p-4 text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-yellow-500/50 resize-none transition-all"
          />
          {state.error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-lg">
              {state.error}
            </div>
          )}
        </div>

        <div className="space-y-3">
          <button
            onClick={handleEdit}
            disabled={state.isProcessing || !prompt.trim()}
            className="w-full py-4 bg-gradient-to-r from-yellow-500 to-orange-600 disabled:opacity-30 disabled:grayscale text-white font-bold rounded-xl shadow-lg shadow-orange-500/20 hover:shadow-orange-500/40 transition-all active:scale-[0.98]"
          >
            Generate Edit
          </button>
          <p className="text-[10px] text-zinc-500 text-center uppercase tracking-widest">
            Powered by Gemini 2.5 Flash Image
          </p>
        </div>
      </div>
    </div>
  );
};
