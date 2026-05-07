import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useAppContext } from "../context/AppContext";

export default function LoginPage() {
  const { currentUser, login } = useAppContext();
  const [form, setForm] = useState({
    email: "manager.alpha@demo.local",
    password: "demo123"
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (currentUser) {
    return <Navigate to="/" replace />;
  }

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      await login(form);
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-shell">
      <section className="login-card">
        <p className="eyebrow">School project frontend</p>
        <h1>Timesheet & Absence Portal</h1>
        <p className="muted-text">
          Login is intentionally simple, but fully connected to the FastAPI backend. Seeded password: <strong>demo123</strong>
        </p>

        <form className="stack-lg" onSubmit={handleSubmit}>
          <label>
            <span>Email</span>
            <input
              type="email"
              value={form.email}
              onChange={(event) => updateField("email", event.target.value)}
              required
            />
          </label>

          <label>
            <span>Password</span>
            <input
              type="password"
              value={form.password}
              onChange={(event) => updateField("password", event.target.value)}
              required
            />
          </label>

          {error ? <div className="error-inline">{error}</div> : null}

          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="demo-credentials">
          <strong>Demo users</strong>
          <span>`admin@demo.local`</span>
          <span>`manager.alpha@demo.local`</span>
          <span>`alice@demo.local`</span>
        </div>
      </section>
    </div>
  );
}
