import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { isAxiosError } from "axios";
import api from "../api";
import PasswordInput from "../components/PasswordInput";

function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    if (newPassword !== confirmPassword) {
      setMessage("Passwords do not match");
      return;
    }

    try {
      await api.post("/reset-password", { token, new_password: newPassword });
      setDone(true);
    } catch (error) {
      const detail = (isAxiosError(error) && error.response?.data?.detail) || "Something went wrong";
      setMessage(detail);
    }
  };

  if (!token) {
    return (
      <div className="auth-card">
        <div className="status-icon error">!</div>
        <h2>Invalid link</h2>
        <p className="auth-message">This reset link is not valid or has expired.</p>
        <Link to="/admin" className="auth-cta">Back to login</Link>
      </div>
    );
  }

  if (done) {
    return (
      <div className="auth-card">
        <div className="status-icon success">✓</div>
        <h2>Password updated</h2>
        <p className="auth-success">You can now log in with your new password.</p>
        <Link to="/admin" className="auth-cta">Go to login</Link>
      </div>
    );
  }

  return (
    <div className="auth-card">
      <h2>Choose a new password</h2>

      <form onSubmit={handleSubmit}>
        <PasswordInput
          value={newPassword}
          onChange={setNewPassword}
          placeholder="New password (8+ characters)"
          minLength={8}
        />
        <PasswordInput
          value={confirmPassword}
          onChange={setConfirmPassword}
          placeholder="Confirm new password"
          minLength={8}
        />
        <button type="submit" className="btn btn-grad btn-block">Update password</button>
      </form>

      {message && <p className="auth-message">{message}</p>}
    </div>
  );
}

export default ResetPasswordPage;