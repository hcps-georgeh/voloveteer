# VoLoveTeer

A Flask prototype that helps students discover local volunteering opportunities matched to their interests.

## Features

- Interest survey
- Interest-based event ranking
- Real opportunity storage in SQLite
- Browser-based saved interest and sign-up state
- Anonymous 1–5 event feedback
- Feedback-informed ranking
- Responsive, accessible interface

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**.

## Add real opportunities

Use `manage_db.py` or the SQLite shell to create opportunities in `voloveteer.db`:

```sql
INSERT INTO opportunities
(title, category, description, location, date_text, organizer, contact_email, registration_url)
VALUES
('River Cleanup', 'Environment', 'Remove litter and restore local riverbanks.',
 'Riverside Park', 'Saturday, 9:00 AM–12:00 PM', 'Green Neighbors',
 'organizer@example.org', 'https://example.org/register');
```

Only publish opportunities from verified organizations. Confirm dates, age requirements, accessibility, and accurate contact details before deployment.

## Deploy

Set `SECRET_KEY` and optionally `DATABASE_PATH` as environment variables:

```bash
export SECRET_KEY='a-long-random-secret'
export DATABASE_PATH='/var/data/voloveteer.db'
export FLASK_DEBUG='0'
```

The demo currently stores feedback and saved opportunities but does not send email or text reminders or transmit personal details to organizers. Those require a consent-aware account system and approved messaging provider.

## Safety

- Do not publish unverified events or scraped private listings.
- Obtain organizer permission before publishing contact details.
- Add parental/guardian consent and age rules before collecting student account data.
- Use HTTPS in production.
- Back up the SQLite database and restrict administrator access.

## License

MIT
