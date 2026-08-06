const isLocalhost = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
const currentHost = isLocalhost ? window.location.hostname : '127.0.0.1';

const endereco_local = `http://${currentHost}:8000`;
export const endereco_prod = 'https://vibemetrics-rybg.onrender.com';
export const endereco_frontend = isLocalhost ? `http://${currentHost}:5501` : `${window.location.origin}/vibeMetrics`;

export const endereco_api_em_uso = isLocalhost ? endereco_local : endereco_prod;

// URLs Base da Aplicação
export const HOME_URL = `${endereco_frontend}/frontend/index.html`;
export const LOGIN_URL = `${endereco_api_em_uso}/api/v1/auth/login`;
export const LOGOUT_URL = `${endereco_api_em_uso}/api/v1/user/logout`;

// Endpoints Centralizados da API
export const API_ENDPOINTS = {
  USER_BASIC_DATA: `${endereco_api_em_uso}/api/v1/user/get_user_basic_data`,
  TOP_ARTISTS: `${endereco_api_em_uso}/api/v1/user/top_artistas`,
  TOP_TRACKS: `${endereco_api_em_uso}/api/v1/user/top_musicas`,
  PERFIL_MUSICAL: `${endereco_api_em_uso}/api/v1/user/perfil_musical`,
  STATUS: `${endereco_api_em_uso}/api/v1/user/status`,
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

/**
 * Verifica se o processamento do usuário já terminou.
 * Se ainda estiver em andamento, exibe um overlay de espera e faz polling a cada 5s.
 * Quando o status mudar para "PRONTO", esconde o overlay e chama o callback onPronto().
 *
 * @param {Function} onPronto - Função chamada quando o processamento terminar.
 * @param {number} maxTentativas - Número máximo de verificações (padrão: 72 = 6 min).
 * @returns {Promise<boolean>} - true se deve prosseguir, false se ainda está processando.
 */
export async function verificarStatusOuAguardar(onPronto, maxTentativas = 72) {
  let res;
  try {
    res = await fetch(API_ENDPOINTS.STATUS, { method: 'GET', credentials: 'include' });
  } catch {
    // Sem conexão: deixa o fluxo normal tratar o erro
    return true;
  }

  if (res.status === 401) {
    window.location.href = HOME_URL;
    return false;
  }

  const { status } = await res.json();

  if (status !== 'PROCESSANDO') {
    return true; // Pronto: o caller pode prosseguir normalmente
  }

  // --- Ainda processando: exibe overlay de espera ---
  const overlay = _criarOverlayProcessamento();
  document.body.appendChild(overlay);

  let tentativas = 0;
  const intervalo = setInterval(async () => {
    tentativas++;

    if (tentativas >= maxTentativas) {
      clearInterval(intervalo);
      overlay.querySelector('#processingMessage').textContent =
        'A análise está demorando mais que o esperado. Tente recarregar a página em alguns minutos.';
      overlay.querySelector('#processingSpinner').classList.add('hidden');
      return;
    }

    try {
      const r = await fetch(API_ENDPOINTS.STATUS, { method: 'GET', credentials: 'include' });
      if (!r.ok) return;
      const { status: novoStatus } = await r.json();

      if (novoStatus !== 'PROCESSANDO') {
        clearInterval(intervalo);
        overlay.remove();
        onPronto();
      }
    } catch {
      // Falha de rede: tenta novamente no próximo ciclo
    }
  }, 5000);

  return false; // O caller NÃO deve prosseguir agora; onPronto() fará isso depois
}

function _criarOverlayProcessamento() {
  const div = document.createElement('div');
  div.id = 'processingOverlay';
  div.style.cssText = `
    position: fixed; inset: 0; z-index: 9999;
    background: rgba(3, 7, 18, 0.96);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 24px;
    text-align: center; padding: 32px;
  `;
  div.innerHTML = `
    <div style="font-size: 3rem; line-height: 1;">🎵</div>
    <div>
      <h2 style="color: #22c55e; font-size: 1.5rem; font-weight: 700; margin-bottom: 8px;">
        Analisando seu perfil musical...
      </h2>
      <p id="processingMessage" style="color: #9ca3af; font-size: 0.95rem; max-width: 380px; line-height: 1.6;">
        Estamos buscando suas músicas e extraindo as emoções com IA.<br>
        Isso pode levar alguns minutos na primeira vez.
      </p>
    </div>
    <div id="processingSpinner"
      style="width: 48px; height: 48px; border: 4px solid #22c55e;
             border-top-color: transparent; border-radius: 50%;
             animation: spin 0.8s linear infinite;">
    </div>
    <p style="color: #6b7280; font-size: 0.8rem;">
      Esta tela vai atualizar automaticamente ✨
    </p>
    <style>
      @keyframes spin { to { transform: rotate(360deg); } }
    </style>
  `;
  return div;
}
