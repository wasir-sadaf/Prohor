import { createContext, useContext, useState, useEffect, useCallback } from "react";
import api from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      if (!api.getToken()) {
        setLoading(false);
        return;
      }
      const data = await api.getMe();
      setUser(data.user);
    } catch {
      api.setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email, password) => {
    const data = await api.login(email, password);
    api.setToken(data.session.access_token);
    setUser(data.user);
    return data;
  };

  const register = async (email, password, full_name) => {
    const data = await api.register(email, password, full_name);
    if (data.session) {
      api.setToken(data.session.access_token);
      setUser(data.user);
    }
    return data;
  };

  const logout = () => {
    api.setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
