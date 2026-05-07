from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.core.database import Base
from app.core.security import get_password_hash
from app.models import RoleEnum, Team, User


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def sample_users(db_session):
    team_a = Team(name="Alpha", active=True)
    team_b = Team(name="Beta", active=True)
    db_session.add_all([team_a, team_b])
    db_session.flush()

    admin = User(email="admin@test.local", name="Admin", role=RoleEnum.ADMIN, team_id=team_a.id, active=True, hashed_password=get_password_hash("demo123"))
    manager_a = User(email="manager.a@test.local", name="Manager A", role=RoleEnum.MANAGER, team_id=team_a.id, active=True, hashed_password=get_password_hash("demo123"))
    manager_b = User(email="manager.b@test.local", name="Manager B", role=RoleEnum.MANAGER, team_id=team_b.id, active=True, hashed_password=get_password_hash("demo123"))
    employee_a = User(email="employee.a@test.local", name="Employee A", role=RoleEnum.EMPLOYEE, team_id=team_a.id, active=True, hashed_password=get_password_hash("demo123"))
    employee_b = User(email="employee.b@test.local", name="Employee B", role=RoleEnum.EMPLOYEE, team_id=team_b.id, active=True, hashed_password=get_password_hash("demo123"))

    db_session.add_all([admin, manager_a, manager_b, employee_a, employee_b])
    db_session.flush()

    team_a.manager_user_id = manager_a.id
    team_b.manager_user_id = manager_b.id
    db_session.add_all([team_a, team_b])
    db_session.commit()

    return {
        "admin": admin,
        "manager_a": manager_a,
        "manager_b": manager_b,
        "employee_a": employee_a,
        "employee_b": employee_b,
        "team_a": team_a,
        "team_b": team_b,
    }
