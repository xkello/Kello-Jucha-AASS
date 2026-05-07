from datetime import date

import pytest
from fastapi import HTTPException

from app.models import AbsenceType, DayType, AuditLog, TimesheetStatus
from app.schemas import AbsenceCreate, DayEntryCreate
from app.services.absences import approve_absence, create_absence
from app.services.timesheets import approve_timesheet, reject_timesheet, submit_timesheet, unlock_timesheet, upsert_timesheet_days


def build_entries(year: int, month: int, start_day: int, count: int, hours: float = 8.0):
    return [DayEntryCreate(date=date(year, month, start_day + idx), hours=hours) for idx in range(count)]


def test_160_hour_hard_limit(db_session, sample_users):
    employee = sample_users["employee_a"]
    ts = upsert_timesheet_days(db_session, employee, employee, 2026, 1, build_entries(2026, 1, 1, 20, 8))
    assert sum(day.hours for day in ts.days) == 160

    with pytest.raises(HTTPException) as exc:
        upsert_timesheet_days(db_session, employee, employee, 2026, 1, [DayEntryCreate(date=date(2026, 1, 21), hours=1)])
    assert exc.value.status_code == 400
    assert "160" in exc.value.detail


def test_14_day_vacation_limit(db_session, sample_users):
    employee = sample_users["employee_a"]
    manager = sample_users["manager_a"]

    approved = create_absence(
        db_session,
        employee,
        AbsenceCreate(type=AbsenceType.VACATION, date_from=date(2026, 1, 5), date_to=date(2026, 1, 16), comment="10 weekdays"),
    )
    approve_absence(db_session, manager, approved, "Approved")

    with pytest.raises(HTTPException) as exc:
        create_absence(
            db_session,
            employee,
            AbsenceCreate(type=AbsenceType.VACATION, date_from=date(2026, 2, 2), date_to=date(2026, 2, 6), comment="Would exceed yearly limit"),
        )
    assert exc.value.status_code == 400
    assert "Vacation limit" in exc.value.detail


def test_absence_overlap_prevention(db_session, sample_users):
    employee = sample_users["employee_a"]
    create_absence(
        db_session,
        employee,
        AbsenceCreate(type=AbsenceType.SICK, date_from=date(2026, 3, 2), date_to=date(2026, 3, 3), comment="Initial request"),
    )

    with pytest.raises(HTTPException) as exc:
        create_absence(
            db_session,
            employee,
            AbsenceCreate(type=AbsenceType.VACATION, date_from=date(2026, 3, 3), date_to=date(2026, 3, 5), comment="Overlap"),
        )
    assert exc.value.status_code == 400
    assert "overlaps" in exc.value.detail


def test_absence_blocks_hour_entry(db_session, sample_users):
    employee = sample_users["employee_a"]
    manager = sample_users["manager_a"]
    absence = create_absence(
        db_session,
        employee,
        AbsenceCreate(type=AbsenceType.SICK, date_from=date(2026, 4, 7), date_to=date(2026, 4, 7), comment="Sick"),
    )
    approve_absence(db_session, manager, absence, "Approved")

    with pytest.raises(HTTPException) as exc:
        upsert_timesheet_days(db_session, employee, employee, 2026, 4, [DayEntryCreate(date=date(2026, 4, 7), hours=8)])
    assert exc.value.status_code == 400
    assert "absence blocks" in exc.value.detail.lower()


def test_timesheet_submit_reject_approve_transitions(db_session, sample_users):
    employee = sample_users["employee_a"]
    manager = sample_users["manager_a"]
    ts = upsert_timesheet_days(db_session, employee, employee, 2026, 5, build_entries(2026, 5, 1, 5, 8))

    ts = submit_timesheet(db_session, employee, ts)
    assert ts.status == TimesheetStatus.SUBMITTED

    with pytest.raises(HTTPException):
        upsert_timesheet_days(db_session, employee, employee, 2026, 5, [DayEntryCreate(date=date(2026, 5, 10), hours=4)])

    ts = reject_timesheet(db_session, manager, ts, "Please fix")
    assert ts.status == TimesheetStatus.REJECTED

    ts = upsert_timesheet_days(db_session, employee, employee, 2026, 5, [DayEntryCreate(date=date(2026, 5, 10), hours=4)])
    ts = submit_timesheet(db_session, employee, ts)
    ts = approve_timesheet(db_session, manager, ts)
    assert ts.status == TimesheetStatus.APPROVED


def test_manager_can_only_act_on_own_team_members(db_session, sample_users):
    employee = sample_users["employee_a"]
    wrong_manager = sample_users["manager_b"]
    ts = upsert_timesheet_days(db_session, employee, employee, 2026, 6, build_entries(2026, 6, 1, 5, 8))
    ts = submit_timesheet(db_session, employee, ts)

    with pytest.raises(HTTPException) as exc:
        approve_timesheet(db_session, wrong_manager, ts)
    assert exc.value.status_code == 403


def test_timesheet_blocks_manual_vacation_and_limits_manual_sick_days(db_session, sample_users):
    employee = sample_users["employee_a"]

    with pytest.raises(HTTPException) as exc:
        upsert_timesheet_days(
            db_session,
            employee,
            employee,
            2026,
            8,
            [DayEntryCreate(date=date(2026, 8, 3), hours=0, day_type=DayType.VACATION)],
        )
    assert exc.value.status_code == 400
    assert "Vacation must be requested" in exc.value.detail

    upsert_timesheet_days(
        db_session,
        employee,
        employee,
        2026,
        8,
        [DayEntryCreate(date=date(2026, 8, 4), hours=0, day_type=DayType.SICK)],
    )

    with pytest.raises(HTTPException) as exc:
        upsert_timesheet_days(
            db_session,
            employee,
            employee,
            2026,
            8,
            [DayEntryCreate(date=date(2026, 8, 5), hours=0, day_type=DayType.SICK)],
        )
    assert exc.value.status_code == 400
    assert "Only one manual sick day" in exc.value.detail


def test_actor_cannot_approve_or_reject_own_timesheet(db_session, sample_users):
    admin = sample_users["admin"]
    ts = upsert_timesheet_days(db_session, admin, admin, 2026, 9, build_entries(2026, 9, 1, 3, 8))
    ts = submit_timesheet(db_session, admin, ts)

    with pytest.raises(HTTPException) as approve_exc:
        approve_timesheet(db_session, admin, ts)
    assert approve_exc.value.status_code == 403

    with pytest.raises(HTTPException) as reject_exc:
        reject_timesheet(db_session, admin, ts, "Cannot self-review")
    assert reject_exc.value.status_code == 403


def test_admin_unlock_logs_audit_event(db_session, sample_users):
    employee = sample_users["employee_a"]
    manager = sample_users["manager_a"]
    admin = sample_users["admin"]
    ts = upsert_timesheet_days(db_session, employee, employee, 2026, 7, build_entries(2026, 7, 1, 5, 8))
    ts = submit_timesheet(db_session, employee, ts)
    ts = approve_timesheet(db_session, manager, ts)
    ts = unlock_timesheet(db_session, admin, ts, "Payroll correction")

    assert ts.status == TimesheetStatus.DRAFT
    audit = db_session.query(AuditLog).filter(AuditLog.action == "timesheet.unlocked", AuditLog.entity_id == str(ts.id)).first()
    assert audit is not None
    assert audit.details_json["reason"] == "Payroll correction"
