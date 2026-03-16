import { useIsAuthenticated } from "@azure/msal-react";
import { ChatPanel } from "./Components/ChatPanel";
import { useAuth } from "./Hooks/useAuth";

export default function App() {
  const isAuthenticated = useIsAuthenticated();
  const { login } = useAuth();

  if (!isAuthenticated) {
    return (
      <div className="sign-in-page">
        <h1>Customer Chatbot</h1>
        <p>Sign in to start chatting</p>
        <button className="sign-in-btn" onClick={login}>
          Sign in with Microsoft
        </button>
      </div>
    );
  }

  return (
    <div className="app">
      <ChatPanel />
    </div>
  );
}
