import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAppContext } from "../context/AppContext";
import teamService from "../services/teamService";
import userService from "../services/userService";
import {
  ErrorMessage,
  LoadingState,
  PageHeader,
  Panel,
  StatusPill
} from "../components/ui/Feedback";

export default function TeamsOverviewPage() {
  const { currentUser } = useAppContext();
  const [state, setState] = useState({
    loading: true,
    error: "",
    teams: [],
    users: []
  });
  const [form, setForm] = useState({
    name: "",
    manager_user_id: ""
  });

  useEffect(() => {
    loadTeams();
  }, []);

  async function loadTeams() {
    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const [teams, users] = await Promise.all([teamService.list(), userService.list()]);
      setState({
        loading: false,
        error: "",
        teams,
        users
      });
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
        teams: [],
        users: []
      });
    }
  }

  async function handleCreate(event) {
    event.preventDefault();
    try {
      await teamService.create({
        name: form.name,
        manager_user_id: form.manager_user_id ? Number(form.manager_user_id) : null
      });
      setForm({ name: "", manager_user_id: "" });
      await loadTeams();
    } catch (error) {
      setState((current) => ({ ...current, error: error.message }));
    }
  }

  const memberCountByTeam = useMemo(() => {
    const counts = {};
    state.users.forEach((user) => {
      if (user.team_id) {
        counts[user.team_id] = (counts[user.team_id] || 0) + 1;
      }
    });
    return counts;
  }, [state.users]);

  if (state.loading) {
    return <LoadingState label="Loading teams..." />;
  }

  if (state.error && !state.teams.length) {
    return <ErrorMessage message={state.error} />;
  }

  return (
    <>
      <PageHeader title="Teams overview" description="Team list based on GET /teams and member counts derived from users." />
      {state.error ? <ErrorMessage message={state.error} /> : null}

      {currentUser.role === "ADMIN" ? (
        <Panel title="Create team">
          <form className="form-grid three-columns" onSubmit={handleCreate}>
            <label>
              <span>Team name</span>
              <input
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                required
              />
            </label>
            <label>
              <span>Manager user id</span>
              <input
                type="number"
                value={form.manager_user_id}
                onChange={(event) => setForm((current) => ({ ...current, manager_user_id: event.target.value }))}
              />
            </label>
            <button className="primary-button align-end" type="submit">
              Create
            </button>
          </form>
        </Panel>
      ) : null}

      <Panel title="Existing teams">
        <div className="card-grid">
          {state.teams.map((team) => (
            <Link className="team-card" key={team.id} to={`/teams/${team.id}`}>
              <div className="team-card-header">
                <h3>{team.name}</h3>
                <StatusPill tone={team.active ? "success" : "danger"}>
                  {team.active ? "Active" : "Inactive"}
                </StatusPill>
              </div>
              <p className="muted-text">Manager user ID: {team.manager_user_id || "-"}</p>
              <strong>{memberCountByTeam[team.id] || 0} members</strong>
            </Link>
          ))}
        </div>
      </Panel>
    </>
  );
}
