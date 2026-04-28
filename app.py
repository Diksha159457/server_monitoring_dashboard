from flask import Flask, render_template, jsonify, request, abort, session, redirect, url_for
from datetime import datetime
from pathlib import Path
from functools import wraps
import json, copy, os

app = Flask(__name__)

# ── Security ───────────────────────────────────────────────────────────────────
app.secret_key = os.environ.get("SECRET_KEY", "serverwatch-dev-secret-2026")

ADMIN_CREDENTIALS_FILE = Path(__file__).resolve().parent / "admins.json"

def load_admins():
    """Load admin accounts from admins.json. Creates default on first run."""
    if ADMIN_CREDENTIALS_FILE.exists():
        return json.loads(ADMIN_CREDENTIALS_FILE.read_text(encoding="utf-8"))
    # Default admin account seeded on first run
    default = {"admin": "serverwatch@2026"}
    ADMIN_CREDENTIALS_FILE.write_text(json.dumps(default, indent=2), encoding="utf-8")
    return default

def save_admins(admins):
    ADMIN_CREDENTIALS_FILE.write_text(json.dumps(admins, indent=2), encoding="utf-8")

# ── Auth decorators ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Unauthorised"}), 401
        return f(*args, **kwargs)
    return decorated

# ── File paths ─────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

# ── Default data ───────────────────────────────────────────────────────────────
DEFAULT_DATA = {
    "inventory": [
        {"id": 1, "team": "SMP",  "app": "AppServer-01", "ip": "192.168.1.10", "hostname": "smp-app01",  "env": "Production", "status": "Active",   "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Java",    "category": "App", "memory": "16 GB", "cpu": 8,  "hw": "Physical"},
        {"id": 2, "team": "SMP",  "app": "AppServer-02", "ip": "192.168.1.11", "hostname": "smp-app02",  "env": "Production", "status": "Active",   "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Java",    "category": "App", "memory": "32 GB", "cpu": 16, "hw": "Physical"},
        {"id": 3, "team": "SMP",  "app": "DB-Primary",   "ip": "192.168.1.20", "hostname": "smp-db01",   "env": "Production", "status": "Active",   "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Oracle",  "category": "DB",  "memory": "32 GB", "cpu": 16, "hw": "Physical"},
        {"id": 4, "team": "SMP",  "app": "WebServer-01", "ip": "192.168.1.30", "hostname": "smp-web01",  "env": "Production", "status": "Warning",  "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Nginx",   "category": "Web", "memory": "8 GB",  "cpu": 4,  "hw": "VM"},
        {"id": 5, "team": "SCMS", "app": "SCMS-App01",   "ip": "192.168.2.10", "hostname": "scms-app01", "env": "UAT",        "status": "Active",   "osType": "Windows",    "osVer": "2019", "tech": ".NET",    "category": "App", "memory": "8 GB",  "cpu": 4,  "hw": "VM"},
        {"id": 6, "team": "SCMS", "app": "SCMS-DB01",    "ip": "192.168.2.20", "hostname": "scms-db01",  "env": "UAT",        "status": "Active",   "osType": "Windows",    "osVer": "2019", "tech": "MSSQL",   "category": "DB",  "memory": "16 GB", "cpu": 8,  "hw": "VM"},
        {"id": 7, "team": "SMP",  "app": "DR-Server-01", "ip": "192.168.3.10", "hostname": "smp-dr01",   "env": "DR",         "status": "Inactive", "osType": "Linux RHEL", "osVer": "8.8",  "tech": "Java",    "category": "App", "memory": "16 GB", "cpu": 8,  "hw": "Physical"},
        {"id": 8, "team": "SCMS", "app": "Dev-Server",   "ip": "192.168.4.10", "hostname": "scms-dev01", "env": "Dev",        "status": "Active",   "osType": "Linux RHEL", "osVer": "9.0",  "tech": "Node.js", "category": "App", "memory": "4 GB",  "cpu": 2,  "hw": "VM"},
    ],
    "disk": [
        {"hostname": "smp-app01",  "total": 500,  "used": 310,  "avail": 190, "pct": 62},
        {"hostname": "smp-app02",  "total": 500,  "used": 420,  "avail": 80,  "pct": 84},
        {"hostname": "smp-db01",   "total": 2000, "used": 1450, "avail": 550, "pct": 73},
        {"hostname": "smp-web01",  "total": 200,  "used": 178,  "avail": 22,  "pct": 89},
        {"hostname": "scms-app01", "total": 300,  "used": 145,  "avail": 155, "pct": 48},
        {"hostname": "scms-db01",  "total": 1000, "used": 480,  "avail": 520, "pct": 48},
        {"hostname": "smp-dr01",   "total": 500,  "used": 100,  "avail": 400, "pct": 20},
        {"hostname": "scms-dev01", "total": 100,  "used": 38,   "avail": 62,  "pct": 38},
    ],
    "team": [
        {"id": "EMP001", "name": "Sandeep Kumar",  "doj": "2020-06-01", "project": "SMP",  "contact": "9876543210", "email": "sandeep@smp.com"},
        {"id": "EMP002", "name": "Navnidhi Singh", "doj": "2022-08-15", "project": "SMP",  "contact": "9876543211", "email": "navnidhi@smp.com"},
        {"id": "EMP003", "name": "Smriti Singh",   "doj": "2022-08-15", "project": "SMP",  "contact": "9876543212", "email": "smriti@smp.com"},
        {"id": "EMP004", "name": "Simran",         "doj": "2022-09-01", "project": "SCMS", "contact": "9876543213", "email": "simran@scms.com"},
        {"id": "EMP005", "name": "Diksha Shahi",   "doj": "2022-09-01", "project": "SCMS", "contact": "9876543214", "email": "diksha@scms.com"},
        {"id": "EMP006", "name": "Samy Raj",       "doj": "2019-03-10", "project": "SMP",  "contact": "9876543215", "email": "samy@smp.com"},
        {"id": "EMP007", "name": "Aaditya Sharma", "doj": "2021-11-20", "project": "SMP",  "contact": "9876543216", "email": "aaditya@smp.com"},
        {"id": "EMP008", "name": "Armaan Khan",    "doj": "2023-01-05", "project": "SCMS", "contact": "9876543217", "email": "armaan@scms.com"},
        {"id": "EMP009", "name": "Pratyush Verma", "doj": "2023-03-15", "project": "SMP",  "contact": "9876543218", "email": "pratyush@smp.com"},
        {"id": "EMP010", "name": "Avanish Tiwari", "doj": "2021-07-22", "project": "SCMS", "contact": "9876543219", "email": "avanish@scms.com"},
        {"id": "EMP011", "name": "Prabhat Mishra", "doj": "2020-12-01", "project": "SMP",  "contact": "9876543220", "email": "prabhat@smp.com"},
    ],
}

