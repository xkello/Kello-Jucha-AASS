import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useAppContext } from "../context/AppContext";
import {
  ErrorMessage,
  LoadingState,
  PageHeader,
  Panel,
  StatusPill
} from "../components/ui/Feedback";
import teamService from "../services/teamService";
import userService from "../services/userService";

export default function TeamDetailPage() {
  const { teamId } = useParams();
  const { currentUser } = useAppContext();
  const [state, setState] = useState({
    loading: true,
    error: "",
    team: null,
    users: []
  });
  const [memberId, setMemberId] = useState("");
  const [editForm, setEditForm] = useState({
    name: "",
    manager_user_id: "",
    active: true
  });

  useEffect(() => {
    loadTeam();
  }, [teamId]);

  async function loadTeam() {
    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const [teams, users] = await Promise.all([teamService.list(), userService.list()]);
      const team = teams.find((item) => String(item.id) === String(teamId));
      if (!team) {
        throw new Error("Team not found.");
      }
      setEditForm({
        name: team.name,
        manager_user_id: team.manager_user_id || "",
        active: team.active
      });
      setState({
        loading: false,
        error: "",
        team,
        users
      });
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
        team: null,
        users: []
      });
    }
  }

  const members = useMemo(
    () => state.users.filter((user) => String(user.team_id) === String(teamId)),
    [state.users, teamId]
  );
  const availableUsers = useMemo(
    () => state.users.filter((user) => !user.team_id || String(user.team_id) !== String(teamId)),
    [state.users, teamId]
  );

  async function handleUpdate(event) {
    event.preventDefault();
    try {
      await teamService.update(teamId, {
        name: editForm.name,
        manager_user_id: editForm.manager_user_id ? Number(editForm.manager_user_id) : null,
        active: Boolean(editForm.active)
      });
      await loadTeam();
    } catch (error) {
      setState((current) => ({ ...current, error: error.message }));
    }
  }

  async function handleAddMember(event) {
    event.preventDefault();
    try {
      await teamService.addMember(teamId, Number(memberId));
      setMemberId("");
      await loadTeam();
    } catch (error) {
      setState((current) => ({ ...current, error: error.message }));
    }
  }

  async function handleRemoveMember(userId) {
    try {
      await teamService.removeMember(teamId, userId);
      await loadTeam();
    } catch (error) {
      setState((current) => ({ ...current, error: error.message }));
    }
  }

  if (state.loading) {
    return <LoadingState label="Loading team detail..." />;
  }

  if (state.error && !state.team) {
    return <ErrorMessage message={state.error} />;
  }

  return (
    <>
      <PageHeader
        title={state.team.name}
        description={`Team detail assembled from /teams and /users for team ${state.team.id}.`}
      />

      {state.error ? <ErrorMessage message={state.error} /> : null}

      <Panel title="Team metadata">
        <div className="detail-grid">
          <div>
            <span className="muted-text">Team ID</span>
            <p>{state.team.id}</p>
          </div>
          <div>
            <span className="muted-text">Manager user ID</span>
            <p>{state.team.manager_user_id || "-"}</p>
          </div>
          <div>
            <span className="muted-text">Status</span>
            <div>
              <StatusPill tone={state.team.active ? "success" : "danger"}>
                {state.team.active ? "Active" : "Inactive"}
              </StatusPill>
            </div>
          </div>
          <div>
            <span className="muted-text">Members</span>
            <p>{members.length}</p>
          </div>
        </div>
      </Panel>

      {currentUser.role === "ADMIN" ? (
        <Panel title="Admin team management">
          <form className="stack-lg" onSubmit={handleUpdate}>
            <div className="form-grid three-columns">
              <label>
                <span>Name</span>
                <input
                  value={editForm.name}
                  onChange={(event) => setEditForm((current) => ({ ...current, name: event.target.value }))}
                  required
                />
              </label>
              <label>
                <span>Manager user id</span>
                <input
                  type="number"
                  value={editForm.manager_user_id}
                  onChange={(event) => setEditForm((current) => ({ ...current, manager_user_id: event.target.value }))}
                />
              </label>
              <label>
                <span>Active</span>
                <select
                  value={String(editForm.active)}
                  onChange={(event) => setEditForm((current) => ({ ...current, active: event.target.value === "true" }))}
                >
                  <option value="true">true</option>
                  <option value="false">false</option>
                </select>
              </label>
            </div>
            <button className="primary-button" type="submit">
              Save team
            </button>
          </form>

          <form className="inline-actions" onSubmit={handleAddMember}>
            <select value={memberId} onChange={(event) => setMemberId(event.target.value)} required>
              <option value="">Select user to add</option>
              {availableUsers.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.name} ({user.role})
                </option>
              ))}
            </select>
            <button className="secondary-button" type="submit">
              Add member
            </button>
          </form>
        </Panel>
      ) : null}

      <Panel title="Team members">
        <div className="stack-md">
          {members.map((member) => (
            <div className="list-row" key={member.id}>
              <div>
                <strong>{member.name}</strong>
                <p className="muted-text">
                  {member.email} | {member.role}
                </p>
              </div>
              {currentUser.role === "ADMIN" ? (
                <button className="ghost-button" onClick={() => handleRemoveMember(member.id)}>
                  Remove
                </button>
              ) : null}
            </div>
          ))}
        </div>
      </Panel>
    </>
  );
}
