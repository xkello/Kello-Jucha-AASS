import { Link } from "react-router-dom";

export function PageHeader({ title, description, action, secondaryAction }) {
  return (
    <div className="page-header panel">
      <div>
        <p className="eyebrow">Module view</p>
        <h2>{title}</h2>
        {description ? <p className="muted-text">{description}</p> : null}
      </div>
      <div className="header-actions">
        {secondaryAction}
        {action}
      </div>
    </div>
  );
}

export function Panel({ title, children, actions }) {
  return (
    <section className="panel">
      {(title || actions) ? (
        <div className="panel-header">
          <h3>{title}</h3>
          <div className="header-actions">{actions}</div>
        </div>
      ) : null}
      {children}
    </section>
  );
}

export function StatCard({ label, value, tone = "default" }) {
  return (
    <article className={`stat-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

export function StatusPill({ children, tone = "default" }) {
  return <span className={`status-pill ${tone}`}>{children}</span>;
}

export function LoadingState({ label = "Loading..." }) {
  return (
    <div className="panel centered-state">
      <div className="spinner" />
      <p>{label}</p>
    </div>
  );
}

export function ErrorMessage({ message, retry }) {
  return (
    <div className="panel error-box">
      <strong>Something went wrong</strong>
      <p>{message}</p>
      {retry ? (
        <button className="secondary-button" onClick={retry}>
          Try again
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({ title, description, actionLabel, actionTo }) {
  return (
    <div className="panel centered-state">
      <strong>{title}</strong>
      <p>{description}</p>
      {actionLabel && actionTo ? (
        <Link className="primary-button" to={actionTo}>
          {actionLabel}
        </Link>
      ) : null}
    </div>
  );
}
