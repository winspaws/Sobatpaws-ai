"""Unit tests for NotificationService - Smart Reminder System.

Run with:
    pytest tests/test_notification_service.py -v
    or
    python tests/test_notification_service.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sqlalchemy import create_engine, select, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from ekosistem_satwa.emr.models import Base, Notification, User, Pet  # noqa: E402
from ekosistem_satwa.emr.service import EMRService  # noqa: E402


def get_test_db_url() -> str:
    """Get an in-memory SQLite URL for testing."""
    return "sqlite:///:memory:"


def setup_test_service() -> tuple[EMRService, sessionmaker]:
    """Setup test EMRService with fresh in-memory database."""
    engine = create_engine(get_test_db_url(), echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create our service and inject our engine/session
    service = EMRService(database_url=get_test_db_url())
    service.engine = engine
    service._SessionLocal = TestingSessionLocal

    return service, TestingSessionLocal


def create_test_user(session: Session, **kwargs) -> User:
    """Create a test user."""
    user = User(
        name=kwargs.get("name", "Test User"),
        email=kwargs.get("email", f"test_{uuid4().hex[:8]}@example.com"),
        role=kwargs.get("role", "pet_owner"),
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def create_test_pet(session: Session, user_id: int, **kwargs) -> Pet:
    """Create a test pet."""
    pet = Pet(
        user_id=user_id,
        name=kwargs.get("name", "Fluffy"),
        species=kwargs.get("species", "cat"),
        is_active=True,
    )
    session.add(pet)
    session.flush()
    return pet


def test_create_notification_basic():
    """Test basic notification creation."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Notification Creation")
    print("=" * 60)

    service, SessionLocal = setup_test_service()

    with service.session() as session:
        user = create_test_user(session)
        pet = create_test_pet(session, user.id)

        # Create notification
        notif = service.create_notification(
            session=session,
            user_id=user.id,
            pet_id=pet.id,
            type="vaccine_reminder",
            channel="in_app",
            title="Rabies Vaccine Due Soon",
            body="Your pet's rabies vaccine is due in 7 days",
            status="pending",
            data={"vaccine_type": "rabies", "days_before": 7},
        )

        print(f"  Created notification: id={notif.id}, type={notif.type}")
        assert notif.id is not None, "Notification should have an ID"
        assert notif.type == "vaccine_reminder"
        assert notif.status == "pending"
        assert notif.user_id == user.id
        assert notif.pet_id == pet.id

        # Verify we can retrieve it
        retrieved = service.get_notification(session, notif.id)
        assert retrieved is not None
        assert retrieved.title == "Rabies Vaccine Due Soon"

        print("  ✓ Basic notification creation working!")


def test_list_notifications_by_user():
    """Test listing notifications for a user with counts."""
    print("\n" + "=" * 60)
    print("TEST 2: List Notifications by User")
    print("=" * 60)

    service, SessionLocal = setup_test_service()

    with service.session() as session:
        user1 = create_test_user(session, email="user1@example.com")
        user2 = create_test_user(session, email="user2@example.com")

        # Create notifications for user1 (2 pending, 1 read)
        for i in range(3):
            service.create_notification(
                session=session,
                user_id=user1.id,
                type="medication_reminder",
                channel="in_app",
                title=f"Medication Reminder #{i + 1}",
                body=f"Time to give medication #{i + 1}",
                status="pending" if i < 2 else "read",
            )

        # Create notification for user2
        service.create_notification(
            session=session,
            user_id=user2.id,
            type="system",
            channel="in_app",
            title="System Update",
            body="Welcome to our app!",
            status="pending",
        )

        # List user1's notifications
        notifications, total, pending_count, unread_count = service.list_notifications_by_user(
            session=session,
            user_id=user1.id,
            limit=10,
            offset=0,
        )

        print(f"  User1 notifications: total={total}, pending={pending_count}, unread={unread_count}")
        assert total == 3, "Should have 3 notifications for user1"
        assert pending_count == 2, "Should have 2 pending notifications"
        assert unread_count == 3, "All 3 should be unread (read_at is NULL for status='read' too?)"
        # Actually, our unread count counts where read_at is NULL
        # The 'read' status was set, but read_at may not be set in this test

        # Test type filtering
        notifications, total, _, _ = service.list_notifications_by_user(
            session=session,
            user_id=user1.id,
            type_filter="medication_reminder",
            limit=10,
            offset=0,
        )
        assert total == 3

        # User2 should have 1
        notifications, total, _, _ = service.list_notifications_by_user(
            session=session,
            user_id=user2.id,
            limit=10,
            offset=0,
        )
        assert total == 1

        print("  ✓ Listing notifications working!")


