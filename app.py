from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "crm.db"

STATUSES = ["New", "Contacted", "Interested", "Follow-up", "Converted", "Not Interested"]
COURSES = ["Python Full Stack", "Data Science", "Web Development", "Digital Marketing", "CloudComputing"]

def calculate_lead_score(lead):
    score = 0

    # Status indicates buying intent
    status_points = {
        "New": 20,
        "Contacted": 35,
        "Interested": 60,
        "Follow-up": 75,
        "Converted": 100,
        "Not Interested": 5
    }

    score += status_points.get(lead["status"], 0)

    # Follow-up requirement indicates an active sales opportunity
    if lead["follow_up"]:
        score += 15

    # Referral leads generally have stronger initial trust
    if lead["source"] == "Referral":
        score += 10
    elif lead["source"] in ["Website", "Instagram", "LinkedIn"]:
        score += 5

    score = min(score, 100)

    if score >= 80:
        category = "Hot"
    elif score >= 50:
        category = "Warm"
    else:
        category = "Cold"

    return score, category

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            course TEXT NOT NULL,
            source TEXT,
            status TEXT NOT NULL DEFAULT 'New',
            follow_up TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    if count == 0:
        sample = [
            ("Ananya Rao", "9876543210", "ananya@example.com", "Python Full Stack", "Website", "Interested", "2026-09-01", "Asked about placement support."),
            ("Rahul Kumar", "9876501234", "rahul@example.com", "Data Science", "Instagram", "Contacted", "2026-08-30", "Requested course details."),
            ("Priya Sharma", "9123456780", "priya@example.com", "Digital Marketing", "Referral", "New", "", "Interested in weekend batches.")
        ]
        for row in sample:
            conn.execute("""
                INSERT INTO leads
                (name, phone, email, course, source, status, follow_up, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*row, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    conn.close()

@app.route("/")
def dashboard():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    converted = conn.execute("SELECT COUNT(*) FROM leads WHERE status='Converted'").fetchone()[0]
    interested = conn.execute("SELECT COUNT(*) FROM leads WHERE status='Interested'").fetchone()[0]
    followups = conn.execute("""
        SELECT COUNT(*) FROM leads
        WHERE follow_up != '' AND follow_up <= date('now', '+7 day')
        AND status NOT IN ('Converted', 'Not Interested')
    """).fetchone()[0]
    conversion_rate = round((converted / total) * 100, 1) if total else 0

    status_data = []
    for status in STATUSES:
        count = conn.execute("SELECT COUNT(*) FROM leads WHERE status=?", (status,)).fetchone()[0]
        status_data.append({"status": status, "count": count})

    recent = conn.execute("SELECT * FROM leads ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    return render_template("dashboard.html", total=total, converted=converted,
                           interested=interested, followups=followups,
                           conversion_rate=conversion_rate,
                           status_data=status_data, recent=recent)

@app.route("/leads")
def leads():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    conn = get_db()

    query = "SELECT * FROM leads WHERE 1=1"
    params = []
    if search:
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ? OR course LIKE ?)"
        term = f"%{search}%"
        params += [term, term, term, term]
    if status:
        query += " AND status=?"
        params.append(status)
    query += " ORDER BY id DESC"

    rows = conn.execute(query, params).fetchall()
    rows = [dict(row) for row in rows]

    for lead in rows:
        lead["score"], lead["category"] = calculate_lead_score(lead)
    conn.close()
    return render_template("leads.html", leads=rows, statuses=STATUSES,
                           courses=COURSES, search=search, selected_status=status)

@app.route("/leads/add", methods=["POST"])
def add_lead():
    data = request.form
    conn = get_db()
    conn.execute("""
        INSERT INTO leads
        (name, phone, email, course, source, status, follow_up, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"], data["phone"], data.get("email", ""),
        data["course"], data.get("source", ""), data.get("status", "New"),
        data.get("follow_up", ""), data.get("notes", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()
    return redirect(url_for("leads"))

@app.route("/leads/edit/<int:lead_id>", methods=["POST"])
def update_lead(lead_id):
    data = request.form
    conn = get_db()
    conn.execute("""
        UPDATE leads SET name=?, phone=?, email=?, course=?, source=?,
        status=?, follow_up=?, notes=? WHERE id=?
    """, (
        data["name"], data["phone"], data.get("email", ""),
        data["course"], data.get("source", ""), data.get("status", "New"),
        data.get("follow_up", ""), data.get("notes", ""), lead_id
    ))
    conn.commit()
    conn.close()
    return redirect(url_for("leads"))

@app.route("/leads/delete/<int:lead_id>", methods=["POST"])
def delete_lead(lead_id):
    conn = get_db()
    conn.execute("DELETE FROM leads WHERE id=?", (lead_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("leads"))

@app.route("/api/stats")
def api_stats():
    conn = get_db()
    data = {}
    for status in STATUSES:
        data[status] = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE status=?", (status,)
        ).fetchone()[0]
    conn.close()
    return jsonify(data)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
