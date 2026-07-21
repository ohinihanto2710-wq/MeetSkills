// ===== CONFIGURATION =====
const API_URL = 'https://meetskills.onrender.com/api';

// ===== GESTION DES TOKENS =====
function getToken() {
  return localStorage.getItem('access_token');
}

function setTokens(access, refresh) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

function removeTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

function isLoggedIn() {
  return !!getToken();
}

// ===== REQUÊTES HTTP =====
async function apiGet(endpoint) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  if (response.status === 401) { redirectToLogin(); return null; }
  return response.json();
}

async function apiPost(endpoint, data, auth = true) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) headers['Authorization'] = `Bearer ${getToken()}`;
  const response = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data)
  });
  return { status: response.status, data: await response.json() };
}

// ===== AUTH =====
async function login(email, password) {
  const result = await apiPost('/auth/jwt/create/', { email, password }, false);
  if (result.status === 200) {
    setTokens(result.data.access, result.data.refresh);
    return true;
  }
  return false;
}

async function logout() {
  removeTokens();
  window.location.href = 'index.html';
}

async function register(data) {
  return await apiPost('/auth/users/', data, false);
}

// ===== MATCHING =====
async function getAnnonces(type = null) {
  const query = type ? `?type=${type}` : '';
  return await apiGet(`/matching/annonces/${query}`);
}

async function getMatches() {
  return await apiGet('/matching/matches/');
}

async function getCompetences() {
  return await apiGet('/matching/competences/');
}

async function publierAnnonce(data) {
  return await apiPost('/matching/annonces/', data);
}

// ===== MESSAGING =====
async function getConversations() {
  return await apiGet('/messaging/conversations/');
}

async function creerConversation(participantId, matchId = null) {
  const data = { participant_id: participantId };
  if (matchId) data.match = matchId;
  return await apiPost('/messaging/conversations/', data);
}

async function getMessages(conversationId) {
  return await apiGet(`/messaging/conversations/${conversationId}/messages/`);
}

async function envoyerMessage(conversationId, contenu) {
  return await apiPost(`/messaging/conversations/${conversationId}/envoyer/`, { contenu });
}

// ===== UTILITAIRES =====
function redirectToLogin() {
  window.location.href = 'connexion.html';
}

function getInitiales(prenom, nom) {
  return `${prenom.charAt(0)}${nom.charAt(0)}`.toUpperCase();
}

function updateHeader() {
  const actions = document.getElementById('headerActions');
  if (!actions) return;
  if (isLoggedIn()) {
    actions.innerHTML = `
      <a href="profil.html" class="btn btn--outline">Mon profil</a>
      <button onclick="logout()" class="btn btn--primary">Déconnexion</button>
    `;
  }
}

// Exécuté sur chaque page
document.addEventListener('DOMContentLoaded', updateHeader);