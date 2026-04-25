# Server Monitoring Dashboard

A Flask-based dashboard for tracking server health, disk utilization, environment inventory, team ownership, and shift planning. The project is built as a polished admin-style interface backed by lightweight JSON APIs, making it a good starting point for infrastructure monitoring demos and operations dashboards.

## 🔗 Live Demo
(https://server-monitoring-dashboard-dbwz.onrender.com)
## Preview

![Server Monitoring Dashboard Preview](docs/dashboard-preview.svg]
> ⚠️ Hosted on Render free tier — may take 30–60 seconds to wake up on first visit.
## Highlights

- KPI summary cards for infrastructure status at a glance
- Inventory table with search and environment filters
- Disk usage view with warning and critical thresholds
- Team details and monthly roster planning sections
- Flask API endpoints that serve data to a responsive frontend

## Tech Stack

- Python
- Flask
- HTML5
- CSS3
- JavaScript

## Project Structure

```text
server_monitoring_dashboard/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── docs/
    └── dashboard-preview.svg
```

## How It Works

- `app.py` serves the dashboard shell and exposes JSON endpoints for each section.
- The frontend loads summary, inventory, disk, team, and roster data dynamically.
- Sample in-memory data keeps the project easy to run locally without database setup.

## Local Setup

```bash
git clone https://github.com/Diksha159457/server_monitoring_dashboard.git
cd server_monitoring_dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Deployment

This repository includes a `render.yaml` blueprint for Render.

1. Create a new Blueprint deployment in Render.
2. Point Render to this GitHub repository.
3. Render will install dependencies from `requirements.txt` and start the app with Gunicorn.

Once deployed, add the live URL near the top of this README for recruiters.

## API Endpoints

- `GET /` renders the main dashboard
- `GET /api/summary` returns KPI counts
- `GET /api/inventory` returns server inventory records
- `GET /api/disk` returns disk usage with severity labels
- `GET /api/team` returns team ownership data
- `GET /api/roster` returns the generated shift roster

## Resume Value

This project demonstrates backend routing, frontend state rendering, API-driven UI composition, and practical dashboard design for operational tooling.

## Future Improvements

- Persist data in a database or external service
- Add authentication and role-based access control
- Add charts for utilization trends over time
- Export reports to CSV or PDF

## License

MIT. See [LICENSE](LICENSE).
