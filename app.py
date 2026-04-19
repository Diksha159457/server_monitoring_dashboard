# ─────────────────────────────────────────────────────────────────────────────
# app.py  —  Flask Backend for the Server Monitoring & Management Dashboard
# Project  : SMP / SCMS Server Monitoring System
# Institute: IET, DDU Gorakhpur University, Dept. of Information Technology
# SRS Ref  : §3.1 (Layer 2 – Application Server), §5.1–§5.5
# ─────────────────────────────────────────────────────────────────────────────

from flask import Flask, render_template, jsonify   # Flask: web framework core; render_template: renders HTML files from /templates; jsonify: converts Python dicts/lists to JSON HTTP responses
import json                                          # json: used for serialising Python data structures (though jsonify handles most cases)
from datetime import datetime                        # datetime: provides current date/time used to stamp the dashboard header

# ── Application Factory ───────────────────────────────────────────────────────
app = Flask(__name__)           # Creates the Flask application instance; __name__ tells Flask where to find templates & static files
app.config['DEBUG'] = True      # Enables debug mode so the server auto-reloads on code changes and shows detailed error pages

# ─────────────────────────────────────────────────────────────────────────────
# DATA LAYER  —  SRS §3.3 (Data Source Layer)
# In production these would be read from JSON files / an Excel sheet via pandas.
# Here they are declared as Python lists of dicts that mirror the SRS data model.
# ─────────────────────────────────────────────────────────────────────────────

# SERVER_INVENTORY: Simulates the server configuration JSON file (SRS §5.3 Inventory Management Module)
# Each dict represents one monitored server with all 13 required fields from the SRS data model
SERVER_INVENTORY = [
    # id: unique row identifier | team: owning team | app: application/server name
    # ip: static IPv4 address | hostname: DNS hostname | env: deployment environment
    # status: operational state | osType/osVer: OS family and version
    # tech: primary technology stack | category: App / DB / Web
    # memory: RAM capacity | cpu: number of cores | hw: Physical or VM

    {"id": 1,  "team": "SMP",  "app": "AppServer-01", "ip": "192.168.1.10", "hostname": "smp-app01",  "env": "Production", "status": "Active",   "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Java",    "category": "App", "memory": "16 GB", "cpu": 8,  "hw": "Physical"},  # SMP Production App Server 1 — primary Java application host
    {"id": 2,  "team": "SMP",  "app": "AppServer-02", "ip": "192.168.1.11", "hostname": "smp-app02",  "env": "Production", "status": "Active",   "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Java",    "category": "App", "memory": "32 GB", "cpu": 16, "hw": "Physical"},  # SMP Production App Server 2 — higher-spec secondary Java host
    {"id": 3,  "team": "SMP",  "app": "DB-Primary",   "ip": "192.168.1.20", "hostname": "smp-db01",   "env": "Production", "status": "Active",   "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Oracle",  "category": "DB",  "memory": "32 GB", "cpu": 16, "hw": "Physical"},  # SMP Primary Oracle DB — most critical data store
    {"id": 4,  "team": "SMP",  "app": "WebServer-01", "ip": "192.168.1.30", "hostname": "smp-web01",  "env": "Production", "status": "Warning",  "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Nginx",   "category": "Web", "memory": "8 GB",  "cpu": 4,  "hw": "VM"},        # Nginx web server — currently in Warning state (high disk: 89%)
    {"id": 5,  "team": "SCMS", "app": "SCMS-App01",   "ip": "192.168.2.10", "hostname": "scms-app01", "env": "UAT",        "status": "Active",   "osType": "Windows",    "osVer": "2019", "tech": ".NET",    "category": "App", "memory": "8 GB",  "cpu": 4,  "hw": "VM"},        # SCMS UAT .NET application server — Windows-based VM
    {"id": 6,  "team": "SCMS", "app": "SCMS-DB01",    "ip": "192.168.2.20", "hostname": "scms-db01",  "env": "UAT",        "status": "Active",   "osType": "Windows",    "osVer": "2019", "tech": "MSSQL",   "category": "DB",  "memory": "16 GB", "cpu": 8,  "hw": "VM"},        # SCMS UAT MSSQL database server — Windows-based VM
    {"id": 7,  "team": "SMP",  "app": "DR-Server-01", "ip": "192.168.3.10", "hostname": "smp-dr01",   "env": "DR",         "status": "Inactive", "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Java",    "category": "App", "memory": "16 GB", "cpu": 8,  "hw": "Physical"},  # Disaster Recovery standby server — intentionally Inactive until failover
    {"id": 8,  "team": "SCMS", "app": "Dev-Server",   "ip": "192.168.4.10", "hostname": "scms-dev01", "env": "Dev",        "status": "Active",   "osType": "Linux RHEL", "osVer": "9.0",  "tech": "Node.js", "category": "App", "memory": "4 GB",  "cpu": 2,  "hw": "VM"},        # Lightweight Dev VM — used by developers for builds and testing
]

