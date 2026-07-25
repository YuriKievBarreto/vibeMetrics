const endereco_local = "http://127.0.0.1:8000";
const endereco_frontend = "http://localhost:5501"
const endereco_aws = "edereco aws";

export const endereco_api_em_uso = endereco_local;

// URLs Base da Aplicação
export const HOME_URL = `${endereco_frontend}/frontend/index.html`;
export const LOGIN_URL = `${endereco_api_em_uso}/api/v1/auth/login`;
export const LOGOUT_URL = `${endereco_api_em_uso}/api/v1/user/logout`;

// Endpoints Centralizados da API
export const API_ENDPOINTS = {
  ME: `${endereco_api_em_uso}/api/v1/user/me`,
  USER_BASIC_DATA: `${endereco_api_em_uso}/api/v1/user/get_user_basic_data`,
  TOP_ARTISTS: `${endereco_api_em_uso}/api/v1/user/top_artistas`,
  TOP_TRACKS: `${endereco_api_em_uso}/api/v1/user/top_musicas`,
  PERFIL_MUSICAL: `${endereco_api_em_uso}/api/v1/user/perfil_musical`,
  LOGOUT: LOGOUT_URL
};

// Aliases para exportações diretas
export const API_ARTISTS_URL = API_ENDPOINTS.TOP_ARTISTS;
export const API_TRACKS_URL = API_ENDPOINTS.TOP_TRACKS;
export const API_PERFIL_MUSICAL_URL = API_ENDPOINTS.PERFIL_MUSICAL;

// Mapeamentos e Constantes de Interface
export const RANK_MAP = ['short_rank', 'medium_rank', 'long_rank'];

export const BUTTON_ACTIVE_CLASSES = ['bg-green-500', 'text-black', 'shadow'];
export const BUTTON_INACTIVE_CLASSES = ['text-gray-400', 'hover:text-white'];

export const VIBE_DISPLAY_MAP = {
  'alegria': 'Energia Vibrante',
  'tristeza': 'Melancolia Profunda',
  'raiva': 'Intensidade Explosiva',
  'paz': 'Calmaria e Harmonia',
  'nostalgia': 'Saudosismo Nostálgico',
  'introspeccao': 'Reflexão Introspectiva',
  'melancolia': 'Melancolia Suave',
  'default': 'Vibe Neutra'
};

// Funções Utilitárias Globais
export async function handleLogout() {
  try {
    await fetch(LOGOUT_URL, { method: 'POST', credentials: 'include' });
  } catch (error) {
    console.error("Erro ao fazer logout:", error);
  }
  window.location.href = HOME_URL;
}

export function formatDuration(ms) {
  if (!ms) return '0:00';
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}
