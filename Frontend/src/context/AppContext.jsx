import { createContext, useContext, useEffect, useState } from "react";
import authService from "../services/authService";

const TOKEN_KEY = "timesheet_portal_token";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [currentUser, setCurrentUser] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [bootError, setBootError] = useState("");

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      if (!token) {
        if (active) {
          setCurrentUser(null);
          setInitializing(false);
        }
        return;
      }

      try {
        const me = await authService.getMe();
        if (active) {
          setCurrentUser(me);
          setBootError("");
        }
      } catch (error) {
        localStorage.removeItem(TOKEN_KEY);
        if (active) {
          setToken(null);
          setCurrentUser(null);
          setBootError(error.message);
        }
      } finally {
        if (active) {
          setInitializing(false);
        }
      }
    }

    bootstrap();

    return () => {
      active = false;
    };
  }, [token]);

  async function login(credentials) {
    const result = await authService.login(credentials);
    localStorage.setItem(TOKEN_KEY, result.access_token);
    setToken(result.access_token);
    const me = await authService.getMe();
    setCurrentUser(me);
    return me;
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setCurrentUser(null);
  }

  return (
    <AppContext.Provider
      value={{
        token,
        currentUser,
        initializing,
        bootError,
        login,
        logout
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used inside AppProvider");
  }
  return context;
}
