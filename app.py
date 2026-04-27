from flask import Flask, render_template, jsonify, request, abort  # Flask: web framework; render_template: loads HTML files from /templates; jsonify: converts Python dict/list to a JSON HTTP response; request: reads incoming request body/params; abort: sends HTTP error codes like 404
from datetime import datetime  # datetime: used to get the current date and time for the dashboard header display
from pathlib import Path  # Path: cross-platform file path handling — works correctly on Windows, Mac, and Linux
import json, copy  # json: reads and writes JSON files on disk; copy: makes deep copies of data so the original DEFAULT_DATA is never accidentally modified

app = Flask(__name__)  # Creates the Flask application instance; __name__ tells Flask where to find the templates/ and static/ folders relative to this file

BASE_DIR  = Path(__file__).resolve().parent  # Gets the absolute directory path of the folder that contains app.py (e.g. /opt/render/project/src)
DATA_FILE = BASE_DIR / "data.json"  # Constructs the full file path to data.json — this single file stores all servers, disk records, and team members persistently

# ── Default seed data (used only if data.json doesn't exist yet) ──────────────

DEFAULT_DATA = {  # Master Python dictionary holding all starting data — written to data.json on first launch
    "inventory": [  # List of server dictionaries; each dict represents one monitored server with 14 fields
        {"id": 1, "team": "SMP",  "app": "AppServer-01", "ip": "192.168.1.10", "hostname": "smp-app01",  "env": "Production", "status": "Active",   "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Java",    "category": "App", "memory": "16 GB", "cpu": 8,  "hw": "Physical"},  # SMP Production App Server 1 — primary Java application host
        {"id": 2, "team": "SMP",  "app": "AppServer-02", "ip": "192.168.1.11", "hostname": "smp-app02",  "env": "Production", "status": "Active",   "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Java",    "category": "App", "memory": "32 GB", "cpu": 16, "hw": "Physical"},  # SMP Production App Server 2 — higher-spec secondary Java host
        {"id": 3, "team": "SMP",  "app": "DB-Primary",   "ip": "192.168.1.20", "hostname": "smp-db01",   "env": "Production", "status": "Active",   "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Oracle",  "category": "DB",  "memory": "32 GB", "cpu": 16, "hw": "Physical"},  # SMP Primary Oracle database — most critical data store
        {"id": 4, "team": "SMP",  "app": "WebServer-01", "ip": "192.168.1.30", "hostname": "smp-web01",  "env": "Production", "status": "Warning",  "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Nginx",   "category": "Web", "memory": "8 GB",  "cpu": 4,  "hw": "VM"},       # Nginx web server — Warning state because disk is at 89%
        {"id": 5, "team": "SCMS", "app": "SCMS-App01",   "ip": "192.168.2.10", "hostname": "scms-app01", "env": "UAT",        "status": "Active",   "osType": "Windows",    "osVer": "2019", "tech": ".NET",    "category": "App", "memory": "8 GB",  "cpu": 4,  "hw": "VM"},       # SCMS UAT .NET application server — Windows virtual machine
        {"id": 6, "team": "SCMS", "app": "SCMS-DB01",    "ip": "192.168.2.20", "hostname": "scms-db01",  "env": "UAT",        "status": "Active",   "osType": "Windows",    "osVer": "2019", "tech": "MSSQL",   "category": "DB",  "memory": "16 GB", "cpu": 8,  "hw": "VM"},       # SCMS UAT MSSQL database server — Windows virtual machine
        {"id": 7, "team": "SMP",  "app": "DR-Server-01", "ip": "192.168.3.10", "hostname": "smp-dr01",   "env": "DR",         "status": "Inactive", "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Java",    "category": "App", "memory": "16 GB", "cpu": 8,  "hw": "Physical"},  # Disaster Recovery standby — kept Inactive until a failover is triggered
        {"id": 8, "team": "SCMS", "app": "Dev-Server",   "ip": "192.168.4.10", "hostname": "scms-dev01", "env": "Dev",        "status": "Active",   "osType": "Linux RHEL", "osVer": "9.0",  "tech": "Node.js", "category": "App", "memory": "4 GB",  "cpu": 2,  "hw": "VM"},       # Lightweight Dev VM used by developers for local builds and testing
    ],
    "disk": [  # List of disk usage records; one entry per server hostname — linked to inventory by hostname
        {"hostname": "smp-app01",  "total": 500,  "used": 310,  "avail": 190, "pct": 62},  # 62% used — Normal; well within safe limits
        {"hostname": "smp-app02",  "total": 500,  "used": 420,  "avail": 80,  "pct": 84},  # 84% used — Warning; just below the 85% critical threshold
        {"hostname": "smp-db01",   "total": 2000, "used": 1450, "avail": 550, "pct": 73},  # 73% used — Warning; large DB volume under pressure
        {"hostname": "smp-web01",  "total": 200,  "used": 178,  "avail": 22,  "pct": 89},  # 89% used — CRITICAL; immediate action required
        {"hostname": "scms-app01", "total": 300,  "used": 145,  "avail": 155, "pct": 48},  # 48% used — Normal
        {"hostname": "scms-db01",  "total": 1000, "used": 480,  "avail": 520, "pct": 48},  # 48% used — Normal
        {"hostname": "smp-dr01",   "total": 500,  "used": 100,  "avail": 400, "pct": 20},  # 20% used — Normal; DR server is mostly idle
        {"hostname": "scms-dev01", "total": 100,  "used": 38,   "avail": 62,  "pct": 38},  # 38% used — Normal; lightweight dev workload
    ],
    "team": [  # List of IT personnel shown in the Team Details section and used to build the shift roster
        {"id": "EMP001", "name": "Sandeep Kumar",  "doj": "2020-06-01", "project": "SMP",  "contact": "9876543210", "email": "sandeep@smp.com"},   # Senior SMP member — joined 2020
        {"id": "EMP002", "name": "Navnidhi Singh", "doj": "2022-08-15", "project": "SMP",  "contact": "9876543211", "email": "navnidhi@smp.com"},   # SMP member
        {"id": "EMP003", "name": "Smriti Singh",   "doj": "2022-08-15", "project": "SMP",  "contact": "9876543212", "email": "smriti@smp.com"},     # SMP member
        {"id": "EMP004", "name": "Simran",         "doj": "2022-09-01", "project": "SCMS", "contact": "9876543213", "email": "simran@scms.com"},    # SCMS member
        {"id": "EMP005", "name": "Diksha Shahi",   "doj": "2022-09-01", "project": "SCMS", "contact": "9876543214", "email": "diksha@scms.com"},    # SCMS member — project author
        {"id": "EMP006", "name": "Samy Raj",       "doj": "2019-03-10", "project": "SMP",  "contact": "9876543215", "email": "samy@smp.com"},       # Longest-serving member — joined 2019
        {"id": "EMP007", "name": "Aaditya Sharma", "doj": "2021-11-20", "project": "SMP",  "contact": "9876543216", "email": "aaditya@smp.com"},    # Mid-level SMP member
        {"id": "EMP008", "name": "Armaan Khan",    "doj": "2023-01-05", "project": "SCMS", "contact": "9876543217", "email": "armaan@scms.com"},    # Junior SCMS member — most recent joiner
        {"id": "EMP009", "name": "Pratyush Verma", "doj": "2023-03-15", "project": "SMP",  "contact": "9876543218", "email": "pratyush@smp.com"},   # Junior SMP member
        {"id": "EMP010", "name": "Avanish Tiwari", "doj": "2021-07-22", "project": "SCMS", "contact": "9876543219", "email": "avanish@scms.com"},   # Mid-level SCMS member
        {"id": "EMP011", "name": "Prabhat Mishra", "doj": "2020-12-01", "project": "SMP",  "contact": "9876543220", "email": "prabhat@smp.com"},    # Experienced SMP member — joined 2020
    ],
}

