
export type LayoutPreset = 'original' | 'cinematic' | 'terminal' | 'minimalist' | 'dynamic';

export interface DesignConfig {
  name: string;
  titleFont: string;
  subtitleFont: string;
  titleSize: string;
  letterSpacing: string;
  alignment: string;
  opacity: number;
  glow: boolean;
  position: string;
}

export interface ImageEditState {
  originalUrl: string;
  editedUrl: string | null;
  isProcessing: boolean;
  error: string | null;
}