SHIFT_CODES = ["G","M1","E","N","CO","PL","G","G","M1","E","N","G","G","CO","G","M1","E","G","N","G","PL","G","M1","G","E","G","N","CO","G","M1","G"]
WEEKDAYS    = ["F","S","S","M","T","W","T","F","S","S","M","T","W","T","F","S","S","M","T","W","T","F","S","S","M","T","W","T","S","S","M"]

# ── Data helpers ───────────────────────────────────────────────────────────────
def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    data = copy.deepcopy(DEFAULT_DATA)
    save_data(data)
    return data

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def next_inv_id(inventory):
    return max((s["id"] for s in inventory), default=0) + 1

def next_emp_id(team):
    nums = [int(m["id"].replace("EMP","")) for m in team if m["id"].startswith("EMP")]
    return f"EMP{(max(nums, default=0)+1):03d}"

def disk_status(pct):
    if pct >= 85: return "Critical","critical"
    if pct >= 65: return "Warning","warning"
    return "Normal","normal"

def build_roster(team):
    roster = []
    for mi, member in enumerate(team):
        shifts = [SHIFT_CODES[(i + mi * 3) % len(SHIFT_CODES)] for i in range(31)]
        roster.append({"name": member["name"].split()[0], "shifts": shifts})
    return roster

def get_summary(data):
    inv  = data["inventory"]
    disk = data["disk"]
    team = data["team"]
    return {
        "active":   sum(1 for s in inv  if s["status"] == "Active"),
        "warning":  sum(1 for s in inv  if s["status"] == "Warning"),
        "inactive": sum(1 for s in inv  if s["status"] == "Inactive"),
        "highDisk": sum(1 for d in disk if d["pct"] >= 85),
        "teamSize": len(team),
    }

# ══════════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("admin"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    body     = request.get_json(force=True)
    username = body.get("username", "").strip()
    password = body.get("password", "")
    admins   = load_admins()
    if username in admins and admins[username] == password:
        session["logged_in"] = True
        session["username"]  = username
        session.permanent    = False
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Invalid username or password"}), 401