SHIFT_CODES = ["G","M1","E","N","CO","PL","G","G","M1","E","N","G","G","CO","G","M1","E","G","N","G","PL","G","M1","G","E","G","N","CO","G","M1","G"]  # Base 31-day shift pattern used to generate each employee's monthly schedule — G=General day shift, M1=Mid shift, E=Early, N=Night, CO=Comp Off, PL=Planned Leave
WEEKDAYS    = ["F","S","S","M","T","W","T","F","S","S","M","T","W","T","F","S","S","M","T","W","T","F","S","S","M","T","W","T","S","S","M"]  # Day-of-week label for each of March 2025's 31 days (F=Fri, S=Sat/Sun, M=Mon, T=Tue, W=Wed) — used to highlight weekends in the roster calendar header

# ── Data persistence helpers ───────────────────────────────────────────────────

def load_data():  # Called by every route that needs data — always reads the latest state from disk so edits made in admin are reflected immediately
    if DATA_FILE.exists():  # Checks whether data.json has already been created on this server
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))  # Reads the file as a text string and parses it into a Python dictionary
    data = copy.deepcopy(DEFAULT_DATA)  # First run: no data.json yet, so deep-copy DEFAULT_DATA to avoid mutating the original constant
    save_data(data)  # Writes the default data to disk so all future calls can load it
    return data  # Returns the freshly initialised data dictionary

