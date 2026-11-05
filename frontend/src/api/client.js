const API_BASE = "/api";

class ApiClient {
  constructor() {
    this.token = localStorage.getItem("prohor_token");
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem("prohor_token", token);
    } else {
      localStorage.removeItem("prohor_token");
    }
  }

  getToken() {
    return this.token;
  }

  async request(endpoint, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Something went wrong");
    }

    return data;
  }

  // Auth
  async register(email, password, full_name) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    });
  }

  async login(email, password) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async getMe() {
    return this.request("/auth/me");
  }

  // Chat
  async sendMessage(message, conversation_id = null) {
    return this.request("/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id }),
    });
  }

  async getConversations() {
    return this.request("/chat/conversations");
  }

  async getMessages(conversationId) {
    return this.request(`/chat/conversations/${conversationId}/messages`);
  }

  // Documents
  async getDocuments() {
    return this.request("/documents");
  }

  async getDocument(id) {
    return this.request(`/documents/${id}`);
  }

  // Legal search
  async searchLegal(query) {
    return this.request(`/legal/search?q=${encodeURIComponent(query)}`);
  }

  async getLegalSource(id) {
    return this.request(`/legal/sources/${id}`);
  }
}

const api = new ApiClient();
export default api;