# DISK_USAGE: Simulates real-time disk monitoring data per server (SRS §5.2 Disk Monitoring Module)
# total/used/avail are all in GB; pct is pre-computed utilization percentage
DISK_USAGE = [
    {"hostname": "smp-app01",  "total": 500,  "used": 310,  "avail": 190, "pct": 62},   # 62%  — Normal; well within safe limits
    {"hostname": "smp-app02",  "total": 500,  "used": 420,  "avail": 80,  "pct": 84},   # 84%  — Warning; approaching critical threshold
    {"hostname": "smp-db01",   "total": 2000, "used": 1450, "avail": 550, "pct": 73},   # 72.5%— Warning; large DB volume under pressure
    {"hostname": "smp-web01",  "total": 200,  "used": 178,  "avail": 22,  "pct": 89},   # 89%  — CRITICAL; immediate attention required
    {"hostname": "scms-app01", "total": 300,  "used": 145,  "avail": 155, "pct": 48},   # 48%  — Normal
    {"hostname": "scms-db01",  "total": 1000, "used": 480,  "avail": 520, "pct": 48},   # 48%  — Normal
    {"hostname": "smp-dr01",   "total": 500,  "used": 100,  "avail": 400, "pct": 20},   # 20%  — Normal; DR server mostly idle
    {"hostname": "scms-dev01", "total": 100,  "used": 38,   "avail": 62,  "pct": 38},   # 38%  — Normal; lightweight dev workload
]

# TEAM_MEMBERS: Simulates IT personnel data from the Excel-based team roster (SRS §5.4 Team Roster Module)
# Fields: id=employee number, name=full name, doj=date of joining, project=team assignment, contact=phone, email
TEAM_MEMBERS = [
    {"id": "EMP001", "name": "Sandeep Kumar",   "doj": "2020-06-01", "project": "SMP",  "contact": "9876543210", "email": "sandeep@smp.com"},    # Most senior SMP member (joined 2020)
    {"id": "EMP002", "name": "Navnidhi Singh",  "doj": "2022-08-15", "project": "SMP",  "contact": "9876543211", "email": "navnidhi@smp.com"},   # SRS project author — SMP team
    {"id": "EMP003", "name": "Smriti Singh",    "doj": "2022-08-15", "project": "SMP",  "contact": "9876543212", "email": "smriti@smp.com"},     # SRS project author — SMP team
    {"id": "EMP004", "name": "Simran",          "doj": "2022-09-01", "project": "SCMS", "contact": "9876543213", "email": "simran@scms.com"},    # SRS project author — SCMS team
    {"id": "EMP005", "name": "Diksha Shahi",    "doj": "2022-09-01", "project": "SCMS", "contact": "9876543214", "email": "diksha@scms.com"},    # SRS project author — SCMS team
    {"id": "EMP006", "name": "Samy Raj",        "doj": "2019-03-10", "project": "SMP",  "contact": "9876543215", "email": "samy@smp.com"},       # Longest-serving SMP member (joined 2019)
    {"id": "EMP007", "name": "Aaditya Sharma",  "doj": "2021-11-20", "project": "SMP",  "contact": "9876543216", "email": "aaditya@smp.com"},    # Mid-level SMP member
    {"id": "EMP008", "name": "Armaan Khan",     "doj": "2023-01-05", "project": "SCMS", "contact": "9876543217", "email": "armaan@scms.com"},    # Junior SCMS member (most recent joiner)
    {"id": "EMP009", "name": "Pratyush Verma",  "doj": "2023-03-15", "project": "SMP",  "contact": "9876543218", "email": "pratyush@smp.com"},   # Junior SMP member
    {"id": "EMP010", "name": "Avanish Tiwari",  "doj": "2021-07-22", "project": "SCMS", "contact": "9876543219", "email": "avanish@scms.com"},   # Mid-level SCMS member
    {"id": "EMP011", "name": "Prabhat Mishra",  "doj": "2020-12-01", "project": "SMP",  "contact": "9876543220", "email": "prabhat@smp.com"},    # Experienced SMP member (joined 2020)
]

# SHIFT_CODES: 31 shift assignments forming one month's base pattern (SRS §5.4 shift scheduling)
# G=General day shift | M1=Mid shift | E=Early shift | N=Night shift | CO=Comp Off | PL=Planned Leave
SHIFT_CODES = ["G","M1","E","N","CO","PL","G","G","M1","E","N","G","G","CO","G","M1","E","G","N","G","PL","G","M1","G","E","G","N","CO","G","M1","G"]

# WEEKDAYS: Single-char day labels for each of March 2025's 31 days (F=Fri, S=Sat/Sun, M=Mon, T=Tue, W=Wed)
# Used in roster column headers to identify and visually distinguish weekends
WEEKDAYS = ["F","S","S","M","T","W","T","F","S","S","M","T","W","T","F","S","S","M","T","W","T","F","S","S","M","T","W","T","S","S","M"]

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS  —  SRS §5.5 (Data Processing Layer)
# ─────────────────────────────────────────────────────────────────────────────