def save_data(data):  # Called after every create, update, or delete operation to persist the change
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")  # Serialises the Python dictionary to a pretty-printed JSON string and overwrites data.json completely

def next_inv_id(inventory):  # Generates the next unique integer ID for a newly added server
    return max((s["id"] for s in inventory), default=0) + 1  # Finds the largest existing ID in the inventory list and adds 1; returns 1 if the list is empty (default=0 + 1)

def next_emp_id(team):  # Generates the next employee ID string in the format EMP001, EMP002, …
    nums = [int(m["id"].replace("EMP","")) for m in team if m["id"].startswith("EMP")]  # Strips the "EMP" prefix from each ID and converts the remaining digits to an integer (e.g. "EMP007" → 7)
    return f"EMP{(max(nums, default=0)+1):03d}"  # Takes the highest number found, adds 1, and zero-pads it to 3 digits (e.g. 11 → "EMP012")

# ── Helpers ────────────────────────────────────────────────────────────────────

def disk_status(pct):  # Determines the severity label and CSS class for a given disk utilisation percentage
    if pct >= 85: return "Critical", "critical"  # 85% or above → Critical (displayed in red on the dashboard)
    if pct >= 65: return "Warning",  "warning"   # 65–84% → Warning (displayed in amber)
    return "Normal", "normal"                     # Below 65% → Normal (displayed in green)

def build_roster(team):  # Produces the complete 31-day shift calendar for every current team member
    roster = []  # Accumulator list — will hold one row dict per employee
    for mi, member in enumerate(team):  # mi = member index (0, 1, 2…); member = the employee's dict from the team list
        shifts = [SHIFT_CODES[(i + mi * 3) % len(SHIFT_CODES)] for i in range(31)]  # For each of the 31 days, picks a shift code by rotating the base pattern by (mi × 3) positions — ensures different employees have different schedules
        roster.append({"name": member["name"].split()[0], "shifts": shifts})  # Appends a row containing the employee's first name and their list of 31 shift codes
    return roster  # Returns the complete list of roster rows, one per team member

def get_summary(data):  # Calculates the five KPI numbers displayed as stat cards on the Overview page
    inv  = data["inventory"]  # Local alias for the server inventory list — avoids typing data["inventory"] repeatedly
    disk = data["disk"]       # Local alias for the disk usage list
    team = data["team"]       # Local alias for the team members list
    return {
        "active":   sum(1 for s in inv  if s["status"] == "Active"),    # Counts every server whose status field equals "Active"
        "warning":  sum(1 for s in inv  if s["status"] == "Warning"),   # Counts every server whose status field equals "Warning"
        "inactive": sum(1 for s in inv  if s["status"] == "Inactive"),  # Counts every server whose status field equals "Inactive"
        "highDisk": sum(1 for d in disk if d["pct"] >= 85),             # Counts servers at Critical disk usage (≥85%)
        "teamSize": len(team),                                           # Total number of IT personnel in the team list
    }

# ── Read routes ────────────────────────────────────────────────────────────────

@app.route("/")  # Registers the root URL "/" — this function runs when someone opens the home page in a browser
def index():  # View function that serves the main dashboard HTML page
    now = datetime.now().strftime("%d %b %Y, %H:%M")  # Formats current date and time as "25 Apr 2026, 11:52" to display in the dashboard header
    return render_template("index.html", now=now)  # Renders templates/index.html and injects the formatted time as the template variable {{ now }}

@app.route("/admin")  # Registers the URL "/admin" — accessible at yoursite.onrender.com/admin
def admin():  # View function that serves the admin panel page
    return render_template("admin.html")  # Renders templates/admin.html — the full CRUD interface for managing servers and team members

@app.route("/api/summary")  # Registers GET /api/summary — the JavaScript on the dashboard calls this to populate the five stat cards
def api_summary():  # Returns the five KPI counts as a JSON object
    return jsonify(get_summary(load_data()))  # Loads the latest data, computes summary statistics, and returns them as a JSON HTTP response

