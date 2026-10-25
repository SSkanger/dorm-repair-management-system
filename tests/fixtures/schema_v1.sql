BEGIN IMMEDIATE;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE
        CHECK (length(trim(username)) BETWEEN 1 AND 50),
    password_hash TEXT NOT NULL
        CHECK (length(password_hash) > 20),
    display_name TEXT NOT NULL
        CHECK (length(trim(display_name)) BETWEEN 1 AND 50),
    role TEXT NOT NULL
        CHECK (role IN ('student', 'repairer')),
    created_at TEXT NOT NULL
        CHECK (length(created_at) >= 20)
);

CREATE TABLE repair_tickets (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    assignee_id INTEGER REFERENCES users(id) ON DELETE RESTRICT,
    building TEXT NOT NULL
        CHECK (length(trim(building)) BETWEEN 1 AND 30),
    room_number TEXT NOT NULL
        CHECK (length(trim(room_number)) BETWEEN 1 AND 20),
    category TEXT NOT NULL
        CHECK (category IN ('照明', '水管', '门锁', '网络', '其他')),
    description TEXT NOT NULL
        CHECK (length(trim(description)) BETWEEN 5 AND 1000),
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    assigned_at TEXT,
    started_at TEXT,
    completed_at TEXT,
    confirmed_at TEXT,
    rating INTEGER
        CHECK (rating IS NULL OR (typeof(rating) = 'integer' AND rating BETWEEN 1 AND 5)),
    review_text TEXT
        CHECK (review_text IS NULL OR (rating IS NOT NULL AND length(trim(review_text)) BETWEEN 1 AND 500)),
    reviewed_at TEXT,
    submission_token TEXT NOT NULL,
    UNIQUE (student_id, submission_token),
    CHECK (assignee_id IS NULL OR assignee_id <> student_id),
    CHECK (
        (status = 'PENDING' AND assignee_id IS NULL AND assigned_at IS NULL AND started_at IS NULL AND completed_at IS NULL)
        OR (status = 'ACCEPTED' AND assignee_id IS NOT NULL AND assigned_at IS NOT NULL AND started_at IS NULL AND completed_at IS NULL)
        OR (status = 'IN_PROGRESS' AND assignee_id IS NOT NULL AND assigned_at IS NOT NULL AND started_at IS NOT NULL AND completed_at IS NULL)
        OR (status = 'COMPLETED' AND assignee_id IS NOT NULL AND assigned_at IS NOT NULL AND started_at IS NOT NULL AND completed_at IS NOT NULL)
    ),
    CHECK (confirmed_at IS NULL OR status = 'COMPLETED'),
    CHECK (rating IS NULL OR (status = 'COMPLETED' AND confirmed_at IS NOT NULL)),
    CHECK ((rating IS NULL AND reviewed_at IS NULL) OR (rating IS NOT NULL AND reviewed_at IS NOT NULL)),
    CHECK (review_text IS NULL OR rating IS NOT NULL),
    CHECK (updated_at >= created_at),
    CHECK (assigned_at IS NULL OR assigned_at >= created_at),
    CHECK (started_at IS NULL OR started_at >= assigned_at),
    CHECK (completed_at IS NULL OR completed_at >= started_at),
    CHECK (confirmed_at IS NULL OR confirmed_at >= completed_at),
    CHECK (reviewed_at IS NULL OR reviewed_at >= confirmed_at)
);

CREATE INDEX idx_tickets_student_created
    ON repair_tickets (student_id, created_at DESC, id DESC);
CREATE INDEX idx_tickets_assignee_created
    ON repair_tickets (assignee_id, created_at DESC, id DESC);
CREATE INDEX idx_tickets_status_created
    ON repair_tickets (status, created_at DESC, id DESC);

PRAGMA user_version = 1;
COMMIT;