def test_confirm_notification_read():
    """Test confirming notification as read."""
    print("\n" + "=" * 60)
    print("TEST 3: Confirm Notification (mark as read)")
    print("=" * 60)

    service, SessionLocal = setup_test_service()

    with service.session() as session:
        user = create_test_user(session)

        notif = service.create_notification(
            session=session,
            user_id=user.id,
            type="system",
            channel="in_app",
            title="Test Notification",
            body="Please confirm you read this",
            status="pending",
        )

        session.flush()
        notif_id = notif.id

        # Confirm as read
        confirmed = service.confirm_notification(
            session=session,
            notif_id=notif_id,
            user_id=user.id,
            action="read",
        )

        assert confirmed is not None
        assert confirmed.read_at is not None
        assert confirmed.status == "read"

        print(f"  Confirmed notification: read_at={confirmed.read_at}, status={confirmed.status}")

        # Try confirming with wrong user_id
        wrong_user = service.confirm_notification(
            session=session,
            notif_id=notif_id,
            user_id=99999,
            action="read",
        )
        assert wrong_user is None, "Should not confirm for wrong user"

        print("  ✓ Confirm notification working!")


def test_confirm_notification_snooze():
    """Test snoozing a notification."""
    print("\n" + "=" * 60)
    print("TEST 4: Snooze Notification")
    print("=" * 60)

    service, SessionLocal = setup_test_service()

    with service.session() as session:
        user = create_test_user(session)

        original_time = datetime.now(timezone.utc) - timedelta(hours=1)

        notif = service.create_notification(
            session=session,
            user_id=user.id,
            type="medication_reminder",
            channel="in_app",
            title="Time for medication",
            body="Give 1 tablet now",
            scheduled_at=original_time,
            status="pending",
        )

        session.flush()
        notif_id = notif.id

        # Snooze for 60 minutes
        confirmed = service.confirm_notification(
            session=session,
            notif_id=notif_id,
            user_id=user.id,
            action="snoozed",
            snooze_minutes=60,
        )

        assert confirmed is not None
        assert confirmed.status == "scheduled"
        assert confirmed.scheduled_at > original_time

        print(f"  Snoozed notification: new scheduled_at={confirmed.scheduled_at}")

        print("  ✓ Snooze notification working!")


def test_list_upcoming_notifications():
    """Test listing upcoming scheduled notifications."""
    print("\n" + "=" * 60)
    print("TEST 5: List Upcoming Notifications")
    print("=" * 60)

    service, SessionLocal = setup_test_service()
    now = datetime.now(timezone.utc)

    with service.session() as session:
        user = create_test_user(session)

        # Create notification due in 1 hour (should appear)
        service.create_notification(
            session=session,
            user_id=user.id,
            type="medication_reminder",
            channel="in_app",
            title="Due in 1 hour",
            body="Upcoming soon",
            scheduled_at=now + timedelta(hours=1),
            status="scheduled",
        )

        # Create notification due in 12 hours (should appear in 24h window)
        service.create_notification(
            session=session,
            user_id=user.id,
            type="vaccine_reminder",
            channel="in_app",
            title="Due in 12 hours",
            body="Tomorrow",
            scheduled_at=now + timedelta(hours=12),
            status="scheduled",
        )

        # Create notification due in 30 hours (should NOT appear in 24h window)
        service.create_notification(
            session=session,
            user_id=user.id,
            type="system",
            channel="in_app",
            title="Due in 30 hours",
            body="Too far ahead",
            scheduled_at=now + timedelta(hours=30),
            status="scheduled",
        )

        # Create already sent notification (should NOT appear)
        service.create_notification(
            session=session,
            user_id=user.id,
            type="system",
            channel="in_app",
            title="Already sent",
            body="This was sent before",
            scheduled_at=now - timedelta(hours=1),
            status="sent",
        )

        # Query upcoming 24 hours
        upcoming = service.list_upcoming_notifications(
            session=session,
            user_id=user.id,
            hours_ahead=24,
            limit=10,
        )

        print(f"  Found {len(upcoming)} upcoming notifications in 24h window")
        for n in upcoming:
            print(f"    - {n.title} (scheduled: {n.scheduled_at})")

        assert len(upcoming) == 2, "Should have 2 upcoming in 24h"

        titles = [n.title for n in upcoming]
        assert "Due in 1 hour" in titles
        assert "Due in 12 hours" in titles
        assert "Due in 30 hours" not in titles
        assert "Already sent" not in titles

        # Check ordering - should be by scheduled_at ascending
        assert upcoming[0].scheduled_at < upcoming[1].scheduled_at

        print("  ✓ Upcoming notifications working!")


def test_create_vaccination_reminder():
    """Test creating vaccination reminders with H-7 and H-1 patterns."""
    print("\n" + "=" * 60)
    print("TEST 6: Vaccination Reminder Factory (H-7, H-1)")
    print("=" * 60)

    service, SessionLocal = setup_test_service()
    next_due = date.today() + timedelta(days=14)

    with service.session() as session:
        user = create_test_user(session)
        pet = create_test_pet(session, user.id)

        # H-7 reminder
        h7_reminder = service.create_vaccination_reminder(
            session=session,
            user_id=user.id,
            pet_id=pet.id,
            vaccine_type="Rabies",
            next_due_date=next_due,
            days_before=7,
        )

        print(f"  H-7 reminder: title='{h7_reminder.title}'")
        print(f"    scheduled_at: {h7_reminder.scheduled_at}")
        assert h7_reminder.type == "vaccine_reminder"
        assert h7_reminder.status == "scheduled"
        assert "7 hari" in h7_reminder.title or "7" in h7_reminder.title

        # H-1 reminder
        h1_reminder = service.create_vaccination_reminder(
            session=session,
            user_id=user.id,
            pet_id=pet.id,
            vaccine_type="Rabies",
            next_due_date=next_due,
            days_before=1,
        )

        print(f"  H-1 reminder: title='{h1_reminder.title}'")
        assert "besok" in h1_reminder.title or "1" in h1_reminder.title

        print("  ✓ Vaccination reminder factory working!")


