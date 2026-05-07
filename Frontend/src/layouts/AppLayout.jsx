import { NavLink, useNavigate } from "react-router-dom";
import { useAppContext } from "../context/AppContext";

const navigation = [
  { to: "/", label: "Dashboard" },
  { to: "/timesheets", label: "Timesheets" },
  { to: "/absences", label: "Absences" },
  { to: "/teams", label: "Teams" },
  { to: "/manager", label: "Manager" },
  { to: "/users", label: "Users" }
];

export default function AppLayout({ children }) {
  const { currentUser, logout } = useAppContext();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <main className="page-shell">
        <header className="app-topbar panel">
          <div className="app-brand">
            <h1>Timesheet Portal</h1>
          </div>

          <nav className="top-nav">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => (isActive ? "top-nav-link active" : "top-nav-link")}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="topbar-user">
            <strong className="topbar-user-name">{currentUser?.name}</strong>
            <button className="secondary-button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </header>

        <section className="content-grid">{children}</section>
      </main>
    </div>
  );
}
