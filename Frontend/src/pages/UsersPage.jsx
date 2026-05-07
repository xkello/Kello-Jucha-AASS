import { useEffect, useMemo, useState } from "react";
import { useAppContext } from "../context/AppContext";
import {
  ErrorMessage,
  LoadingState,
  PageHeader,
  Panel,
  StatusPill
} from "../components/ui/Feedback";
import userService from "../services/userService";
import teamService from "../services/teamService";

export default function UsersPage() {
  const { currentUser } = useAppContext();
  const [state, setState] = useState({
    loading: true,
    error: "",
    users: [],
    teams: []
  });
  const [form, setForm] = useState({
    email: "",
    name: "",
    role: "EMPLOYEE",
    team_id: "",
    password: "demo123"
  });

  useEffect(() => {
    loadUsers();
  }, []);

  async function loadUsers() {
    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const [users, teams] = await Promise.all([userService.list(), teamService.list()]);
      setState({
        loading: false,
        error: "",
        users,
        teams
      });
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
        users: [],
        teams: []
      });
    }
  }

  const teamNameById = useMemo(() => {
    const map = {};
    state.teams.forEach((team) => {
      map[team.id] = team.name;
    });
    return map;
  }, [state.teams]);

  async function handleCreate(event) {
    event.preventDefault();
    try {
      await userService.create({
        ...form,
        team_id: form.team_id ? Number(form.team_id) : null
      });
      setForm({
        email: "",
        name: "",
        role: "EMPLOYEE",
        team_id: "",
        password: "demo123"
      });
      await loadUsers();
    } catch (error) {
      setState((current) => ({ ...current, error: error.message }));
    }
  }

  async function handleDeactivate(userId) {
    try {
      await userService.deactivate(userId);
      await loadUsers();
    } catch (error) {
      setState((current) => ({ ...current, error: error.message }));
    }
  }

  if (state.loading) {
    return <LoadingState label="Loading users..." />;
  }

  if (state.error && !state.users.length) {
    return <ErrorMessage message={state.error} />;
  }

  return (
    <>
      <PageHeader
        title={currentUser.role === "ADMIN" ? "Users management" : "User profile"}
        description="User listing from GET /users with lightweight admin management."
      />

      {state.error ? <ErrorMessage message={state.error} /> : null}

      <Panel title="Current user">
        <div className="detail-grid">
          <div>
            <span className="muted-text">Name</span>
            <p>{currentUser.name}</p>
          </div>
          <div>
            <span className="muted-text">Email</span>
            <p>{currentUser.email}</p>
          </div>
          <div>
            <span className="muted-text">Role</span>
            <p>{currentUser.role}</p>
          </div>
          <div>
            <span className="muted-text">Team</span>
            <p>{currentUser.team_id ? teamNameById[currentUser.team_id] || currentUser.team_id : "-"}</p>
          </div>
        </div>
      </Panel>

      {currentUser.role === "ADMIN" ? (
        <Panel title="Create user">
          <form className="form-grid three-columns" onSubmit={handleCreate}>
            <label>
              <span>Name</span>
              <input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} required />
            </label>
            <label>
              <span>Email</span>
              <input type="email" value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} required />
            </label>
            <label>
              <span>Role</span>
              <select value={form.role} onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))}>
                <option value="EMPLOYEE">EMPLOYEE</option>
                <option value="MANAGER">MANAGER</option>
                <option value="ADMIN">ADMIN</option>
              </select>
            </label>
            <label>
              <span>Team</span>
              <select value={form.team_id} onChange={(event) => setForm((current) => ({ ...current, team_id: event.target.value }))}>
                <option value="">No team</option>
                {state.teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Password</span>
              <input value={form.password} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} required />
            </label>
            <button className="primary-button align-end" type="submit">
              Create user
            </button>
          </form>
        </Panel>
      ) : null}

      <Panel title="Visible users">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Role</th>
                <th>Team</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {state.users.map((user) => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td>
                    <strong>{user.name}</strong>
                    <div className="muted-text">{user.email}</div>
                  </td>
                  <td>{user.role}</td>
                  <td>{user.team_id ? teamNameById[user.team_id] || user.team_id : "-"}</td>
                  <td>
                    <StatusPill tone={user.active ? "success" : "danger"}>
                      {user.active ? "Active" : "Inactive"}
                    </StatusPill>
                  </td>
                  <td>
                    {currentUser.role === "ADMIN" && user.active ? (
                      <button className="ghost-button" onClick={() => handleDeactivate(user.id)}>
                        Deactivate
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}