def disk_status(pct):
    """Returns severity label and CSS class for a given disk utilization percentage.
       Thresholds defined in SRS §5.2: ≥85% Critical, ≥65% Warning, <65% Normal."""
    if pct >= 85:           # Critical threshold: disk is nearly full, immediate action needed
        return "Critical", "critical"
    elif pct >= 65:         # Warning threshold: disk usage is elevated, monitor closely
        return "Warning", "warning"
    else:                   # Normal threshold: disk usage is within healthy bounds
        return "Normal", "normal"

def build_roster():
    """Generates each team member's 31-day shift schedule by rotating the SHIFT_CODES base pattern.
       Each employee's schedule is offset by (index × 3) to ensure variety across the team."""
    roster = []                                             # Initialise empty list to collect all rows
    for mi, member in enumerate(TEAM_MEMBERS):              # mi = member index, member = employee dict
        shifts = []                                         # Holds the 31 shift codes for this employee
        for i in range(31):                                 # Iterate over each of the 31 days in March
            code = SHIFT_CODES[(i + mi * 3) % len(SHIFT_CODES)]  # Rotate pattern by (mi*3) positions to stagger schedules
            shifts.append(code)                             # Append the resolved shift code for day i
        roster.append({                                     # Add this employee's full row to the roster list
            "name": member["name"].split()[0],              # Use first name only to save horizontal space in the calendar
            "shifts": shifts,                               # List of 31 shift codes for the month
        })
    return roster                                           # Return the complete list of roster rows

def get_summary():
    """Computes the five KPI values shown on the Overview stat cards (SRS §5.1 Dashboard Module)."""
    return {
        "active":   sum(1 for s in SERVER_INVENTORY if s["status"] == "Active"),    # Count servers with status Active
        "warning":  sum(1 for s in SERVER_INVENTORY if s["status"] == "Warning"),   # Count servers with status Warning
        "inactive": sum(1 for s in SERVER_INVENTORY if s["status"] == "Inactive"),  # Count servers with status Inactive
        "highDisk": sum(1 for d in DISK_USAGE if d["pct"] >= 85),                   # Count servers at critical disk level
        "teamSize": len(TEAM_MEMBERS),                                               # Total number of IT personnel
    }

# ─────────────────────────────────────────────────────────────────────────────
# ROUTES  —  SRS §3.1 Layer 2 (Flask acts as the application server / routing layer)
# Each route function handles one HTTP endpoint, preparing data and returning a response.
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")                     # Maps HTTP GET / to the index view — the dashboard home page
def index():
    """Renders the main dashboard HTML shell.
       All data is loaded dynamically via AJAX calls from the JavaScript frontend."""
    now = datetime.now().strftime("%d %b %Y, %H:%M")   # Format current date-time for display in the page header
    return render_template("index.html", now=now)       # Render templates/index.html and pass 'now' as a template variable

# ── API Endpoints — JSON data served to the JavaScript frontend via fetch() ──

@app.route("/api/summary")          # GET /api/summary — returns the five KPI counts for the Overview stat cards
def api_summary():
    """Returns JSON summary statistics: active, warning, inactive server counts, high-disk count, team size."""
    return jsonify(get_summary())   # Serialise the summary dict to a JSON HTTP response

@app.route("/api/inventory")        # GET /api/inventory — returns the full server inventory list
def api_inventory():
    """Returns the complete SERVER_INVENTORY list as JSON for the Inventory Management table (SRS §5.3)."""
    return jsonify(SERVER_INVENTORY)  # Serialise and return the full list of server configuration dicts

@app.route("/api/disk")             # GET /api/disk — returns disk usage data augmented with severity labels
def api_disk():
    """Returns DISK_USAGE list enriched with statusLabel and statusClass fields (SRS §5.2)."""
    enriched = []                               # Will hold each disk record with added severity fields
    for d in DISK_USAGE:                        # Iterate over every server's disk record
        label, cls = disk_status(d["pct"])      # Compute severity label ("Critical"/"Warning"/"Normal") and CSS class
        enriched.append({**d, "statusLabel": label, "statusClass": cls})  # Merge original dict with the two new fields
    return jsonify(enriched)                    # Return the enriched list as a JSON response

@app.route("/api/team")             # GET /api/team — returns the full team member list
def api_team():
    """Returns the complete TEAM_MEMBERS list as JSON for the Team Details table (SRS §5.4)."""
    return jsonify(TEAM_MEMBERS)    # Serialise and return the full list of employee dicts

@app.route("/api/roster")           # GET /api/roster — returns the computed monthly shift roster
def api_roster():
    """Returns the generated roster (name + 31 shift codes) and weekday labels for the calendar header."""
    return jsonify({
        "roster":   build_roster(),  # Generated list of {name, shifts[]} objects for all 11 team members
        "weekdays": WEEKDAYS,        # 31-element list of day-letter codes used to label calendar columns
    })

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":          # Only runs the development server when the file is executed directly (not imported)
    app.run(debug=True, port=5000)  # Start Flask dev server on http://localhost:5000 with auto-reload enabled
