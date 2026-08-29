from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "edtech-lead-crm-secret-key"

# =========================================================
# DATABASE CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "crm.db")

STATUSES = [
    "New",
    "Contacted",
    "Interested",
    "Follow-up",
    "Converted",
    "Not Interested"
]


def get_db():
    """
    Create a database connection.
    Using an absolute path ensures Render and local development
    use the same database location.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Create the leads table if it does not already exist.
    Also inserts sample data when the database is empty.
    """

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

    # Add sample leads only when database is empty
    count = conn.execute(
        "SELECT COUNT(*) FROM leads"
    ).fetchone()[0]

    if count == 0:
        sample_leads = [
            (
                "Ananya Rao",
                "9876543210",
                "ananya@example.com",
                "Python Full Stack",
                "Website",
                "Interested",
                "2026-09-01",
                "Interested in weekend batch",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ),
            (
                "Rahul Kumar",
                "9876501234",
                "rahul@example.com",
                "Data Science",
                "Instagram",
                "Contacted",
                "2026-09-03",
                "Asked about course fees",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ),
            (
                "Priya Sharma",
                "9123456780",
                "priya@example.com",
                "Digital Marketing",
                "Referral",
                "New",
                "",
                "",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        ]

        conn.executemany("""
            INSERT INTO leads
            (
                name,
                phone,
                email,
                course,
                source,
                status,
                follow_up,
                notes,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_leads)

        conn.commit()

    conn.close()


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.route("/")
def dashboard():

    # Make absolutely sure the table exists
    init_db()

    conn = get_db()

    total = conn.execute(
        "SELECT COUNT(*) FROM leads"
    ).fetchone()[0]

    new_count = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = ?",
        ("New",)
    ).fetchone()[0]

    contacted_count = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = ?",
        ("Contacted",)
    ).fetchone()[0]

    interested_count = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = ?",
        ("Interested",)
    ).fetchone()[0]

    follow_up_count = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = ?",
        ("Follow-up",)
    ).fetchone()[0]

    converted_count = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = ?",
        ("Converted",)
    ).fetchone()[0]

    not_interested_count = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE status = ?",
        ("Not Interested",)
    ).fetchone()[0]

    recent_leads = conn.execute("""
        SELECT *
        FROM leads
        ORDER BY id DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        new_count=new_count,
        contacted_count=contacted_count,
        interested_count=interested_count,
        follow_up_count=follow_up_count,
        converted_count=converted_count,
        not_interested_count=not_interested_count,
        recent_leads=recent_leads
    )


# =========================================================
# LEADS PAGE
# =========================================================

@app.route("/leads")
def leads():

    init_db()

    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()

    conn = get_db()

    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if search:
        query += """
            AND (
                name LIKE ?
                OR phone LIKE ?
                OR email LIKE ?
                OR course LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY id DESC"

    rows = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    # IMPORTANT:
    # Convert sqlite3.Row objects to dictionaries.
    # This prevents:
    # TypeError: Object of type Row is not JSON serializable
    leads_data = [dict(row) for row in rows]

    return render_template(
        "leads.html",
        leads=leads_data,
        statuses=STATUSES,
        search=search,
        selected_status=status
    )


# =========================================================
# ADD LEAD
# =========================================================

@app.route("/add", methods=["POST"])
def add_lead():

    init_db()

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    course = request.form.get("course", "").strip()
    source = request.form.get("source", "").strip()
    status = request.form.get("status", "New").strip()
    follow_up = request.form.get("follow_up", "").strip()
    notes = request.form.get("notes", "").strip()

    if not name or not phone or not course:
        flash(
            "Name, phone and course are required.",
            "error"
        )
        return redirect(url_for("leads"))

    if status not in STATUSES:
        status = "New"

    conn = get_db()

    conn.execute("""
        INSERT INTO leads
        (
            name,
            phone,
            email,
            course,
            source,
            status,
            follow_up,
            notes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        phone,
        email,
        course,
        source,
        status,
        follow_up,
        notes,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    flash("Lead added successfully.", "success")

    return redirect(url_for("leads"))


# =========================================================
# EDIT LEAD
# =========================================================

@app.route("/edit/<int:lead_id>", methods=["GET", "POST"])
def edit_lead(lead_id):

    init_db()

    conn = get_db()

    lead = conn.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    if lead is None:
        conn.close()
        return "Lead not found", 404

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()
        source = request.form.get("source", "").strip()
        status = request.form.get("status", "New").strip()
        follow_up = request.form.get("follow_up", "").strip()
        notes = request.form.get("notes", "").strip()

        if not name or not phone or not course:
            flash(
                "Name, phone and course are required.",
                "error"
            )
            conn.close()
            return redirect(
                url_for("edit_lead", lead_id=lead_id)
            )

        if status not in STATUSES:
            status = "New"

        conn.execute("""
            UPDATE leads
            SET
                name = ?,
                phone = ?,
                email = ?,
                course = ?,
                source = ?,
                status = ?,
                follow_up = ?,
                notes = ?
            WHERE id = ?
        """, (
            name,
            phone,
            email,
            course,
            source,
            status,
            follow_up,
            notes,
            lead_id
        ))

        conn.commit()
        conn.close()

        flash("Lead updated successfully.", "success")

        return redirect(url_for("leads"))

    lead_data = dict(lead)

    conn.close()

    return render_template(
        "edit_lead.html",
        lead=lead_data,
        statuses=STATUSES
    )


# =========================================================
# DELETE LEAD
# =========================================================

@app.route("/delete/<int:lead_id>", methods=["POST", "GET"])
def delete_lead(lead_id):

    init_db()

    conn = get_db()

    conn.execute(
        "DELETE FROM leads WHERE id = ?",
        (lead_id,)
    )

    conn.commit()
    conn.close()

    flash("Lead deleted successfully.", "success")

    return redirect(url_for("leads"))


# =========================================================
# UPDATE STATUS
# =========================================================

@app.route("/update-status/<int:lead_id>", methods=["POST"])
def update_status(lead_id):

    init_db()

    status = request.form.get("status", "New").strip()

    if status not in STATUSES:
        return jsonify({
            "success": False,
            "error": "Invalid status"
        }), 400

    conn = get_db()

    conn.execute("""
        UPDATE leads
        SET status = ?
        WHERE id = ?
    """, (
        status,
        lead_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "status": status
    })


# =========================================================
# API - GET ALL LEADS
# =========================================================

@app.route("/api/leads")
def api_leads():

    init_db()

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM leads
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    # Convert Row -> dict
    data = [dict(row) for row in rows]

    return jsonify(data)


# =========================================================
# API - GET SINGLE LEAD
# =========================================================

@app.route("/api/leads/<int:lead_id>")
def api_single_lead(lead_id):

    init_db()

    conn = get_db()

    row = conn.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return jsonify({
            "error": "Lead not found"
        }), 404

    return jsonify(dict(row))


# =========================================================
# API - STATISTICS
# =========================================================

@app.route("/api/stats")
def api_stats():

    init_db()

    conn = get_db()

    data = {}

    for status in STATUSES:

        result = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE status = ?",
            (status,)
        ).fetchone()

        data[status] = result[0]

    total = conn.execute(
        "SELECT COUNT(*) FROM leads"
    ).fetchone()[0]

    data["total"] = total

    conn.close()

    return jsonify(data)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    try:

        init_db()

        conn = get_db()

        conn.execute(
            "SELECT 1 FROM leads LIMIT 1"
        ).fetchone()

        conn.close()

        return jsonify({
            "status": "healthy",
            "database": "connected"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================================================
# START APPLICATION
# =========================================================

# Initialize database when application starts.
init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )