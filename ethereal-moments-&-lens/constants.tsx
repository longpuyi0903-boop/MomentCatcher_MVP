
import { DesignConfig } from './types';

export const DESIGN_PRESETS: Record<string, DesignConfig> = {
  original: {
    name: "Original View",
    titleFont: "font-serif",
    subtitleFont: "font-serif",
    titleSize: "text-4xl",
    letterSpacing: "tracking-[0.4em]",
    alignment: "text-left",
    opacity: 0.9,
    glow: false,
    position: "top-12 left-12"
  },
  cinematic: {
    name: "Cinematic Modern",
    titleFont: "font-sans font-black",
    subtitleFont: "font-sans font-light",
    titleSize: "text-7xl",
    letterSpacing: "tracking-tight",
    alignment: "text-center",
    opacity: 1,
    glow: true,
    position: "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
  },
  terminal: {
    name: "Tactical Data",
    titleFont: "font-mono font-medium",
    subtitleFont: "font-mono font-light",
    titleSize: "text-2xl",
    letterSpacing: "tracking-widest",
    alignment: "text-right",
    opacity: 0.8,
    glow: true,
    position: "bottom-12 right-12"
  },
  minimalist: {
    name: "Elegant Serif",
    titleFont: "font-serif italic",
    subtitleFont: "font-sans font-extralight",
    titleSize: "text-5xl",
    letterSpacing: "tracking-normal",
    alignment: "text-left",
    opacity: 0.7,
    glow: false,
    position: "top-1/4 left-20"
  }
};

export const PLACEHOLDER_BG = "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&q=80&w=2000";
