import calendar
import os
from contextlib import contextmanager
from datetime import datetime, date, timedelta

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Text,
    Enum,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker, Session

from app.config import DATABASE_URL


# Ensure the data directory exists for SQLite
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    fb_ad_account_id = Column(String(100), nullable=True)
    fb_token = Column(Text, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    budget_config = relationship("ClientBudgetConfig", back_populates="client", uselist=False, cascade="all, delete-orphan")
    snapshots = relationship("AccountDailySnapshot", back_populates="client", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="client", foreign_keys="Task.client_id")
    notes = relationship("Note", back_populates="client", foreign_keys="Note.client_id")
    alert_rules = relationship("AlertRule", back_populates="client", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="client", cascade="all, delete-orphan")


class ClientBudgetConfig(Base):
    __tablename__ = "client_budget_configs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, unique=True)
    daily_limit = Column(Float, default=0.0)
    monthly_limit = Column(Float, default=0.0)
    alert_threshold_pct = Column(Float, default=80.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="budget_config")


class AccountDailySnapshot(Base):
    __tablename__ = "account_daily_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    spend = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="snapshots")


class TaskLabel(Base):
    __tablename__ = "task_labels"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7), default="#6c757d")  # hex color


class TaskLabelAssoc(Base):
    __tablename__ = "task_label_assoc"

    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    label_id = Column(Integer, ForeignKey("task_labels.id"), primary_key=True)


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="comments")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    section = Column(String(100), nullable=True)          # e.g. "Para fazer", "Fazendo", "Feito"
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")         # pending / done
    source = Column(String(20), default="manual")          # manual / whatsapp
    priority = Column(Integer, default=4)                  # 1=red, 2=orange, 3=blue, 4=none
    due_date = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)
    start_time = Column(String(5), nullable=True)      # "HH:MM" format
    duration_minutes = Column(Integer, nullable=True)   # e.g. 30, 60, 90
    recurrence = Column(String(100), nullable=True)    # e.g. "daily", "weekly:1", "monthly:15", "weekdays"
    recurrence_end = Column(Date, nullable=True)        # optional end date for recurrence
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    client = relationship("Client", back_populates="tasks", foreign_keys=[client_id])
    subtasks = relationship(
        "Task",
        primaryjoin="Task.parent_id == Task.id",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="select",
    )
    parent = relationship(
        "Task",
        primaryjoin="Task.parent_id == Task.id",
        back_populates="subtasks",
        remote_side="Task.id",
        lazy="select",
    )
    comments = relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at",
    )
    labels = relationship(
        "TaskLabel",
        secondary="task_label_assoc",
        lazy="select",
    )


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="notes", foreign_keys=[client_id])


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    rule_type = Column(String(50), nullable=False)  # e.g. "daily_budget", "monthly_budget"
    threshold = Column(Float, nullable=False)
    notify_whatsapp = Column(Boolean, default=False)
    active = Column(Boolean, default=True)

    client = relationship("Client", back_populates="alert_rules")
    alerts = relationship("Alert", back_populates="rule", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    message = Column(Text, nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)

    client = relationship("Client", back_populates="alerts")
    rule = relationship("AlertRule", back_populates="alerts")


def init_db():
    """Create all tables and run column migrations for existing databases."""
    Base.metadata.create_all(bind=engine)
    _migrate_tasks_columns()


def _migrate_tasks_columns():
    """Add new columns to tasks table if they don't exist (SQLite ALTER TABLE)."""
    migrations = [
        "ALTER TABLE tasks ADD COLUMN parent_id INTEGER REFERENCES tasks(id)",
        "ALTER TABLE tasks ADD COLUMN section VARCHAR(100)",
        "ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 4",
        "ALTER TABLE tasks ADD COLUMN due_date DATE",
        "ALTER TABLE tasks ADD COLUMN deadline DATE",
        "ALTER TABLE tasks ADD COLUMN completed_at DATETIME",
        "ALTER TABLE tasks ADD COLUMN start_time VARCHAR(5)",
        "ALTER TABLE tasks ADD COLUMN duration_minutes INTEGER",
        "ALTER TABLE tasks ADD COLUMN recurrence VARCHAR(100)",
        "ALTER TABLE tasks ADD COLUMN recurrence_end DATE",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(__import__("sqlalchemy").text(sql))
                conn.commit()
            except Exception:
                # Column already exists — safe to ignore
                pass


@contextmanager
def get_session() -> Session:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_next_due_date(current_due: date, recurrence: str) -> date:
    """Calculate next due date based on recurrence rule."""
    if recurrence == "daily":
        return current_due + timedelta(days=1)
    if recurrence == "weekdays":
        d = current_due + timedelta(days=1)
        while d.weekday() >= 5:
            d += timedelta(days=1)
        return d
    if recurrence == "weekly":
        return current_due + timedelta(weeks=1)
    if recurrence.startswith("weekly:"):
        # weekly:N where N is weekday (0=Mon..6=Sun)
        target_weekday = int(recurrence.split(":")[1])
        d = current_due + timedelta(days=1)
        while d.weekday() != target_weekday:
            d += timedelta(days=1)
        return d
    if recurrence == "monthly":
        # same day next month
        month = current_due.month + 1 if current_due.month < 12 else 1
        year = current_due.year + (1 if current_due.month == 12 else 0)
        last_day = calendar.monthrange(year, month)[1]
        day = min(current_due.day, last_day)
        return date(year, month, day)
    if recurrence.startswith("monthly:"):
        day_num = int(recurrence.split(":")[1])
        month = current_due.month + 1 if current_due.month < 12 else 1
        year = current_due.year + (1 if current_due.month == 12 else 0)
        last_day = calendar.monthrange(year, month)[1]
        day_num = min(day_num, last_day)
        return date(year, month, day_num)
    return current_due + timedelta(days=1)


def complete_recurring_task(task_id: int, session) -> bool:
    """Mark task done and create next occurrence if recurring. Returns True if next was created."""
    task = session.get(Task, task_id)
    if not task or not task.recurrence:
        return False
    task.status = "done"
    task.completed_at = datetime.utcnow()
    next_due = get_next_due_date(task.due_date or date.today(), task.recurrence)
    if task.recurrence_end and next_due > task.recurrence_end:
        return False
    new_task = Task(
        title=task.title,
        description=task.description,
        client_id=task.client_id,
        section=task.section,
        priority=task.priority,
        due_date=next_due,
        deadline=None,
        start_time=task.start_time,
        duration_minutes=task.duration_minutes,
        recurrence=task.recurrence,
        recurrence_end=task.recurrence_end,
        status="pending",
        source="manual",
        created_at=datetime.utcnow(),
    )
    session.add(new_task)
    session.flush()
    # Copy labels
    for label in task.labels:
        session.add(TaskLabelAssoc(task_id=new_task.id, label_id=label.id))
    return True
