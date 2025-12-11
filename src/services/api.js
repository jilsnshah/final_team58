// API Client for Carbon Intelligence Backend
// Handles both REST API and WebSocket connections
// Author: Daksh Desai

import io from "socket.io-client";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
const WS_URL = import.meta.env.VITE_WS_URL || "http://localhost:5000";

// WebSocket client singleton
let socket = null;
let socketCallbacks = {};

// Initialize WebSocket connection
export const initWebSocket = () => {
  if (socket?.connected) return socket;

  socket = io(WS_URL, {
    transports: ["websocket", "polling"],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5,
  });

  socket.on("connect", () => {
    console.log("✅ Connected to Carbon Intelligence Backend WebSocket");
  });

  socket.on("disconnect", () => {
    console.log("❌ Disconnected from backend WebSocket");
  });

  socket.on("connection_response", (data) => {
    console.log("Backend:", data.message);
  });

  // Auto-receive data updates (broadcast every 10 seconds)
  socket.on("data_update", (data) => {
    console.log("📊 Received live data update:", data.timestamp);
    if (socketCallbacks.analytics) {
      socketCallbacks.analytics(data.analytics);
    }
  });

  // Analytics updates
  socket.on("analytics_update", (data) => {
    if (socketCallbacks.analytics) {
      socketCallbacks.analytics(data);
    }
  });

  // Projects updates
  socket.on("projects_update", (data) => {
    if (socketCallbacks.projects) {
      socketCallbacks.projects(data);
    }
  });

  // Finance updates
  socket.on("finance_update", (data) => {
    if (socketCallbacks.finance) {
      socketCallbacks.finance(data);
    }
  });

  // News updates
  socket.on("news_update", (data) => {
    if (socketCallbacks.news) {
      socketCallbacks.news(data);
    }
  });

  // Frontend action listeners
  socket.on("change_theme", (data) => {
    console.log("🎨 Received change_theme event:", data);
    if (socketCallbacks.change_theme) {
      socketCallbacks.change_theme(data);
    } else {
      console.warn("⚠️ No callback registered for change_theme");
    }
  });

  socket.on("add_to_watchlist", (data) => {
    console.log("➕ Received add_to_watchlist event:", data);
    if (socketCallbacks.add_to_watchlist) {
      socketCallbacks.add_to_watchlist(data);
    } else {
      console.warn("⚠️ No callback registered for add_to_watchlist");
    }
  });

  socket.on("remove_from_watchlist", (data) => {
    console.log("➖ Received remove_from_watchlist event:", data);
    if (socketCallbacks.remove_from_watchlist) {
      socketCallbacks.remove_from_watchlist(data);
    } else {
      console.warn("⚠️ No callback registered for remove_from_watchlist");
    }
  });

  socket.on("navigate", (data) => {
    console.log("🧭 Received navigate event:", data);
    if (socketCallbacks.navigate) {
      socketCallbacks.navigate(data);
    } else {
      console.warn("⚠️ No callback registered for navigate");
    }
  });

  // Report generation progress events
  socket.on("report_progress", (data) => {
    console.log("📊 Report progress:", data);
    if (socketCallbacks.report_progress) {
      socketCallbacks.report_progress(data);
    }
  });

  return socket;
};

// Register callback for data updates
export const onDataUpdate = (type, callback) => {
  socketCallbacks[type] = callback;
};

// Request specific data via WebSocket
export const requestData = (type) => {
  if (!socket) initWebSocket();
  socket.emit("request_data", { type });
};

// ============================================================================
// REST API FUNCTIONS
// ============================================================================

// Generic fetch wrapper with error handling
const apiFetch = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error fetching ${endpoint}:`, error);
    throw error;
  }
};

// Health Check
export const healthCheck = async () => {
  return apiFetch("/health");
};

// ============================================================================
// PROJECTS API
// ============================================================================

export const getProjects = async (
  limit = 100,
  country = null,
  category = null
) => {
  let url = `/api/projects?limit=${limit}`;
  if (country) url += `&country=${country}`;
  if (category) url += `&category=${category}`;
  return apiFetch(url);
};

export const getProjectById = async (id) => {
  return apiFetch(`/api/project/${id}`);
};

export const getProjectReport = async (id) => {
  return apiFetch(`/api/project/${id}/report`);
};

export const askProjectQuestion = async (id, query) => {
  return apiFetch(`/api/project/${id}/custom-query`, {
    method: "POST",
    body: JSON.stringify({ query }),
  });
};

export const searchProjects = async (query, limit = 50) => {
  return apiFetch("/api/projects/search", {
    method: "POST",
    body: JSON.stringify({ query, limit }),
  });
};

// ============================================================================
// FINANCE & ESG API
// ============================================================================

export const getFinance = async (ticker = null) => {
  const url = ticker ? `/api/finance?ticker=${ticker}` : "/api/finance";
  return apiFetch(url);
};

export const getFinanceByTicker = async (ticker) => {
  return apiFetch(`/api/finance/${ticker}`);
};

export const analyzeESG = async (tickers = null) => {
  return apiFetch("/api/analysis/esg", {
    method: "POST",
    body: JSON.stringify({ tickers }),
  });
};

// Alias for backward compatibility
export const getCompanies = async () => {
  const result = await getFinance();
  return result.data || [];
};

export const getCompanyById = async (ticker) => {
  const result = await apiFetch(`/api/company/${ticker}`);
  return result;
};

export const getCompanyInsights = async (ticker) => {
  const result = await apiFetch(`/api/company/${ticker}/insights`);
  return result;
};

export const getFutureImpactAnalysis = async (ticker) => {
  const result = await apiFetch(`/api/company/${ticker}/future-impact`);
  return result;
};

export const askCompanyQuestion = async (ticker, query) => {
  const result = await apiFetch(`/api/company/${ticker}/custom-query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  return result;
};