@app.route("/signup", methods=["GET"])
def signup():
    """Signup page — only accessible when already logged in as an admin."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("signup.html", current_user=session.get("username",""))

@app.route("/signup", methods=["POST"])
def signup_post():
    """Create a new admin account — requires existing admin session."""
    if not session.get("logged_in"):
        return jsonify({"ok": False, "error": "Unauthorised"}), 401
    body     = request.get_json(force=True)
    username = body.get("username", "").strip()
    password = body.get("password", "")
    confirm  = body.get("confirm", "")

    if not username or not password:
        return jsonify({"ok": False, "error": "Username and password are required"}), 400
    if len(username) < 3:
        return jsonify({"ok": False, "error": "Username must be at least 3 characters"}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": "Password must be at least 6 characters"}), 400
    if password != confirm:
        return jsonify({"ok": False, "error": "Passwords do not match"}), 400

    admins = load_admins()
    if username in admins:
        return jsonify({"ok": False, "error": f'Username "{username}" already exists'}), 409

    admins[username] = password
    save_admins(admins)
    return jsonify({"ok": True, "username": username}), 201

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    now = datetime.now().strftime("%d %b %Y, %H:%M")
    return render_template("index.html", now=now)

@app.route("/api/summary")
def api_summary():
    return jsonify(get_summary(load_data()))

@app.route("/api/inventory")
def api_inventory():
    return jsonify(load_data()["inventory"])

@app.route("/api/disk")
def api_disk():
    enriched = []
    for d in load_data()["disk"]:
        label, cls = disk_status(d["pct"])
        enriched.append({**d, "statusLabel": label, "statusClass": cls})
    return jsonify(enriched)

@app.route("/api/team")
def api_team():
    return jsonify(load_data()["team"])

@app.route("/api/roster")
def api_roster():
    data = load_data()
    return jsonify({"roster": build_roster(data["team"]), "weekdays": WEEKDAYS})

# ══════════════════════════════════════════════════════════════════════════════
# PROTECTED ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin")
@login_required
def admin():
    username = session.get("username", "Admin")
    admins   = load_admins()
    admin_count = len(admins)
    return render_template("admin.html", username=username, admin_count=admin_count)

@app.route("/api/admin/server", methods=["POST"])
@api_login_required
def add_server():
    body = request.get_json(force=True)
    data = load_data()
    body["id"] = next_inv_id(data["inventory"])
    total = int(body.get("diskTotal", 500))
    used  = int(body.get("diskUsed",  100))
    data["inventory"].append({k: v for k, v in body.items() if k not in ("diskTotal","diskUsed")})
    data["disk"].append({"hostname": body["hostname"], "total": total, "used": used,
                         "avail": total - used, "pct": round(used / total * 100)})
    save_data(data)
    return jsonify({"ok": True, "id": body["id"]}), 201

@app.route("/api/admin/server/<int:sid>", methods=["PUT"])
@api_login_required
def update_server(sid):
    body = request.get_json(force=True)
    data = load_data()
    for i, s in enumerate(data["inventory"]):
        if s["id"] == sid:
            data["inventory"][i] = {**s, **body, "id": sid}
            if "diskTotal" in body or "diskUsed" in body:
                total = int(body.get("diskTotal", 500))
                used  = int(body.get("diskUsed", 100))
                hn = data["inventory"][i]["hostname"]
                for j, d in enumerate(data["disk"]):
                    if d["hostname"] == hn:
                        data["disk"][j] = {"hostname": hn, "total": total, "used": used,
                                           "avail": total - used, "pct": round(used / total * 100)}
            save_data(data)
            return jsonify({"ok": True})
    abort(404)

@app.route("/api/admin/server/<int:sid>", methods=["DELETE"])
@api_login_required
def delete_server(sid):
    data = load_data()
    inv  = [s for s in data["inventory"] if s["id"] != sid]
    if len(inv) == len(data["inventory"]): abort(404)
    removed_hn = next((s["hostname"] for s in data["inventory"] if s["id"] == sid), None)
    data["inventory"] = inv
    if removed_hn:
        data["disk"] = [d for d in data["disk"] if d["hostname"] != removed_hn]
    save_data(data)
    return jsonify({"ok": True})

@app.route("/api/admin/member", methods=["POST"])
@api_login_required
def add_member():
    body = request.get_json(force=True)
    data = load_data()
    body["id"] = next_emp_id(data["team"])
    data["team"].append(body)
    save_data(data)
    return jsonify({"ok": True, "id": body["id"]}), 201

@app.route("/api/admin/member/<emp_id>", methods=["PUT"])
@api_login_required
def update_member(emp_id):
    body = request.get_json(force=True)
    data = load_data()
    for i, m in enumerate(data["team"]):
        if m["id"] == emp_id:
            data["team"][i] = {**m, **body, "id": emp_id}
            save_data(data)
            return jsonify({"ok": True})
    abort(404)

@app.route("/api/admin/member/<emp_id>", methods=["DELETE"])
@api_login_required
def delete_member(emp_id):
    data = load_data()
    team = [m for m in data["team"] if m["id"] != emp_id]
    if len(team) == len(data["team"]): abort(404)
    data["team"] = team
    save_data(data)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True, port=5000)