@app.route("/api/inventory")  # Registers GET /api/inventory — called by the frontend JavaScript to fill the Server Inventory table
def api_inventory():  # Returns the complete server list as JSON
    return jsonify(load_data()["inventory"])  # Loads data.json and extracts only the "inventory" key, returning it as a JSON array

@app.route("/api/disk")  # Registers GET /api/disk — called by the frontend to fill the Disk Monitoring table
def api_disk():  # Returns disk records enriched with human-readable severity labels and CSS class names
    enriched = []  # Will hold the augmented version of each disk record
    for d in load_data()["disk"]:  # Iterates over every disk record in data.json
        label, cls = disk_status(d["pct"])  # Calls disk_status() to determine severity ("Critical"/"Warning"/"Normal") and its matching CSS class ("critical"/"warning"/"normal")
        enriched.append({**d, "statusLabel": label, "statusClass": cls})  # Merges all original disk fields with the two new severity fields using Python dictionary unpacking (**)
    return jsonify(enriched)  # Returns the enriched list as a JSON array response

@app.route("/api/team")  # Registers GET /api/team — called by the frontend to populate the Team Details table
def api_team():  # Returns the complete team members list as JSON
    return jsonify(load_data()["team"])  # Loads data.json and returns only the "team" key as a JSON array

@app.route("/api/roster")  # Registers GET /api/roster — called by the frontend to build the monthly shift roster calendar
def api_roster():  # Returns the computed roster rows and weekday header labels
    data = load_data()  # Loads the latest data so the roster reflects any team members added or removed via admin
    return jsonify({"roster": build_roster(data["team"]), "weekdays": WEEKDAYS})  # Returns a JSON object containing the generated roster rows and the 31-day weekday label array for March 2025

# ── Admin: Server CRUD ─────────────────────────────────────────────────────────

@app.route("/api/admin/server", methods=["POST"])  # Registers POST /api/admin/server — triggered when the admin submits the Add Server form
def add_server():  # Creates a new server entry in the inventory and automatically creates a matching disk record
    body = request.get_json(force=True)  # Parses the JSON payload from the request body (the form field values sent by admin.html)
    data = load_data()  # Loads current data so the new server can be appended to the existing list
    body["id"] = next_inv_id(data["inventory"])  # Assigns the next available numeric ID so every server has a unique identifier
    total = int(body.get("diskTotal", 500))  # Reads the disk total from the form submission; falls back to 500 GB if the field was left empty
    used  = int(body.get("diskUsed",  100))  # Reads the disk used from the form submission; falls back to 100 GB if the field was left empty
    data["inventory"].append({k: v for k, v in body.items() if k not in ("diskTotal","diskUsed")})  # Appends the new server dict to inventory, excluding diskTotal/diskUsed because those belong in the separate disk list
    data["disk"].append({"hostname": body["hostname"], "total": total, "used": used,
                         "avail": total - used, "pct": round(used / total * 100)})  # Creates a matching disk record for this server, computing available space and usage percentage on the fly
    save_data(data)  # Writes the updated data (with the new server and disk record) back to data.json
    return jsonify({"ok": True, "id": body["id"]}), 201  # Returns a JSON success message with the new server's ID; HTTP 201 = resource successfully created

@app.route("/api/admin/server/<int:sid>", methods=["PUT"])  # Registers PUT /api/admin/server/4 — triggered when admin clicks Save on the Edit Server form (sid is the server ID extracted from the URL)
def update_server(sid):  # Updates an existing server record identified by its numeric ID
    body = request.get_json(force=True)  # Parses the updated field values from the request body
    data = load_data()  # Loads current data so we can locate and patch the right server
    for i, s in enumerate(data["inventory"]):  # Iterates through the inventory list with index i and server dict s
        if s["id"] == sid:  # Stops when it finds the server whose ID matches the URL parameter
            data["inventory"][i] = {**s, **body, "id": sid}  # Replaces the server record by merging the original fields (**s) with the updated fields (**body); forces the ID to stay unchanged
            if "diskTotal" in body or "diskUsed" in body:  # Only touches the disk record if the admin also submitted disk values
                total = int(body.get("diskTotal", 500))  # Reads the new disk total (GB)
                used  = int(body.get("diskUsed", 100))   # Reads the new disk used (GB)
                hn = data["inventory"][i]["hostname"]  # Gets the hostname of the updated server to find its matching disk record
                for j, d in enumerate(data["disk"]):  # Iterates through disk records to find the one for this hostname
                    if d["hostname"] == hn:  # Matches the disk record belonging to this server
                        data["disk"][j] = {"hostname": hn, "total": total, "used": used,
                                           "avail": total - used, "pct": round(used / total * 100)}  # Replaces the disk record with recalculated values (avail and pct are derived from total and used)
            save_data(data)  # Writes the updated data back to data.json
            return jsonify({"ok": True})  # Returns a JSON success response
    abort(404)  # If the loop finishes without finding the server, returns HTTP 404 Not Found

