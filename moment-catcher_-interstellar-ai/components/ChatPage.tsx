
import React, { useState, useEffect, useRef } from 'react';
import { GoogleGenAI, LiveServerMessage, Modality } from '@google/genai';
import { UserConfig, Message, PlanetData } from '../types';
import ParticleOrb from './ParticleOrb';
import { PLANETS } from './PlanetSelection';

interface ChatPageProps {
  config: UserConfig;
  onUpdateConfig?: (config: Partial<UserConfig>) => void;
}

interface MomentLog {
  id: string;
  title: string;
  content: string;
  date: string;
  moodColor: string;
}

// Audio Utilities for Live API
function encode(bytes: Uint8Array) {
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function decode(base64: string) {
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
  return bytes;
}

async function decodeAudioData(data: Uint8Array, ctx: AudioContext, sampleRate: number): Promise<AudioBuffer> {
  const dataInt16 = new Int16Array(data.buffer);
  const buffer = ctx.createBuffer(1, dataInt16.length, sampleRate);
  const channelData = buffer.getChannelData(0);
  for (let i = 0; i < dataInt16.length; i++) channelData[i] = dataInt16[i] / 32768.0;
  return buffer;
}

const ChatPage: React.FC<ChatPageProps> = ({ config, onUpdateConfig }) => {
  const [status, setStatus] = useState('STANDBY');
  const [isListening, setIsListening] = useState(false);
  const [showMemories, setShowMemories] = useState(false);
  const [showCaptureConfirm, setShowCaptureConfirm] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [activeMoment, setActiveMoment] = useState<MomentLog | null>(null);
  
  const [userTranscription, setUserTranscription] = useState("");
  const [modelTranscription, setModelTranscription] = useState("");
  
  const [tempCompanion, setTempCompanion] = useState(config.companionName);
  const [tempTraveler, setTempTraveler] = useState(config.travelerName);

  const audioContextRef = useRef<AudioContext | null>(null);
  const sessionRef = useRef<any>(null);
  const nextStartTimeRef = useRef(0);
  const sourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());

  useEffect(() => {
    setModelTranscription(`Establishing link on ${config.selectedPlanet?.name}. I am ${config.companionName}. Ready to log.`);
    setTempCompanion(config.companionName);
    setTempTraveler(config.travelerName);
  }, [config]);

  const toggleVoiceSession = async () => {
    if (isListening) {
      sessionRef.current?.close();
      setIsListening(false);
      setStatus('STANDBY');
      return;
    }

    try {
      setStatus('INITIATING...');
      const ai = new GoogleGenAI({ apiKey: (process.env as any).API_KEY });
      
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
      }
      const outCtx = audioContextRef.current;
      const inCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const sessionPromise = ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-09-2025',
        config: {
          responseModalities: [Modality.AUDIO],
          inputAudioTranscription: {},
          outputAudioTranscription: {},
          systemInstruction: `You are ${config.companionName}, a supportive AI inspired by Interstellar. You are talking to ${config.travelerName} on ${config.selectedPlanet?.name}. Be poetic, calm, and insightful. Keep responses relatively concise for voice flow.`,
          speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Puck' } } }
        },
        callbacks: {
          onopen: () => {
            setIsListening(true);
            setStatus('ACTIVE_LINK');
            const source = inCtx.createMediaStreamSource(stream);
            const processor = inCtx.createScriptProcessor(4096, 1, 1);
            processor.onaudioprocess = (e) => {
              const inputData = e.inputBuffer.getChannelData(0);
              const int16 = new Int16Array(inputData.length);
              for (let i = 0; i < inputData.length; i++) int16[i] = inputData[i] * 32768;
              sessionPromise.then(s => s.sendRealtimeInput({ 
                media: { data: encode(new Uint8Array(int16.buffer)), mimeType: 'audio/pcm;rate=16000' } 
              }));
            };
            source.connect(processor);
            processor.connect(inCtx.destination);
          },
          onmessage: async (msg: LiveServerMessage) => {
            if (msg.serverContent?.inputTranscription) setUserTranscription(msg.serverContent.inputTranscription.text);
            if (msg.serverContent?.outputTranscription) setModelTranscription(msg.serverContent.outputTranscription.text);
            if (msg.serverContent?.modelTurn?.parts?.[0]?.inlineData?.data) {
              const audioData = decode(msg.serverContent.modelTurn.parts[0].inlineData.data);
              nextStartTimeRef.current = Math.max(nextStartTimeRef.current, outCtx.currentTime);
              const buffer = await decodeAudioData(audioData, outCtx, 24000);
              const source = outCtx.createBufferSource();
              source.buffer = buffer;
              source.connect(outCtx.destination);
              source.start(nextStartTimeRef.current);
              nextStartTimeRef.current += buffer.duration;
              sourcesRef.current.add(source);
              source.onended = () => sourcesRef.current.delete(source);
            }
          }
        }
      });
      sessionRef.current = await sessionPromise;
    } catch (err) { setStatus('ERROR'); }
  };

  const handleCrystallize = () => {
    const moods = ['#a855f7', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
    const newMoment = {
      id: Math.random().toString(36).substr(2, 6).toUpperCase(),
      title: "Fragment Capture",
      content: modelTranscription || "Establishing silence in the vacuum of space...",
      date: new Date().toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '.'),
      moodColor: moods[Math.floor(Math.random() * moods.length)]
    };
    
    // Set active moment first then close the confirm dialog to ensure the card jumps out correctly
    setActiveMoment(newMoment);
    setShowCaptureConfirm(false);
  };

  const saveSettings = () => {
    if (onUpdateConfig) {
      onUpdateConfig({
        travelerName: tempTraveler.toUpperCase(),
        companionName: tempCompanion.toUpperCase()
      });
    }
    setShowSettings(false);
  };

  const resetSettings = () => {
    setTempTraveler('COOPER');
    setTempCompanion('CASE');
  };

  const downloadMoment = (moment?: MomentLog) => {
    const target = moment || activeMoment;
    if (!target) return;
    const logText = `[ENDURANCE LOG #${target.id}]\nDATE: ${target.date}\nSTATION: ${config.selectedPlanet?.id.toUpperCase()}\n--------------------\n"${target.content}"\n--------------------`;
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `LOG_${target.id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const triggerImageDownload = async (imageUrl: string, filename: string) => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename.replace(/\s+/g, '_').toUpperCase()}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed', error);
      window.open(imageUrl, '_blank');
    }
  };

  return (
    <div className="z-10 w-full h-full flex flex-col items-center justify-between pb-16 pt-12 px-6 animate-[fadeInChat_3s_ease-out] relative">
      
      {/* Top Status Bar & Settings Trigger */}
      <div className="z-20 w-full flex items-center justify-between px-6">
        <div className="flex-1"></div>
        <div className="px-4 py-1.5 border border-white/5 rounded-full bg-black/40 backdrop-blur-md flex items-center space-x-3">
           <div className={`w-1.5 h-1.5 rounded-full ${isListening ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse' : 'bg-white/10'}`}></div>
           <span className="text-[8px] tracking-[0.6em] mono-font text-white/40 uppercase font-bold">STATION: {config.selectedPlanet?.id.toUpperCase()} // {status}</span>
        </div>
        <div className="flex-1 flex justify-end">
          <button 
            onClick={() => setShowSettings(true)}
            className="w-10 h-10 rounded-full border border-white/10 bg-white/[0.03] flex items-center justify-center hover:bg-white/[0.1] hover:border-white/20 transition-all opacity-40 hover:opacity-100 group shadow-lg"
          >
            <svg className="w-4 h-4 text-white/60 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Center Visualizer Area */}
      <div className="relative w-full flex-grow flex items-center justify-center -mt-10 overflow-visible">
        <div className="w-[80vh] aspect-square opacity-80 pointer-events-none">
          <ParticleOrb active={isListening} imageUrl={config.selectedPlanet?.imageUrl} />
        </div>
        
        <div className="absolute inset-x-0 bottom-[18%] flex flex-col items-center justify-center pointer-events-none px-6 z-30 space-y-6">
          {modelTranscription && (
            <div className="max-w-3xl px-10 py-6 bg-black/40 backdrop-blur-md border border-white/5 rounded-3xl text-center shadow-[0_0_50px_rgba(0,0,0,0.5)] animate-[slideUp_0.8s_ease-out]">
              <p className="text-white/95 text-base md:text-xl font-light tracking-[0.05em] leading-relaxed dreamy-font italic glow-text-dreamy">
                {modelTranscription}
              </p>
            </div>
          )}
          {userTranscription && (
            <div className="max-w-xl px-6 py-2 bg-white/[0.02] border border-white/5 rounded-full text-center opacity-40 animate-[fadeIn_0.5s_ease-out]">
              <p className="text-white/80 text-[10px] tracking-[0.2em] mono-font uppercase italic">
                {userTranscription}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Control Bar - Bottom */}
      <div className="w-full max-w-2xl flex items-center justify-between px-10 z-40">
        <button onClick={() => setShowMemories(true)} className="w-12 h-12 rounded-full border border-white/5 bg-white/[0.01] flex items-center justify-center group opacity-30 hover:opacity-100 transition-all">
          <svg className="w-4 h-4 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 6h16M4 12h16m-7 6h7" /></svg>
        </button>

        <button onClick={toggleVoiceSession} className={`w-24 h-24 rounded-full border transition-all duration-700 flex items-center justify-center relative ${isListening ? 'border-white/30 bg-white/5 scale-110' : 'border-white/5 bg-white/[0.01]'}`}>
          <div className={`w-12 h-12 rounded-full border border-white/10 flex items-center justify-center ${isListening ? 'bg-white shadow-[0_0_15px_white]' : ''}`}>
             <div className={`w-2 h-2 rounded-full ${isListening ? 'bg-black' : 'bg-white/20'}`}></div>
          </div>
        </button>

        <button 
          onClick={() => setShowCaptureConfirm(true)}
          className="h-12 px-8 border border-white/10 rounded-full bg-white/[0.02] hover:bg-white/[0.08] transition-all flex items-center space-x-4 group shadow-2xl relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-[1500ms]"></div>
          <span className="text-[9px] tracking-[0.5em] mono-font text-white/40 uppercase group-hover:text-white">Capture</span>
          <svg className="w-3 h-3 text-white/20 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        </button>
      </div>

      {/* REFINED SYSTEM CONFIGURATION DIALOG - INTERSTELLAR AESTHETIC */}
      {showSettings && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center bg-black/75 backdrop-blur-md animate-[fadeIn_0.3s_ease-out]">
           <div className="w-[420px] bg-[#0d0d0d] border border-white/10 shadow-[0_0_60px_rgba(0,0,0,1)] relative rounded-sm p-[1px]">
              <div className="relative p-12 z-10 bg-[#080808] rounded-sm">
                
                <button 
                  onClick={() => setShowSettings(false)}
                  className="absolute top-8 right-8 text-white/20 hover:text-white transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>

                <div className="text-center mb-16">
                   <h3 className="mono-font text-[14px] tracking-[0.4em] text-white/40 uppercase font-bold">
                      SYSTEM CONFIGURATION
                   </h3>
                </div>

                <div className="space-y-12 mb-16 px-2">
                  <div className="flex items-center justify-between">
                    <label className="mono-font text-[9px] tracking-[0.2em] text-white/25 uppercase">COMPANION</label>
                    <div className="w-3/5 relative">
                      <input 
                        type="text" 
                        value={tempCompanion}
                        onChange={(e) => setTempCompanion(e.target.value)}
                        className="w-full bg-transparent text-right py-1 text-2xl text-[#cbd5e1] focus:outline-none mono-font italic pr-2 placeholder:text-white/5"
                        placeholder="N/A"
                      />
                      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-white/20"></div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="mono-font text-[9px] tracking-[0.2em] text-white/25 uppercase">TRAVELER</label>
                    <div className="w-3/5 relative">
                      <input 
                        type="text" 
                        value={tempTraveler}
                        onChange={(e) => setTempTraveler(e.target.value)}
                        className="w-full bg-transparent text-right py-1 text-2xl text-[#94a3b8] focus:outline-none mono-font italic pr-2 placeholder:text-white/5"
                        placeholder="N/A"
                      />
                      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-white/20"></div>
                    </div>
                  </div>
                </div>
                
                <div className="flex space-x-4">
                   <button 
                     onClick={resetSettings} 
                     className="flex-1 py-4 bg-white/[0.02] border border-white/5 hover:bg-white/[0.08] transition-all text-white/50 mono-font text-[10px] tracking-[0.2em] uppercase rounded-sm"
                   >
                      Reset Core
                   </button>
                   <button 
                     onClick={saveSettings} 
                     className="flex-1 py-4 bg-[#451a03]/40 border border-[#b45309]/20 hover:bg-[#451a03]/60 transition-all text-[#fcd34d]/70 mono-font text-[10px] tracking-[0.2em] uppercase font-bold rounded-sm shadow-lg"
                   >
                      Commit
                   </button>
                </div>
                <div className="mt-8 text-center opacity-10">
                   <span className="mono-font text-[6px] tracking-[0.3em] uppercase">Endurance Mission Control // Sector 04</span>
                </div>
              </div>
           </div>
        </div>
      )}

      {/* Capture Confirmation Dialog */}
      {showCaptureConfirm && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 backdrop-blur-xl animate-[fadeIn_0.3s_ease-out]">
           <div className="w-[450px] bg-black/50 border border-white/10 shadow-[0_0_150px_rgba(0,0,0,0.5)] relative overflow-hidden group p-[1px]">
              <div className="relative p-16 z-10">
                <div className="text-center mb-10">
                   <div className="text-[7px] tracking-[0.8em] mono-font text-white/30 uppercase mb-6 font-bold">
                      // AUTHORIZING QUANTUM INTERLOCK
                   </div>
                   <h3 className="dreamy-font text-3xl text-white/90 tracking-[0.4em] font-light italic leading-tight">
                     Freeze this moment?
                   </h3>
                </div>
                <div className="flex flex-col space-y-4">
                   <button onClick={handleCrystallize} className="w-full py-5 bg-white/[0.03] border border-white/10 hover:border-white/40 hover:bg-white/[0.08] transition-all text-white/80 mono-font text-[10px] tracking-[0.8em] uppercase font-bold shadow-[0_0_20px_rgba(255,255,255,0.05)]">
                      Crystallize
                   </button>
                   <button onClick={() => setShowCaptureConfirm(false)} className="w-full py-5 border border-white/10 bg-white/[0.02] hover:bg-white/[0.05] transition-all text-white/40 mono-font text-[10px] tracking-[0.8em] uppercase">
                      Fade
                   </button>
                </div>
              </div>
           </div>
        </div>
      )}

      {/* Moment Details Card - Redesigned to match screenshot layout with sci-fi aesthetic */}
      {activeMoment && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center bg-black/70 backdrop-blur-3xl animate-[fadeIn_0.5s_ease-out]">
           <div className="w-full max-w-xl bg-[#0f0f11] shadow-[0_0_80px_rgba(0,0,0,0.9)] relative overflow-hidden mx-6 rounded-md border border-white/5">
              {/* Vertical Accent Bar */}
              <div className="absolute left-0 top-4 bottom-4 w-[3px] bg-purple-500/60 rounded-r-full shadow-[0_0_10px_rgba(168,85,247,0.4)]"></div>
              
              <div className="p-10 md:p-14 relative">
                {/* Close Button Top Right */}
                <button 
                  onClick={() => setActiveMoment(null)} 
                  className="absolute top-8 right-8 text-white/20 hover:text-white transition-all z-20"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>

                {/* Header Row: Title & Date */}
                <div className="flex flex-col md:flex-row md:items-start justify-between mb-6">
                  <h2 className="dreamy-font text-3xl md:text-4xl text-white/90 uppercase italic leading-tight glow-text-dreamy mb-2 md:mb-0 max-w-[70%]">
                    {activeMoment.title}
                  </h2>
                  <div className="mono-font text-[11px] tracking-[0.2em] text-white/30 uppercase mt-2">
                    {activeMoment.date}
                  </div>
                </div>

                {/* Separator line */}
                <div className="w-full h-[1px] bg-white/5 mb-10"></div>

                {/* Main Content */}
                <div className="relative">
                  <p className="dreamy-font text-xl md:text-2xl text-white/80 italic leading-[1.8] font-light">
                    "{activeMoment.content}"
                  </p>
                </div>

                {/* Footer Data Tags */}
                <div className="mt-16 pt-6 border-t border-white/[0.03] flex justify-between items-center opacity-30">
                  <div className="mono-font text-[8px] tracking-[0.3em] uppercase font-bold">STATION_{config.selectedPlanet?.id.toUpperCase()}</div>
                  <div className="mono-font text-[8px] tracking-[0.3em] uppercase">LOG_REF_{activeMoment.id}</div>
                  <button onClick={() => downloadMoment()} className="hover:text-white transition-colors">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                  </button>
                </div>
              </div>
           </div>
        </div>
      )}

      {/* Archive Gallery Modal - WITH PNG DOWNLOAD BUTTONS */}
      {showMemories && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/98 backdrop-blur-2xl animate-[fadeIn_0.4s_ease-out] p-8 md:p-12 overflow-y-auto no-scrollbar">
          <div className="w-full max-w-5xl">
            <button onClick={() => setShowMemories(false)} className="fixed top-8 right-8 z-[110] p-4 text-white/40 hover:text-white border border-white/10 rounded-full px-8 bg-black/40 uppercase mono-font text-[10px] tracking-[0.4em]">Close Archive</button>
            <div className="text-center mb-16 mt-8">
              <h2 className="dreamy-font text-3xl tracking-[0.6em] text-white/50 uppercase font-light italic">Memory Archive</h2>
              <p className="mono-font text-[8px] text-white/20 tracking-[0.3em] mt-4 uppercase font-bold">// SECURE STORAGE FRAGMENTS</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 pb-32">
              {PLANETS.map((planet) => (
                <div key={planet.id} className="relative aspect-[16/10] border border-white/5 overflow-hidden group transition-all rounded-sm bg-black/20">
                  <img src={planet.imageUrl} className="w-full h-full object-cover grayscale opacity-20 group-hover:opacity-100 group-hover:grayscale-0 transition-all duration-[1.5s]" alt={planet.name} />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/30 to-transparent"></div>
                  
                  {/* Download Button Overlay */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500 z-20">
                     <button 
                       onClick={(e) => {
                         e.stopPropagation();
                         triggerImageDownload(planet.imageUrl, planet.name);
                       }}
                       className="bg-black/60 backdrop-blur-md border border-white/20 px-5 py-2.5 rounded-full text-[9px] tracking-[0.4em] uppercase hover:bg-white hover:text-black transition-all mono-font flex items-center space-x-3 shadow-2xl"
                     >
                       <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                       <span>Export PNG</span>
                     </button>
                  </div>

                  <div className="absolute bottom-6 left-6 right-6 pointer-events-none">
                    <div className="mono-font text-[7px] tracking-[0.4em] text-white/20 mb-1.5 uppercase italic">LOG: #{planet.id.toUpperCase()}</div>
                    <div className="dreamy-font text-lg tracking-[0.15em] text-white/70 uppercase font-extralight italic">{planet.name}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Existing styling for animations */}
      <style>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(40px) scale(0.98); filter: blur(15px); }
          to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0px); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
    </div>
  );
};

export default ChatPage;
