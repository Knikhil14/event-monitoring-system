import os

import requests
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

QUERY_API_URL = os.getenv("QUERY_API_URL", "http://event-query-api-service")

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="10">
  <title>Event Monitoring Dashboard</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #0f172a; color: #e5e7eb; }
    header { padding: 24px 32px; background: #111827; border-bottom: 1px solid #334155; }
    main { padding: 24px 32px; display: grid; gap: 24px; }
    h1 { margin: 0; font-size: 28px; }
    h2 { margin: 0 0 12px; font-size: 18px; }
    table { width: 100%; border-collapse: collapse; background: #111827; }
    th, td { padding: 12px; border-bottom: 1px solid #334155; text-align: left; }
    th { color: #93c5fd; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }
    .card { background: #111827; border: 1px solid #334155; border-radius: 8px; padding: 16px; }
    .count { font-size: 32px; font-weight: 700; margin-top: 8px; }
    .empty { color: #94a3b8; }
  </style>
</head>
<body>
  <header><h1>Event Monitoring Dashboard</h1></header>
  <main>
    <section>
      <h2>Severity Counts</h2>
      <div class="grid">
        {% for item in stats.severity_counts %}
        <div class="card">
          <div>{{ item.severity }}</div>
          <div class="count">{{ item.count }}</div>
        </div>
        {% else %}
        <div class="empty">No processed events yet.</div>
        {% endfor %}
      </div>
    </section>
    <section>
      <h2>Recent Processed Events</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>Type</th><th>Source</th><th>Severity</th><th>Status</th><th>Message</th></tr>
        </thead>
        <tbody>
          {% for event in events %}
          <tr>
            <td>{{ event.id }}</td>
            <td>{{ event.event_type }}</td>
            <td>{{ event.source }}</td>
            <td>{{ event.severity }}</td>
            <td>{{ event.status }}</td>
            <td>{{ event.message }}</td>
          </tr>
          {% else %}
          <tr><td colspan="6" class="empty">Send a test event to populate the dashboard.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


@app.get("/health")
def health_check():
    return jsonify({"status": "healthy", "service": "dashboard"})


@app.get("/")
def index():
    try:
        stats = requests.get(f"{QUERY_API_URL}/events/stats", timeout=5).json()
        events = requests.get(f"{QUERY_API_URL}/events?limit=25", timeout=5).json()
    except requests.RequestException:
        stats = {"severity_counts": []}
        events = {"events": []}
    return render_template_string(
        HTML,
        stats=stats,
        events=events.get("events", []),
    )
