"""SQLite inventory — owns the DB schema and all read/write operations."""
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "inventory.db")


def _db_path() -> str:
    return os.path.normpath(DB_PATH)


@contextmanager
def _conn():
    con = sqlite3.connect(_db_path())
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init(all_codes: set[str]) -> None:
    """Create tables and seed every known sticker as 'missing'."""
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS inventory (
                code        TEXT PRIMARY KEY,
                status      TEXT NOT NULL DEFAULT 'missing',
                quantity    INTEGER NOT NULL DEFAULT 0,
                source_img  TEXT,
                updated_at  TEXT
            );
            CREATE TABLE IF NOT EXISTS scan_log (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                filename      TEXT NOT NULL,
                image_type    TEXT,
                team_code     TEXT,
                slots_found   INTEGER DEFAULT 0,
                raw_response  TEXT,
                processed_at  TEXT
            );
        """)
        existing = {row[0] for row in con.execute("SELECT code FROM inventory")}
        missing = all_codes - existing
        now = _now()
        con.executemany(
            "INSERT INTO inventory (code, status, quantity, updated_at) VALUES (?, 'missing', 0, ?)",
            [(code, now) for code in missing],
        )
        if missing:
            print(f"  Seeded {len(missing)} new stickers as 'missing'")


def upsert_owned(code: str, source_img: str) -> None:
    """Mark a sticker as owned in album. Never downgrades from 'owned'."""
    with _conn() as con:
        existing = con.execute("SELECT status FROM inventory WHERE code=?", (code,)).fetchone()
        if existing and existing["status"] == "owned":
            return
        con.execute(
            """INSERT INTO inventory (code, status, quantity, source_img, updated_at)
               VALUES (?, 'owned', 1, ?, ?)
               ON CONFLICT(code) DO UPDATE SET
                 status=excluded.status,
                 quantity=excluded.quantity,
                 source_img=excluded.source_img,
                 updated_at=excluded.updated_at
               WHERE status != 'owned'""",
            (code, source_img, _now()),
        )


def upsert_extra(code: str, source_img: str) -> None:
    """Increment extra count for a duplicate sticker."""
    with _conn() as con:
        row = con.execute("SELECT status, quantity FROM inventory WHERE code=?", (code,)).fetchone()
        if row:
            new_qty = (row["quantity"] or 0) + 1
            new_status = "extra" if row["status"] == "missing" else row["status"]
            con.execute(
                "UPDATE inventory SET status=?, quantity=?, source_img=?, updated_at=? WHERE code=?",
                (new_status, new_qty, source_img, _now(), code),
            )
        else:
            con.execute(
                "INSERT INTO inventory (code, status, quantity, source_img, updated_at) VALUES (?, 'extra', 1, ?, ?)",
                (code, source_img, _now()),
            )


def mark_team_missing(team_code: str, codes_in_team: list[str]) -> None:
    """For a freshly scanned album page, mark unscanned team slots as missing (only if not already owned)."""
    with _conn() as con:
        for code in codes_in_team:
            row = con.execute("SELECT status FROM inventory WHERE code=?", (code,)).fetchone()
            if not row or row["status"] == "missing":
                con.execute(
                    "INSERT INTO inventory (code, status, quantity, updated_at) VALUES (?, 'missing', 0, ?) "
                    "ON CONFLICT(code) DO UPDATE SET updated_at=excluded.updated_at WHERE status='missing'",
                    (code, _now()),
                )


def log_scan(filename: str, image_type: str, team_code: str, slots_found: int, raw: str) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO scan_log (filename, image_type, team_code, slots_found, raw_response, processed_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (filename, image_type, team_code, slots_found, raw, _now()),
        )


def stats() -> dict:
    with _conn() as con:
        rows = con.execute(
            "SELECT status, COUNT(*) as cnt, SUM(quantity) as qty FROM inventory GROUP BY status"
        ).fetchall()
    result = {"owned": 0, "missing": 0, "extra": 0, "extra_qty": 0, "total": 0}
    for row in rows:
        s = row["status"]
        result[s] = row["cnt"]
        if s == "extra":
            result["extra_qty"] = row["qty"] or 0
    result["total"] = result["owned"] + result["missing"] + result["extra"]
    return result


def missing_by_team(team_code: str) -> list[str]:
    with _conn() as con:
        rows = con.execute(
            "SELECT code FROM inventory WHERE status='missing' AND code LIKE ? ORDER BY code",
            (f"{team_code}%",),
        ).fetchall()
    return [r["code"] for r in rows]


def all_missing() -> list[str]:
    with _conn() as con:
        rows = con.execute(
            "SELECT code FROM inventory WHERE status='missing' ORDER BY code"
        ).fetchall()
    return [r["code"] for r in rows]


def all_extras() -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT code, quantity FROM inventory WHERE status='extra' ORDER BY code"
        ).fetchall()
    return [{"code": r["code"], "qty": r["quantity"]} for r in rows]


def owned_codes() -> set[str]:
    with _conn() as con:
        rows = con.execute("SELECT code FROM inventory WHERE status IN ('owned','extra')").fetchall()
    return {r["code"] for r in rows}


def team_progress(team_code: str) -> dict:
    with _conn() as con:
        rows = con.execute(
            "SELECT status, COUNT(*) as cnt FROM inventory WHERE code LIKE ? GROUP BY status",
            (f"{team_code}%",),
        ).fetchall()
    d = {"owned": 0, "missing": 0, "extra": 0}
    for row in rows:
        d[row["status"]] = row["cnt"]
    d["total"] = d["owned"] + d["missing"] + d["extra"]
    d["have"] = d["owned"] + d["extra"]
    return d


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")
