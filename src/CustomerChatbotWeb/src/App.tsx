import { useIsAuthenticated } from "@azure/msal-react";
import { ChatPanel } from "./Components/ChatPanel";
import { useAuth } from "./Hooks/useAuth";

export default function App() {
  const isAuthenticated = useIsAuthenticated();
  const { login } = useAuth();

  if (!isAuthenticated) {
    return (
      <div style={{ textAlign: "center", marginTop: "2rem" }}>
        <h1>Customer Chatbot</h1>
        <p>Sign in to start chatting</p>
        <button onClick={login}>Sign in with Microsoft</button>
      </div>
    );
  }

  return (
    <div className="app">
      <ChatPanel />
    </div>
  );
}
