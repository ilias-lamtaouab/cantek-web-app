import { useState } from "react";
import { isAxiosError } from "axios";
import api from "../api";
import PasswordInput from "./PasswordInput";

interface AuthFormProps {
  onLoginSuccess: (token: string) => void;
}

type Mode = "login" | "forgot";

function AuthForm({ onLoginSuccess }: AuthFormProps) {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<{ text: string; type: "error" | "success" } | null>(null);
  const [loading, setLoading] = useState(false);

  const switchMode = (newMode: Mode) => {
    setMode(newMode);
    setMessage(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setLoading(true);

    try {
      if (mode === "login") {
        const response = await api.post("/login", { email, password });
        const token = response.data.access_token;
        localStorage.setItem("token", token);
        onLoginSuccess(token);
      } else {
        await api.post("/forgot-password", { email });
        setMessage({
          text: "If this email exists, a reset link has been sent. Check your inbox.",
          type: "success",
        });
      }
    } catch (error) {
      const detail = isAxiosError(error) ? error.response?.data?.detail : undefined;
      setMessage({
        text: typeof detail === "string" ? detail : "Something went wrong",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const title = mode === "login" ? "Log In" : "Forgot Password";
  const buttonText = mode === "login" ? "Log In" : "Send reset link";

  return (
    <div className="auth-card">
      <h2>{title}</h2>

      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        {mode === "login" && (
          <PasswordInput value={password} onChange={setPassword} placeholder="Password" />
        )}

        <button type="submit" className={`btn btn-grad btn-block ${loading ? "is-loading" : ""}`} disabled={loading}>
          {loading ? "Please wait..." : buttonText}
        </button>
      </form>

      {message && (
        <p className={message.type === "success" ? "auth-success" : "auth-message"}>
          {message.text}
        </p>
      )}

      {mode === "login" ? (
        <button type="button" className="auth-toggle" onClick={() => switchMode("forgot")}>
          Forgot password?
        </button>
      ) : (
        <button type="button" className="auth-toggle" onClick={() => switchMode("login")}>
          Back to log in
        </button>
      )}
    </div>
  );
}

export default AuthForm;