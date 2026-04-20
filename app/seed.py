from datetime import date

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models import AbsenceRequest, AbsenceStatus, AbsenceType, DayType, RoleEnum, Team, Timesheet, TimesheetDay, TimesheetStatus, User


def seed_database() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "admin@demo.local").first():
            return

        team_alpha = Team(name="Team Alpha", active=True)
        team_beta = Team(name="Team Beta", active=True)
        db.add_all([team_alpha, team_beta])
        db.flush()

        users = [
            User(email="admin@demo.local", name="Admin User", role=RoleEnum.ADMIN, team_id=team_alpha.id, hashed_password=get_password_hash(settings.demo_password)),
            User(email="manager.alpha@demo.local", name="Manager Alpha", role=RoleEnum.MANAGER, team_id=team_alpha.id, hashed_password=get_password_hash(settings.demo_password)),
            User(email="manager.beta@demo.local", name="Manager Beta", role=RoleEnum.MANAGER, team_id=team_beta.id, hashed_password=get_password_hash(settings.demo_password)),
            User(email="alice@demo.local", name="Alice Employee", role=RoleEnum.EMPLOYEE, team_id=team_alpha.id, hashed_password=get_password_hash(settings.demo_password)),
            User(email="bob@demo.local", name="Bob Employee", role=RoleEnum.EMPLOYEE, team_id=team_alpha.id, hashed_password=get_password_hash(settings.demo_password)),
            User(email="eva@demo.local", name="Eva Employee", role=RoleEnum.EMPLOYEE, team_id=team_beta.id, hashed_password=get_password_hash(settings.demo_password)),
        ]
        db.add_all(users)
        db.flush()

        team_alpha.manager_user_id = users[1].id
        team_beta.manager_user_id = users[2].id
        db.add_all([team_alpha, team_beta])
        db.flush()

        alice = users[3]
        bob = users[4]
        eva = users[5]
        manager_alpha = users[1]

        ts_alice = Timesheet(user_id=alice.id, month=4, year=2026, status=TimesheetStatus.DRAFT)
        ts_bob = Timesheet(
            user_id=bob.id,
            month=4,
            year=2026,
            status=TimesheetStatus.SUBMITTED,
            approver_user_id=manager_alpha.id,
        )
        db.add_all([ts_alice, ts_bob])
        db.flush()

        alice_days = [
            TimesheetDay(timesheet_id=ts_alice.id, date=date(2026, 4, 1), hours=8, day_type=DayType.WORK),
            TimesheetDay(timesheet_id=ts_alice.id, date=date(2026, 4, 2), hours=8, day_type=DayType.WORK),
            TimesheetDay(timesheet_id=ts_alice.id, date=date(2026, 4, 3), hours=8, day_type=DayType.WORK),
        ]
        bob_days = [
            TimesheetDay(timesheet_id=ts_bob.id, date=date(2026, 4, 1), hours=8, day_type=DayType.WORK),
            TimesheetDay(timesheet_id=ts_bob.id, date=date(2026, 4, 2), hours=8, day_type=DayType.WORK),
        ]
        db.add_all(alice_days + bob_days)

        absences = [
            AbsenceRequest(user_id=alice.id, type=AbsenceType.VACATION, date_from=date(2026, 5, 5), date_to=date(2026, 5, 7), status=AbsenceStatus.REQUESTED, comment="Family trip"),
            AbsenceRequest(user_id=eva.id, type=AbsenceType.SICK, date_from=date(2026, 4, 10), date_to=date(2026, 4, 11), status=AbsenceStatus.APPROVED, approver_user_id=users[2].id, comment="Doctor note received"),
        ]
        db.add_all(absences)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
