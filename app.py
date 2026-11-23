from pathlib import Path
import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deployment")
DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).with_name("voloveteer.db")))

INTERESTS = ["Animals", "Environment", "Arts", "Food", "Tutoring", "Community"]


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_db() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                date_text TEXT NOT NULL,
                organizer TEXT NOT NULL,
                contact_email TEXT,
                registration_url TEXT,
                active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                FOREIGN KEY (event_id) REFERENCES opportunities(id)
            );

            CREATE TABLE IF NOT EXISTS event_signups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                browser_session_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(event_id, browser_session_id),
                FOREIGN KEY (event_id) REFERENCES opportunities(id)
            );
        """)


def seed_db():
    """Seed local demo opportunities only when the table is empty."""
    with get_db() as connection:
        if connection.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]:
            return
        connection.executemany("""
            INSERT INTO opportunities
            (title, category, description, location, date_text, organizer,
             contact_email, registration_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("Park Cleanup", "Environment", "Pick up litter and care for neighborhood green spaces.", "Riverside Park", "Saturday, 9:00 AM–12:00 PM", "Green Neighbors", "demo@example.org", None),
            ("Animal Shelter Helper", "Animals", "Prepare supplies and support shelter staff.", "City Animal Shelter", "Sunday, 10:00 AM–1:00 PM", "City Animal Shelter", "demo@example.org", None),
            ("Community Mural Day", "Arts", "Assist local artists with a community mural project.", "Eastside Community Center", "Saturday, 11:00 AM–2:00 PM", "Eastside Arts Group", "demo@example.org", None),
            ("Food Bank Sorting", "Food", "Sort donated food and prepare pantry boxes.", "Community Food Hub", "Wednesday, 4:00 PM–6:00 PM", "Community Food Hub", "demo@example.org", None),
            ("Homework Club", "Tutoring", "Help younger students with reading and homework.", "Northside Library", "Thursday, 3:30 PM–5:00 PM", "Northside Library", "demo@example.org", None),
            ("Neighborhood Welcome Table", "Community", "Welcome visitors and help with a family community event.", "Main Street Plaza", "Saturday, 10:00 AM–1:00 PM", "Main Street Association", "demo@example.org", None),
        ])


init_db()
seed_db()


def get_feedback_stats(event_id):
    with get_db() as connection:
        row = connection.execute(
            "SELECT AVG(rating) AS average, COUNT(*) AS count FROM feedback WHERE event_id = ?",
            (event_id,),
        ).fetchone()
    average = round(row["average"], 1) if row["average"] is not None else None
    return average, row["count"]


def find_event(event_id):
    with get_db() as connection:
        return connection.execute(
            "SELECT * FROM opportunities WHERE id = ? AND active = 1", (event_id,)
        ).fetchone()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/survey", methods=["GET", "POST"])
def survey():
    if request.method == "POST":
        selected = [item for item in request.form.getlist("interests") if item in INTERESTS]
        session["interests"] = selected
        flash("Your interests have been saved for this browser session.")
        return redirect(url_for("opportunities"))
    return render_template("survey.html", interests=INTERESTS, selected=session.get("interests", []))


@app.route("/opportunities")
def opportunities():
    interests = session.get("interests", [])
    with get_db() as connection:
        events = connection.execute(
            "SELECT * FROM opportunities WHERE active = 1 ORDER BY date_text"
        ).fetchall()

    ranked_events = []
    for event in events:
        average, count = get_feedback_stats(event["id"])
        ranked_events.append({
            "row": event,
            "matched": event["category"] in interests,
            "rating": average,
            "rating_count": count,
        })
    ranked_events.sort(key=lambda item: (item["matched"], item["rating"] or 0), reverse=True)

    browser_id = session.get("browser_id")
    registered = set()
    if browser_id:
        with get_db() as connection:
            registered = {row["event_id"] for row in connection.execute(
                "SELECT event_id FROM event_signups WHERE browser_session_id = ?",
                (browser_id,),
            )}

    return render_template(
        "opportunities.html",
        events=ranked_events,
        interests=interests,
        registered=registered,
    )


@app.post("/sign-up/<int:event_id>")
def sign_up(event_id):
    event = find_event(event_id)
    if not event:
        return "Opportunity not found", 404

    import uuid
    browser_id = session.setdefault("browser_id", uuid.uuid4().hex)
    with get_db() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO event_signups (event_id, browser_session_id) VALUES (?, ?)",
            (event_id, browser_id),
        )

    flash("This opportunity is saved in this browser. It has not sent your information to the organizer.")
    return redirect(url_for("opportunities"))


@app.route("/feedback/<int:event_id>", methods=["GET", "POST"])
def feedback(event_id):
    event = find_event(event_id)
    if not event:
        return "Opportunity not found", 404

    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", ""))
        except ValueError:
            rating = 0
        if rating not in range(1, 6):
            flash("Please choose a rating from 1 to 5.")
        else:
            with get_db() as connection:
                connection.execute(
                    "INSERT INTO feedback (event_id, rating) VALUES (?, ?)",
                    (event_id, rating),
                )
            flash("Thanks! Your anonymous rating will help improve recommendations.")
            return redirect(url_for("opportunities"))

    return render_template("feedback.html", event=event)


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