def test_create_medication_reminder():
    """Test creating medication schedule reminders."""
    print("\n" + "=" * 60)
    print("TEST 7: Medication Reminder Factory")
    print("=" * 60)

    service, SessionLocal = setup_test_service()
    scheduled_time = datetime.now(timezone.utc) + timedelta(hours=4)

    with service.session() as session:
        user = create_test_user(session)
        pet = create_test_pet(session, user.id)

        med_reminder = service.create_medication_reminder(
            session=session,
            user_id=user.id,
            pet_id=pet.id,
            medication_name="Amoxicillin",
            dosage="1 tablet 250mg",
            scheduled_time=scheduled_time,
        )

        print(f"  Medication reminder: title='{med_reminder.title}'")
        print(f"    body: {med_reminder.body}")
        assert med_reminder.type == "medication_reminder"
        assert "Amoxicillin" in med_reminder.title
        assert "1 tablet 250mg" in med_reminder.body

        print("  ✓ Medication reminder factory working!")


def test_create_emergency_alert():
    """Test creating emergency alerts."""
    print("\n" + "=" * 60)
    print("TEST 8: Emergency Alert")
    print("=" * 60)

    service, SessionLocal = setup_test_service()

    with service.session() as session:
        user = create_test_user(session)
        pet = create_test_pet(session, user.id)

        alert = service.create_emergency_alert(
            session=session,
            user_id=user.id,
            pet_id=pet.id,
            alert_title="Emergency: Abnormal Symptoms Detected",
            alert_body="Your pet is showing severe symptoms. Please consult a vet immediately.",
        )

        print(f"  Emergency alert: type={alert.type}, channel={alert.channel}")
        assert alert.type == "emergency"
        assert alert.channel == "push"
        assert alert.status == "pending"
        assert alert.data is not None
        assert alert.data.get("urgent") == True  # noqa: E712

        print("  ✓ Emergency alert working!")


def test_create_re_engagement():
    """Test creating inactive user re-engagement reminders."""
    print("\n" + "=" * 60)
    print("TEST 9: Re-engagement Reminder (Day-7)")
    print("=" * 60)

    service, SessionLocal = setup_test_service()

    with service.session() as session:
        user = create_test_user(session)

        re_engagement = service.create_re_engagement_reminder(
            session=session,
            user_id=user.id,
            days_inactive=7,
        )

        print(f"  Re-engagement: type={re_engagement.type}, channel={re_engagement.channel}")
        print(f"    title: {re_engagement.title}")
        assert re_engagement.type == "re_engagement"
        assert re_engagement.channel == "push"
        assert re_engagement.data is not None
        assert re_engagement.data.get("days_inactive") == 7
        assert re_engagement.data.get("campaign") == "re_engagement_day_7"

        print("  ✓ Re-engagement reminder working!")


def test_create_weekly_digest():
    """Test creating weekly digest notifications."""
    print("\n" + "=" * 60)
    print("TEST 10: Weekly Digest")
    print("=" * 60)

    service, SessionLocal = setup_test_service()

    with service.session() as session:
        user = create_test_user(session)

        digest = service.create_weekly_digest(
            session=session,
            user_id=user.id,
            summary_data={
                "pet_count": 2,
                "upcoming_vaccines": 1,
                "active_medications": 3,
            },
        )

        print(f"  Weekly digest: type={digest.type}, channel={digest.channel}")
        assert digest.type == "weekly_digest"
        assert digest.channel == "email"
        assert "2" in digest.body or "1" in digest.body or "3" in digest.body

        print("  ✓ Weekly digest working!")


def run_all_tests():
    """Run all notification service tests."""
    print("\n" + "=" * 60)
    print("NOTIFICATION SERVICE TEST SUITE")
    print("=" * 60)

    all_passed = True
    tests = [
        test_create_notification_basic,
        test_list_notifications_by_user,
        test_confirm_notification_read,
        test_confirm_notification_snooze,
        test_list_upcoming_notifications,
        test_create_vaccination_reminder,
        test_create_medication_reminder,
        test_create_emergency_alert,
        test_create_re_engagement,
        test_create_weekly_digest,
    ]

    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n  ✗ FAILED: {test_func.__name__}")
            print(f"    Error: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED! ✓")
    else:
        print("SOME TESTS FAILED! ✗")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