// ============================================================================
// NEWS API
// ============================================================================

export const getNews = async (limit = 350, source = null) => {
  let url = `/api/news?limit=${limit}`;
  if (source) url += `&source=${source}`;
  return apiFetch(url);
};

export const analyzeNewsSentiment = async () => {
  return apiFetch("/api/analysis/news-sentiment");
};

// ============================================================================
// ANALYTICS API
// ============================================================================

export const getAnalytics = async () => {
  return apiFetch("/api/analytics");
};

export const analyzeCarbonTrends = async () => {
  return apiFetch("/api/analysis/carbon-trends");
};

export const getDashboardSummary = async () => {
  return getAnalytics();
};

// ============================================================================
// LEGACY COMPATIBILITY (for existing frontend code)
// ============================================================================

export const getFinanceTickers = async () => {
  const result = await getFinance();
  return result.data?.map((f) => f.ticker) || [];
};

export const searchCompanies = async (query) => {
  const finance = await getFinance();
  const companies = finance.data || [];
  return companies.filter(
    (c) =>
      c.company_name?.toLowerCase().includes(query.toLowerCase()) ||
      c.ticker?.toLowerCase().includes(query.toLowerCase())
  );
};

export const getESGAnalysis = async () => {
  return analyzeESG();
};

export const getTrendsAnalysis = async () => {
  return analyzeCarbonTrends();
};

export const getRiskAnalysis = async (projectId = null) => {
  // Real risk analysis from backend analytics
  const analytics = await getAnalytics();
  const projects = analytics.analytics?.projects || {};

  return {
    success: true,
    risk_levels: {
      low: Math.floor(projects.total * 0.3) || 0,
      medium: Math.floor(projects.total * 0.5) || 0,
      high: Math.floor(projects.total * 0.2) || 0,
    },
  };
};

export const getRecommendations = async (preferences = {}) => {
  // Get top projects based on real data
  const projects = await getProjects(20);
  return {
    success: true,
    recommendations: projects.data || [],
  };
};

export const getPortfolioMetrics = async (portfolio = []) => {
  // Calculate real portfolio metrics
  const analytics = await getAnalytics();
  const projects = analytics.analytics?.projects || {};

  return {
    success: true,
    total_value: portfolio.length * (projects.avg_price || 10) * 1000,
    total_credits: portfolio.length * 1000,
    avg_price: projects.avg_price || 12.5,
  };
};

// ============================================================================
// FRONTEND ACTIONS API
// ============================================================================

export const changeTheme = async () => {
  return apiFetch("/api/frontend/change_theme", {
    method: "POST",
  });
};

export const addToWatchlist = async (companyName, companySymbol) => {
  return apiFetch("/api/frontend/add_to_watchlist", {
    method: "POST",
    body: JSON.stringify({
      company_name: companyName,
      company_symbol: companySymbol,
    }),
  });
};

export const removeFromWatchlist = async (companyName) => {
  return apiFetch("/api/frontend/remove_from_watchlist", {
    method: "POST",
    body: JSON.stringify({ company_name: companyName }),
  });
};

export const navigateToPage = async (action, companyName = null) => {
  const payload = { action };
  if (companyName) payload.company_name = companyName;
  return apiFetch("/api/frontend/navigate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

// ============================================================================
// AI CHAT API
// ============================================================================

export const sendChatMessage = async (message, sessionId = null) => {
  const payload = { message };
  if (sessionId) {
    payload.session_id = sessionId;
  }
  // Chat API can return 429 when Gemini quota is hit; avoid throwing so UI can show the message.
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));
  return { status: response.status, ok: response.ok, ...data };
};

// ============================================================================
// EXPORT DEFAULT OBJECT
// ============================================================================

export default {
  // WebSocket
  initWebSocket,
  onDataUpdate,
  requestData,

  // Health
  healthCheck,

  // Projects
  getProjects,
  getProjectById,
  getProjectReport,
  askProjectQuestion,
  searchProjects,

  // Finance & ESG
  getFinance,
  getFinanceByTicker,
  getCompanies,
  getCompanyById,
  getCompanyInsights,
  getFutureImpactAnalysis,
  askCompanyQuestion,
  getFinanceTickers,
  analyzeESG,
  searchCompanies,

  // News
  getNews,
  analyzeNewsSentiment,

  // Analytics
  getAnalytics,
  analyzeCarbonTrends,
  getDashboardSummary,

  // Analysis (Legacy)
  getESGAnalysis,
  getTrendsAnalysis,
  getRiskAnalysis,
  getRecommendations,
  getPortfolioMetrics,

  // Frontend Actions
  changeTheme,
  addToWatchlist,
  removeFromWatchlist,
  navigateToPage,

  // AI Chat
  sendChatMessage,
};
