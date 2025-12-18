
export enum AppState {
  LANDING = 'LANDING',
  PLANET_SELECTION = 'PLANET_SELECTION',
  INITIATING = 'INITIATING',
  CONNECTED = 'CONNECTED'
}

export interface UserConfig {
  travelerName: string;
  companionName: string;
  selectedPlanet?: PlanetData;
}

export interface PlanetData {
  id: string;
  name: string;
  description: string;
  color: string;
  imageUrl: string;
}

export interface Message {
  role: 'user' | 'model';
  text: string;
}