@app.route("/api/admin/server/<int:sid>", methods=["DELETE"])  # Registers DELETE /api/admin/server/4 — triggered when admin confirms server deletion in the dialog
def delete_server(sid):  # Removes a server and its associated disk record from data.json
    data = load_data()  # Loads current data from data.json
    inv = [s for s in data["inventory"] if s["id"] != sid]  # Builds a new inventory list containing every server EXCEPT the one being deleted
    if len(inv) == len(data["inventory"]):  # If lengths are equal, no server was removed — the ID didn't exist
        abort(404)  # Returns HTTP 404 Not Found
    removed_hn = next((s["hostname"] for s in data["inventory"] if s["id"] == sid), None)  # Captures the hostname of the deleted server so we can also delete its disk record
    data["inventory"] = inv  # Replaces the inventory with the filtered list (one server removed)
    if removed_hn:  # Only clean up disk data if we successfully identified a hostname
        data["disk"] = [d for d in data["disk"] if d["hostname"] != removed_hn]  # Filters out the disk record whose hostname matches the deleted server
    save_data(data)  # Writes the updated data (server and disk record both removed) back to data.json
    return jsonify({"ok": True})  # Returns a JSON success response

# ── Admin: Team CRUD ───────────────────────────────────────────────────────────

@app.route("/api/admin/member", methods=["POST"])  # Registers POST /api/admin/member — triggered when admin submits the Add Member form
def add_member():  # Creates a new team member record and saves it to data.json
    body = request.get_json(force=True)  # Parses the new member's details (name, doj, project, contact, email) from the request body
    data = load_data()  # Loads current data from data.json
    body["id"] = next_emp_id(data["team"])  # Auto-generates the next sequential employee ID (e.g. "EMP012") so the admin never has to type it manually
    data["team"].append(body)  # Appends the complete new member dictionary to the team list
    save_data(data)  # Writes the updated team list back to data.json
    return jsonify({"ok": True, "id": body["id"]}), 201  # Returns the new employee ID in the response so the admin panel can display it; HTTP 201 = resource created

@app.route("/api/admin/member/<emp_id>", methods=["PUT"])  # Registers PUT /api/admin/member/EMP005 — triggered when admin saves edits to an existing team member (emp_id comes from the URL)
def update_member(emp_id):  # Updates a team member's record identified by their employee ID string (e.g. "EMP005")
    body = request.get_json(force=True)  # Parses the updated field values from the request body
    data = load_data()  # Loads current data from data.json
    for i, m in enumerate(data["team"]):  # Iterates through the team list with index i and member dict m
        if m["id"] == emp_id:  # Stops when it finds the member whose ID matches the URL parameter
            data["team"][i] = {**m, **body, "id": emp_id}  # Replaces the member record by merging original fields (**m) with updated fields (**body); forces the ID to stay unchanged
            save_data(data)  # Writes the updated team list back to data.json
            return jsonify({"ok": True})  # Returns a JSON success response
    abort(404)  # If no member with that ID was found, returns HTTP 404 Not Found

@app.route("/api/admin/member/<emp_id>", methods=["DELETE"])  # Registers DELETE /api/admin/member/EMP005 — triggered when admin confirms deletion of a team member
def delete_member(emp_id):  # Removes a team member from the team list in data.json
    data = load_data()  # Loads current data from data.json
    team = [m for m in data["team"] if m["id"] != emp_id]  # Builds a new team list containing every member EXCEPT the one being deleted
    if len(team) == len(data["team"]):  # If lengths are equal, no member was removed — the employee ID didn't exist
        abort(404)  # Returns HTTP 404 Not Found
    data["team"] = team  # Replaces the team list with the filtered version (one member removed)
    save_data(data)  # Writes the updated team list back to data.json
    return jsonify({"ok": True})  # Returns a JSON success response

if __name__ == "__main__":  # Only executes the block below when you run `python app.py` directly — ignored when gunicorn starts the app on Render
    app.run(debug=True, port=5000)  # Starts Flask's built-in development server on http://localhost:5000 with debug mode on (auto-reloads on code changes and shows detailed error pages)