# 🖥️ ServerWatch — Project Structure

> **Live Demo:** [https://server-monitoring-dashboard-dbwz.onrender.com](https://server-monitoring-dashboard-dbwz.onrender.com)
> **Admin Panel:** [https://server-monitoring-dashboard-dbwz.onrender.com/admin](https://server-monitoring-dashboard-dbwz.onrender.com/admin)

---

## 📁 Full Directory Tree

```
server_monitoring_dashboard/
│
├── 📄 app.py                    ← Flask application — all routes, auth, API
├── 📄 data.json                 ← Auto-generated: servers, disk, team data
├── 📄 admins.json               ← Auto-generated: admin username/password store
├── 📄 requirements.txt          ← Python dependencies
├── 📄 render.yaml               ← Render deployment config
├── 📄 README.md                 ← Project documentation
├── 📄 .gitignore                ← Git ignore rules
│
├── 📂 static/
│   ├── 📂 css/
│   │   ├── style.css            ← Main dashboard styles (index.html)
│   │   └── theme.css            ← 🆕 Shared dark/light/auto theme tokens
│   │
│   └── 📂 js/
│       ├── main.js              ← Main dashboard logic (charts, tables, API calls)
│       └── theme.js             ← 🆕 Shared theme engine (all pages)
│
├── 📂 templates/
│   ├── index.html               ← Public dashboard — overview, inventory, disk, roster
│   ├── login.html               ← 🆕 Admin login page (session-based auth)
│   ├── signup.html              ← 🆕 Create new admin accounts (login required)
│   └── admin.html               ← 🔒 Protected admin CRUD panel
│
└── 📂 docs/
    └── dashboard-preview.svg    ← Dashboard preview image for README
```

---

## 🔗 URL Routes

| URL | Auth | Description |
|-----|------|-------------|
| `/` | Public | Main dashboard — server overview, disk monitoring, team, roster |
| `/login` | Public | Admin login form |
| `/logout` | Logged-in | Clears session → redirects to `/login` |
| `/signup` | 🔒 Login required | Create new admin accounts |
| `/admin` | 🔒 Login required | CRUD admin panel for servers and team members |

### API Endpoints

| Endpoint | Auth | Method | Description |
|----------|------|--------|-------------|
| `/api/summary` | Public | GET | Returns 5 KPI counts (active, warning, inactive, disk, team) |
| `/api/inventory` | Public | GET | Returns full server inventory list |
| `/api/disk` | Public | GET | Returns disk usage with severity labels |
| `/api/team` | Public | GET | Returns team members list |
| `/api/roster` | Public | GET | Returns 31-day shift schedule |
| `/api/admin/server` | 🔒 | POST | Add a new server |
| `/api/admin/server/<id>` | 🔒 | PUT | Update an existing server |
| `/api/admin/server/<id>` | 🔒 | DELETE | Delete a server |
| `/api/admin/member` | 🔒 | POST | Add a new team member |
| `/api/admin/member/<id>` | 🔒 | PUT | Update an existing team member |
| `/api/admin/member/<id>` | 🔒 | DELETE | Delete a team member |
| `/login` | Public | POST | Validate credentials → set session |
| `/signup` | 🔒 | POST | Create new admin account |

---

## 🗂️ File Responsibilities

### `app.py`
The Flask backend — does everything:
- Serves all HTML pages via `render_template()`
- Handles session-based login/logout/signup auth
- Exposes all public and protected API routes
- Reads/writes `data.json` for server + team data
- Reads/writes `admins.json` for admin credentials
- Protects `/admin` and `/api/admin/*` with `@login_required` decorator

### `data.json` *(auto-created)*
Stores all live application data:
```json
{
  "inventory": [ { "id": 1, "hostname": "smp-app01", ... } ],
  "disk":      [ { "hostname": "smp-app01", "pct": 62, ... } ],
  "team":      [ { "id": "EMP001", "name": "Sandeep Kumar", ... } ]
}
```
Created automatically on first run using default seed data.

### `admins.json` *(auto-created)*
Stores admin login credentials:
```json
{
  "admin": "serverwatch@2026"
}
```
New admins added via `/signup` are appended here.

### `static/css/theme.css` *(new)*
Shared CSS custom property tokens for dark and light themes.
Imported by every HTML page. Controls `--bg`, `--text`, `--surface`, etc.

### `static/js/theme.js` *(new)*
Shared JavaScript theme engine. Loaded by every page.
- Reads preference from `localStorage` key `sw-theme`
- Applies `data-theme="dark"` or `"light"` to `<html>`
- Auto-follows OS setting when mode is `"auto"`
- Exposes `setTheme('dark'|'light'|'auto')` globally
- Exposes `showToast(msg, type)` globally

### `static/css/style.css`
Dashboard-specific styles for `index.html` — charts, sidebar nav, tables, stat cards.

### `static/js/main.js`
Dashboard logic — fetches API data, renders charts, populates all tables on the main page.

### `templates/index.html`
The public-facing dashboard. Shows:
- KPI stat cards (active/warning/inactive/disk/team)
- Disk usage bar charts
- Server inventory table
- Team details table
- Monthly shift roster calendar

### `templates/login.html`
Admin login page at `/login`. Features:
- Username + password form
- Show/hide password toggle
- Dark / Light / Auto theme toggle
- Enter key support
- Animated error messages
- Hint box with default credentials

### `templates/signup.html`
Create new admin accounts at `/signup`. Features:
- Only accessible when already logged in
- Password strength meter (Weak → Strong)
- Live password requirements checklist
- Confirm password match indicator
- Creates entry in `admins.json`

### `templates/admin.html`
Protected CRUD admin panel at `/admin`. Features:
- Add / Edit / Delete servers (15 fields including disk)
- Add / Edit / Delete team members
- Live search for both tables
- Dark / Light / Auto theme toggle
- Username shown in sidebar
- Sign Out button
- Stats bar synced with live data

---

## 🔐 Authentication Flow

```
User visits /admin
      ↓
Session active? ──YES──→ Show admin panel
      │
      NO
      ↓
Redirect to /login
      ↓
User submits credentials
      ↓
POST /login → check admins.json
      ↓
Match? ──YES──→ Set session["logged_in"] = True → Redirect /admin
      │
      NO
      ↓
Return 401 → Show error on login page
```

### Signup flow
```
Admin visits /signup (must be logged in)
      ↓
Fills username + password + confirm
      ↓
POST /signup → validate → append to admins.json
      ↓
New admin can now log in at /login
```

---

## 🌗 Theme System

All 4 pages (index, login, signup, admin) share the same theme engine:

| Mode | Behaviour |
|------|-----------|
| 🌙 Dark | Forces dark theme regardless of OS |
| ☀️ Light | Forces light theme regardless of OS |
| ◑ Auto | Follows the user's OS/browser preference automatically |

- Preference saved to `localStorage` key `sw-theme`
- Switching theme on any page persists to all other pages
- Zero flash on page load (theme applied before render)

---

## 🚀 Deployment (Render)

### Required Environment Variables
Set these in Render → your service → **Environment**:

| Variable | Example Value | Purpose |
|----------|--------------|---------|
| `SECRET_KEY` | `xK9#mP2$qL8nR5vT7w` | Signs Flask session cookies |
| `ADMIN_USERNAME` | `admin` | *(Legacy — now stored in admins.json)* |
| `ADMIN_PASSWORD` | `serverwatch@2026` | *(Legacy — now stored in admins.json)* |

### `render.yaml`
```yaml
services:
  - type: web
    name: server-monitoring-dashboard
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
```

### `requirements.txt`
```
flask
gunicorn
```

---

## 🛠️ Local Development

```bash
# Clone the repo
git clone https://github.com/Diksha159457/server_monitoring_dashboard.git
cd server_monitoring_dashboard

# Create virtual environment
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
# venv\Scripts\activate    # Windows

# Install dependencies
pip install flask gunicorn

# Run the app
python app.py

# Open in browser
# http://localhost:5000
# http://localhost:5000/login   (admin: admin / serverwatch@2026)
```

---

## 📊 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 · Flask 3 · Gunicorn |
| Frontend | Vanilla HTML5 · CSS3 · JavaScript (ES2020) |
| Fonts | Inter (UI) · JetBrains Mono (code/IDs) |
| Icons | Font Awesome 6 |
| Storage | JSON files (`data.json`, `admins.json`) |
| Auth | Flask sessions (server-side, signed cookies) |
| Hosting | Render (free tier) |
| Theme | CSS custom properties + localStorage |

---

## 🔄 Data Flow

```
Browser
  ↓ GET /
Flask (app.py)
  ↓ render_template("index.html")
Browser renders HTML
  ↓ JavaScript fetch("/api/inventory")
Flask returns JSON from data.json
  ↓
JavaScript populates tables + charts
```

---

*Built by Diksha Shahi · IET, DDU Gorakhpur University · Dept. of Information Technology*