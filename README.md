# Server Monitoring Dashboard

A Flask-based dashboard for monitoring and managing server infrastructure for SMP / SCMS environments. The project provides a clean admin-style UI with live summary cards, server inventory, disk monitoring, team details, and a monthly shift roster.

## Preview

![Server Monitoring Dashboard Preview](docs/dashboard-preview.svg)

## Demo Highlights

- Overview page with server health KPIs
- Inventory management with search and environment filters
- Disk monitoring with warning and critical indicators
- Team details and monthly roster planning
- Flask-powered API endpoints serving dashboard data dynamically

## Features

- Dashboard overview with KPI cards
- Server inventory table with filtering and search
- Disk usage monitoring with severity indicators
- Team details section
- Monthly shift roster view
- Flask JSON API endpoints for frontend data loading
- Responsive UI using HTML, CSS, and JavaScript

## Project Structure

```text
flask_dashboard/
├── app.py
├── requirements.txt
├── README.md
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── templates/
    └── index.html
```

## Tech Stack

- Python
- Flask
- HTML5
- CSS3
- JavaScript
- Font Awesome
- Google Fonts

## Setup Instructions

1. Clone or download the project.
2. Open a terminal in the project folder:

```bash
cd /Users/dikshashahi/Downloads/flask_dashboard
```

3. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the Flask app:

```bash
python app.py
```

6. Open the app in your browser:

```text
http://127.0.0.1:5000
```

## Demo Walkthrough

1. Launch the Flask server with `python app.py`
2. Open `http://127.0.0.1:5000`
3. Use the left sidebar to switch between Overview, Server Inventory, Disk Monitoring, Team Details, and Roster
4. Try the search and environment filters in the inventory table
5. Review disk utilization severity states from the monitoring section

## API Endpoints

- `GET /` - Render the main dashboard page
- `GET /api/summary` - Dashboard summary metrics
- `GET /api/inventory` - Full server inventory
- `GET /api/disk` - Disk usage data with severity labels
- `GET /api/team` - Team member data
- `GET /api/roster` - Monthly shift roster data

## Notes

- The project currently uses in-memory sample data in `app.py`.
- This makes it easy to demo, test, and extend without setting up a database first.
- In a production version, the data layer can be moved to JSON, Excel, or a database-backed service.

## Future Improvements

- Add authentication for admin users
- Persist data in a database
- Add charts for server utilization trends
- Export reports to CSV or PDF
- Add role-based access control

## Author

Diksha Shahi
