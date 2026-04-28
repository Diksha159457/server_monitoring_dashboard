/* ═══════════════════════════════════════════════════════════════════════════
   main.js  —  Frontend Controller for the Server Monitoring Dashboard
   Project  : SMP / SCMS Server Monitoring System
   SRS Ref  : §3.1 Layer 1 (Presentation Layer) + §3.2 (UI Interaction Logic)

   Architecture:
   ┌─────────────────────────────────────────────────────────────────────┐
   │  INIT         → DOMContentLoaded fires → initApp()                  │
   │  NAVIGATION   → nav clicks → showSection() + updatePageTitle()      │
   │  DATA FETCH   → fetch('/api/...') → JSON → render functions         │
   │  RENDER       → build HTML strings → inject via innerHTML           │
   │  FILTERS      → pill clicks + keyup search → re-render subset       │
   └─────────────────────────────────────────────────────────────────────┘
   ═══════════════════════════════════════════════════════════════════════════ */

"use strict";
// "use strict": Enables JavaScript strict mode — prevents silent errors, disallows undeclared variables,
// and throws exceptions for unsafe patterns (e.g., deleting non-deletable properties).

// ─────────────────────────────────────────────────────────────────────────────
// GLOBAL STATE — Module-level variables shared across render and filter functions
// ─────────────────────────────────────────────────────────────────────────────

let allInventory = [];      // Stores the full server inventory array from /api/inventory — used for client-side filtering
let allTeam      = [];      // Stores the full team members array from /api/team — used for client-side search filtering
let activeEnvFilter = "All"; // Tracks which environment pill button is currently selected; default = "All"

// ─────────────────────────────────────────────────────────────────────────────
// CONSTANTS — Reference lookups used across multiple render functions
// ─────────────────────────────────────────────────────────────────────────────

// ENV_COLORS: Maps environment names to their hex accent colors — used for env badge CSS and env tile borders
const ENV_COLORS = {
  Production: "#f85149",  // Red — production is the most critical environment
  UAT:        "#d29922",  // Amber — user-acceptance testing is pre-production
  DR:         "#bc8cff",  // Purple — disaster recovery environment
  Dev:        "#58a6ff",  // Blue — development environment
  Hotfix:     "#db2777",  // Pink — emergency hotfix environment
  E2E:        "#39d353",  // Green — end-to-end testing environment
};

// SHIFT_COLORS: Maps each shift code to its background and text color for the roster calendar cells
const SHIFT_COLORS = {
  G:  { bg: "#1f3a5f", text: "#58a6ff",  label: "General"       }, // Blue tones — standard daytime shift
  M1: { bg: "#1a3d2b", text: "#3fb950",  label: "Mid-Shift"     }, // Green tones — afternoon shift
  E:  { bg: "#3d3000", text: "#d29922",  label: "Early"         }, // Amber tones — early morning shift
  N:  { bg: "#2d1f4d", text: "#bc8cff",  label: "Night"         }, // Purple tones — overnight shift
  CO: { bg: "#3d1f35", text: "#f778ba",  label: "Comp Off"      }, // Pink tones — compensatory day off
  PL: { bg: "#3d1515", text: "#f85149",  label: "Planned Leave" }, // Red tones — pre-approved leave
};

function applyTheme(t){
  if(t==='auto'){
    t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
  }
  document.documentElement.setAttribute('data-theme',t);
  document.getElementById('btn-dark') ?.style && (document.getElementById('btn-dark').style.background  = t==='dark' ?'#3b82f6':'transparent');
  document.getElementById('btn-light')?.style && (document.getElementById('btn-light').style.background = t==='light'?'#3b82f6':'transparent');
  document.getElementById('btn-auto') ?.style && (document.getElementById('btn-auto').style.background  = localStorage.getItem('sw-theme')==='auto'?'#3b82f6':'transparent');
}
function setTheme(t){ localStorage.setItem('sw-theme',t); applyTheme(t); }
(function(){
  applyTheme(localStorage.getItem('sw-theme')||'auto');
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{
    if((localStorage.getItem('sw-theme')||'auto')==='auto') applyTheme('auto');
  });
})();

// PAGE_TITLES: Maps section IDs to the display text shown in the topbar page-title element
const PAGE_TITLES = {
  overview:  "Dashboard Overview",    // Title shown when the Overview section is active
  inventory: "Server Inventory",      // Title shown when the Inventory section is active
  disk:      "Disk Usage Monitoring", // Title shown when the Disk Monitoring section is active
  team:      "Team Details",          // Title shown when the Team Details section is active
  roster:    "Team Roster",           // Title shown when the Team Roster section is active
};

// ─────────────────────────────────────────────────────────────────────────────
// UTILITY FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * envBadgeClass — Returns the CSS badge class for a given environment string
 * Used in the Inventory table to color-code the Environment column cells
 */
function envBadgeClass(env) {
  const map = {            // Maps each environment name to its corresponding CSS badge class
    Production: "badge-prod",   // Red badge class for Production
    UAT:        "badge-uat",    // Amber badge class for UAT
    DR:         "badge-dr",     // Purple badge class for DR
    Dev:        "badge-dev",    // Blue badge class for Dev
  };
  return map[env] || "badge-dev"; // Falls back to "badge-dev" if env is not found in the map
}

/**
 * statusBadgeClass — Returns the CSS badge class for a given server status string
 * Used in the Inventory table to color-code the Status column cells
 */
function statusBadgeClass(status) {
  const map = {               // Maps each status string to its CSS badge class
    Active:   "badge-active",   // Green badge class for Active servers
    Warning:  "badge-warning",  // Amber badge class for Warning servers
    Inactive: "badge-inactive", // Red badge class for Inactive servers
  };
  return map[status] || "";  // Returns empty string if status is unrecognised (no badge styling)
}

/**
 * diskFillClass — Returns the CSS class for the progress bar fill based on disk percentage
 * Used in disk progress bars to color the fill according to SRS §5.2 thresholds
 */
function diskFillClass(pct) {
  if (pct >= 85) return "fill-critical";  // ≥85%: red fill — critical threshold per SRS §5.2
  if (pct >= 65) return "fill-warning";   // ≥65%: amber fill — warning threshold
  return "fill-normal";                   // <65%: green fill — normal/healthy
}

/**
 * diskTextClass — Returns the CSS class for coloring text (stats label and pct%) by disk severity
 */
function diskTextClass(pct) {
  if (pct >= 85) return "critical";  // Red text class for critical disk usage
  if (pct >= 65) return "warning";   // Amber text class for warning disk usage
  return "normal";                   // Green text class for normal disk usage
}

// ─────────────────────────────────────────────────────────────────────────────
// NAVIGATION — Section switching and page title updates
// ─────────────────────────────────────────────────────────────────────────────

/**
 * showSection — Makes the target section visible and hides all others
 * Also updates the "active" class on the sidebar nav links for highlight styling
 * @param {string} sectionId — The id suffix of the target section (e.g., "overview")
 */
function showSection(sectionId) {
  // Hide all content sections by removing the "active" class from each
  document.querySelectorAll(".content-section").forEach(sec => {
    sec.classList.remove("active"); // Removes "active" → display:none is re-applied → section hides
  });

  // Show the target section by adding the "active" class to it
  const target = document.getElementById("section-" + sectionId);  // Constructs the full element id (e.g., "section-overview")
  if (target) target.classList.add("active");                        // Adds "active" → display:block → section becomes visible

  // Update the highlighted state on all sidebar nav links
  document.querySelectorAll(".nav-link").forEach(link => {
    link.classList.remove("active"); // Remove "active" from all nav links first (clears previous selection)
  });

  // Add "active" class back to only the clicked nav link
  const activeLink = document.querySelector(`.nav-link[data-section="${sectionId}"]`);
  // CSS attribute selector: finds the nav link whose data-section attribute matches the target sectionId
  if (activeLink) activeLink.classList.add("active"); // Highlights this nav link with the blue active style

  // Update the topbar page title to match the newly active section
  const titleEl = document.getElementById("pageTitle");   // Gets the h1 element showing the page name
  if (titleEl) titleEl.textContent = PAGE_TITLES[sectionId] || "Dashboard"; // Sets title text from the lookup map
}

// ─────────────────────────────────────────────────────────────────────────────
// RENDER FUNCTIONS — Each function fetches data and injects HTML into the DOM
// ─────────────────────────────────────────────────────────────────────────────

/**
 * renderSummary — Fetches /api/summary and injects five KPI stat cards
 * into the #statCards container on the Overview page (SRS §5.1)
 */
async function renderSummary() {
  const res  = await fetch("/api/summary");   // Makes an HTTP GET request to Flask's /api/summary endpoint
  const data = await res.json();              // Parses the JSON response body into a JavaScript object

  // Define the five stat cards as an array of config objects
  const cards = [
    { icon: "✅", label: "Active Servers",  value: data.active,   sub: "Running normally", color: "#3fb950" }, // Green accent for healthy servers
    { icon: "⚠️", label: "Warning",         value: data.warning,  sub: "Needs attention",  color: "#d29922" }, // Amber accent for servers needing review
    { icon: "🔴", label: "Inactive",        value: data.inactive, sub: "Offline / DR",     color: "#f85149" }, // Red accent for offline servers
    { icon: "💾", label: "High Disk Usage", value: data.highDisk, sub: "≥85% utilized",    color: "#bc8cff" }, // Purple accent for critical disk usage
    { icon: "👥", label: "Team Members",    value: data.teamSize, sub: "IT Personnel",     color: "#58a6ff" }, // Blue accent for headcount
  ];

  // Build the HTML string for all five cards by mapping over the cards array
  const html = cards.map(c => `
    <div class="stat-card" style="border-left-color:${c.color}">
      <!-- stat-card div: individual KPI card; border-left-color uses the card's accent color -->
      <div class="stat-icon">${c.icon}</div>
      <!-- stat-icon: Large emoji representing the metric category -->
      <div class="stat-value">${c.value}</div>
      <!-- stat-value: Large bold numeric count (e.g., 6 active servers) -->
      <div class="stat-label">${c.label}</div>
      <!-- stat-label: Metric name below the count (e.g., "Active Servers") -->
      <div class="stat-sub">${c.sub}</div>
      <!-- stat-sub: Descriptive subtitle (e.g., "Running normally") -->
    </div>
  `).join("");  // join("") converts the array of HTML strings into a single string with no separator

  document.getElementById("statCards").innerHTML = html;
  // Injects the constructed HTML into the #statCards container — replaces any previous content
}

/**
 * renderDiskSummary — Fetches /api/disk and renders compact progress-bar rows
 * into #diskSummaryBars on the Overview page for a quick visual disk overview
 */
async function renderDiskSummary() {
  const res  = await fetch("/api/disk");   // Fetches enriched disk data from Flask's /api/disk endpoint
  const data = await res.json();           // Parses the JSON response into an array of disk objects

  // Build one progress-bar row per server disk record
  const html = data.map(d => `
    <div class="disk-bar-row">
      <!-- disk-bar-row: Container for one server's label line + progress bar -->
      <div class="disk-bar-label">
        <!-- disk-bar-label: Flex row with hostname on left and stats on right -->
        <span class="hostname">${d.hostname}</span>
        <!-- hostname: Monospace server hostname on the left of the label row -->
        <span class="stats ${diskTextClass(d.pct)}">${d.pct}% &nbsp; ${d.used}GB / ${d.total}GB</span>
        <!-- stats: Percentage and GB values on the right, colored by severity class -->
        <!-- diskTextClass(d.pct) returns "critical", "warning", or "normal" CSS class -->
      </div>
      <div class="progress-track">
        <!-- progress-track: Full-width grey bar track container -->
        <div class="progress-fill ${diskFillClass(d.pct)}" style="width:${d.pct}%"></div>
        <!-- progress-fill: Colored fill element; width = utilization %; color class from diskFillClass() -->
      </div>
    </div>
  `).join(""); // Joins all row strings into one HTML block

  document.getElementById("diskSummaryBars").innerHTML = html;
  // Injects all progress-bar rows into the #diskSummaryBars container
}

/**
 * renderEnvTiles — Counts servers per environment using allInventory and renders tiles
 * into #envTiles on the Overview page showing server counts per deployment environment
 */
function renderEnvTiles() {
  const envs = ["Production", "UAT", "DR", "Dev"];  // Four main environments to count and display

  // Build one tile per environment
  const html = envs.map(env => {
    const count = allInventory.filter(s => s.env === env).length;  // Count servers belonging to this environment
    const color = ENV_COLORS[env] || "#58a6ff";                     // Look up the accent color; fallback to blue
    return `
      <div class="env-tile" style="border-top-color:${color}">
        <!-- env-tile: Individual environment count tile; top border uses the env's accent color -->
        <div class="env-count" style="color:${color}">${count}</div>
        <!-- env-count: Large number showing how many servers are in this environment; colored by env -->
        <div class="env-label">${env}</div>
        <!-- env-label: Small label below the count showing the environment name -->
      </div>
    `;
  }).join(""); // Joins all tile strings into one HTML block

  document.getElementById("envTiles").innerHTML = html;
  // Injects all environment tiles into the #envTiles container
}

/**
 * renderInventory — Fetches /api/inventory, builds the server inventory table,
 * and injects filter pill buttons. Stores data in allInventory for re-filtering.
 * Implements SRS §5.3 Server Inventory Management Module.
 */
async function renderInventory() {
  const res  = await fetch("/api/inventory");  // Fetches the full server inventory list from Flask
  allInventory = await res.json();              // Stores parsed array globally for use by filter/search functions
  renderEnvTiles();                             // Renders environment tiles now that inventory data is available

  // Build environment filter pill buttons
  const envs = ["All", "Production", "UAT", "DR", "Dev"];  // Full list of filter options
  const pillsHtml = envs.map(e => `
    <button class="pill-btn ${e === activeEnvFilter ? "active" : ""}"
            style="${e !== "All" ? `background:${e === activeEnvFilter ? ENV_COLORS[e] : "transparent"}` : e === activeEnvFilter ? "background:#58a6ff;color:white" : ""}"
            data-env="${e}" onclick="setEnvFilter('${e}')">
    <!-- pill-btn: Filter button; "active" class highlights the selected environment
         data-env: Stores the environment name for reference
         onclick: Calls setEnvFilter() with this environment when clicked -->
      ${e}
    </button>
  `).join(""); // Joins all pill button strings

  document.getElementById("envFilters").innerHTML = pillsHtml;
  // Injects the filter pill buttons into the #envFilters container

  renderInventoryTable(); // Renders the actual table rows with the current filter applied
}

/**
 * renderInventoryTable — Applies the current env filter and search query to allInventory,
 * then rebuilds the table body and row count footer.
 * Called on initial load and on every filter/search change.
 */
function renderInventoryTable() {
  const search = document.getElementById("inventorySearch").value.toLowerCase();
  // Gets the current search text; toLowerCase() for case-insensitive comparison

  // Filter allInventory: keep servers matching both the active environment pill and the search string
  const filtered = allInventory.filter(s => {
    const matchEnv = activeEnvFilter === "All" || s.env === activeEnvFilter;
    // matchEnv: True if "All" is selected or this server's env matches the active filter

    const matchSearch = !search ||                                // No search = all pass
      s.app.toLowerCase().includes(search) ||                    // Match: application name contains search text
      s.ip.includes(search)               ||                     // Match: IP address contains search text
      s.hostname.toLowerCase().includes(search);                 // Match: hostname contains search text

    return matchEnv && matchSearch;  // Server must satisfy both conditions to appear in the table
  });

  // Build one <tr> per filtered server
  const rows = filtered.map((s, i) => `
    <tr>
      <td><strong>${s.team}</strong></td>
      <!-- Team name in bold: SMP or SCMS -->
      <td>${s.app}</td>
      <!-- Application or server display name -->
      <td class="mono">${s.ip}</td>
      <!-- IP address in monospace font for digit alignment; "mono" CSS class applies JetBrains Mono -->
      <td class="mono">${s.hostname}</td>
      <!-- Hostname in monospace for consistent character width -->
      <td><span class="badge ${envBadgeClass(s.env)}">${s.env}</span></td>
      <!-- Environment cell: colored badge using envBadgeClass() to select the right CSS class -->
      <td><span class="badge ${statusBadgeClass(s.status)}">${s.status}</span></td>
      <!-- Status cell: colored badge using statusBadgeClass() — Active/Warning/Inactive -->
      <td>${s.osType}</td>
      <!-- OS family: "Linux RHEL" or "Windows" -->
      <td class="mono">${s.osVer}</td>
      <!-- OS version in monospace for numeric version alignment -->
      <td>${s.tech}</td>
      <!-- Technology stack: Java, Oracle, Nginx, MSSQL, Node.js, .NET -->
      <td>${s.category}</td>
      <!-- Server category: App, DB, or Web -->
      <td class="mono">${s.memory}</td>
      <!-- RAM in monospace: e.g., "16 GB" -->
      <td class="mono">${s.cpu}</td>
      <!-- CPU core count in monospace -->
      <td>${s.hw}</td>
      <!-- Hardware type: "Physical" or "VM" -->
    </tr>
  `).join(""); // Joins all row strings into one HTML block

  document.getElementById("inventoryBody").innerHTML = rows || `
    <tr><td colspan="13" style="text-align:center;padding:24px;color:#484f58">
      No servers match the current filter.
    </td></tr>
  `;
  // Injects rows into the table body, OR shows an empty-state message if no servers matched

  document.getElementById("inventoryCount").textContent =
    `Showing ${filtered.length} of ${allInventory.length} servers`;
  // Updates the footer text to tell the user how many servers are currently visible
}

/**
 * setEnvFilter — Updates the active environment filter and re-renders the inventory table
 * @param {string} env — The selected environment name (e.g., "Production" or "All")
 */
function setEnvFilter(env) {
  activeEnvFilter = env;   // Updates the global active filter state

  // Update pill button appearance: "active" class + filled background on the selected pill
  document.querySelectorAll(".pill-btn").forEach(btn => {
    const isActive = btn.dataset.env === env;       // True if this button matches the newly selected env
    btn.classList.toggle("active", isActive);        // Adds "active" if isActive, removes it otherwise

    // Update the background color: selected pill gets solid env color, others are transparent
    if (btn.dataset.env === "All") {
      btn.style.background = isActive ? "#58a6ff" : "transparent";  // Blue for "All" when active
      btn.style.color      = isActive ? "white" : "";               // White text when active, default otherwise
    } else {
      const envColor = ENV_COLORS[btn.dataset.env];                  // Looks up the env's accent color
      btn.style.background = isActive ? envColor : "transparent";    // Solid color when active, transparent otherwise
      btn.style.color      = isActive ? "white" : "";                // White text when active
    }
  });

  renderInventoryTable();  // Re-renders the table with the updated filter applied
}

/**
 * renderDisk — Fetches /api/disk and renders the full Disk Usage Monitoring table
 * with progress bars and severity badges. Implements SRS §5.2.
 */
async function renderDisk() {
  const res  = await fetch("/api/disk");  // Fetches enriched disk data (with statusLabel/statusClass) from Flask
  const data = await res.json();          // Parses JSON response into an array of disk objects

  // Build one <tr> per server disk record
  const rows = data.map((d, i) => `
    <tr>
      <td class="mono"><strong>${d.hostname}</strong></td>
      <!-- Hostname cell: bold monospace text for the server identifier -->
      <td class="mono">${d.total}</td>
      <!-- Total disk capacity in GB -->
      <td class="mono ${diskTextClass(d.pct)}">${d.used}</td>
      <!-- Used space in GB, colored by severity (diskTextClass returns critical/warning/normal) -->
      <td class="mono">${d.avail}</td>
      <!-- Available free space in GB -->
      <td>
        <div class="bar-cell">
        <!-- bar-cell: Flex row container for the progress bar + percentage label -->
          <div class="progress-track">
          <!-- progress-track: Grey pill-shaped bar container -->
            <div class="progress-fill ${diskFillClass(d.pct)}" style="width:${d.pct}%"></div>
            <!-- progress-fill: Colored fill, width = pct%, class sets red/amber/green color -->
          </div>
          <span class="pct-label ${diskTextClass(d.pct)}">${d.pct}%</span>
          <!-- pct-label: Percentage number to the right of the bar, colored by severity -->
        </div>
      </td>
      <td>
        <span class="badge badge-${d.statusClass === "critical" ? "critical" : d.statusClass === "warning" ? "warning-d" : "normal"}">
        <!-- Status badge: CSS class selected based on Flask-computed statusClass field
             "warning-d" is a distinct class from the server-status "warning" to avoid selector conflicts -->
          ${d.statusLabel}
          <!-- statusLabel: "Critical", "Warning", or "Normal" text inside the badge -->
        </span>
      </td>
    </tr>
  `).join(""); // Joins all row strings into one HTML block

  document.getElementById("diskBody").innerHTML = rows;
  // Injects the disk usage table rows into the #diskBody tbody element
}

/**
 * renderTeam — Fetches /api/team and renders the Team Details table.
 * Stores data in allTeam for client-side search filtering. Implements SRS §5.4.
 */
async function renderTeam() {
  const res = await fetch("/api/team");  // Fetches team member list from Flask's /api/team endpoint
  allTeam = await res.json();             // Stores parsed array globally for use by the search filter function
  renderTeamTable();                      // Renders the initial table with no search filter applied
}

/**
 * renderTeamTable — Applies the current search query to allTeam and rebuilds the team table body.
 * Called on initial load and on every keystroke in the team search input.
 */
function renderTeamTable() {
  const search = document.getElementById("teamSearch").value.toLowerCase();
  // Gets the current team search text and lowercases it for case-insensitive comparison

  // Filter allTeam: keep employees whose name, project, or ID contains the search text
  const filtered = allTeam.filter(m =>
    !search ||                                           // No search = show all employees
    m.name.toLowerCase().includes(search) ||             // Match by full name (case-insensitive)
    m.project.toLowerCase().includes(search) ||          // Match by project name: "smp" or "scms"
    m.id.toLowerCase().includes(search)                  // Match by employee ID: "emp001" etc.
  );

  // Build one <tr> per filtered team member
  const rows = filtered.map(m => `
    <tr>
      <td class="mono" style="color:#58a6ff;font-weight:700">${m.id}</td>
      <!-- Employee ID: blue bold monospace text for quick visual lookup -->
      <td><strong>${m.name}</strong></td>
      <!-- Full employee name in bold -->
      <td class="mono">${m.doj}</td>
      <!-- Date of joining in ISO format, monospace for date digit alignment -->
      <td>
        <span class="badge ${m.project === "SMP" ? "badge-smp" : "badge-scms"}">${m.project}</span>
        <!-- Project badge: blue for SMP, green for SCMS — clearly distinguishes the two teams -->
      </td>
      <td class="mono">${m.contact}</td>
      <!-- Phone number in monospace for consistent digit spacing -->
      <td style="color:#58a6ff">${m.email}</td>
      <!-- Email address styled in accent blue to visually suggest it's a link/contact point -->
    </tr>
  `).join(""); // Joins all row strings into one HTML block

  document.getElementById("teamBody").innerHTML = rows || `
    <tr><td colspan="6" style="text-align:center;padding:24px;color:#484f58">
      No team members match your search.
    </td></tr>
  `;
  // Injects rows OR shows an empty-state message if no employees match the search
}

/**
 * renderRoster — Fetches /api/roster and builds the full 31-column shift calendar.
 * Also injects the shift code legend. Implements SRS §5.4 shift scheduling feature.
 */
async function renderRoster() {
  const res  = await fetch("/api/roster");  // Fetches roster data from Flask's /api/roster endpoint
  const data = await res.json();            // Parses JSON: { roster: [...], weekdays: [...] }

  // ── Build the Shift Code Legend ────────────────────────────────────────────
  const legendHtml = Object.entries(SHIFT_COLORS).map(([code, sc]) => `
    <span class="shift-badge" style="background:${sc.bg};color:${sc.text}">
    <!-- shift-badge: Small colored pill for one shift type; uses inline styles from SHIFT_COLORS -->
      ${code} – ${sc.label}
      <!-- Displays the shift code and its full name (e.g., "G – General") -->
    </span>
  `).join(""); // Joins all legend badge strings

  document.getElementById("shiftLegend").innerHTML = legendHtml;
  // Injects all shift legend badges into the #shiftLegend flex container

  // ── Build the Calendar Header Row (Name + 31 day columns) ─────────────────
  const headerCells = data.weekdays.map((wd, i) => {
    const dayNum = i + 1;                           // Day number (1–31) from the index
    const isWeekend = wd === "S";                   // True if this day is Saturday or Sunday
    return `
      <th class="${isWeekend ? "weekend" : ""}">
      <!-- th: One column header per day; "weekend" class applies darker background for Sat/Sun -->
        <div>${dayNum}</div>
        <!-- Day number shown in bold in the header -->
        <div style="font-size:9px;opacity:0.6">${wd}</div>
        <!-- Weekday letter (M/T/W/T/F/S) shown smaller below the day number -->
      </th>
    `;
  }).join(""); // Joins all 31 day header cells

  document.getElementById("rosterHead").innerHTML = `
    <tr>
      <th>Name</th>
      <!-- Fixed "Name" column header — sticky positioning keeps this visible during horizontal scroll -->
      ${headerCells}
      <!-- 31 day column headers injected here -->
    </tr>
  `;
  // Injects the complete header row into the #rosterHead thead element

  // ── Build the Calendar Body Rows (one row per team member) ────────────────
  const bodyRows = data.roster.map((row, ri) => {
    // Build 31 shift-code cells for this employee
    const cells = row.shifts.map((code, di) => {
      const sc = SHIFT_COLORS[code] || { bg: "#21262d", text: "#8b949e" };
      // Looks up shift colors; falls back to grey if code is unrecognised

      const isWeekend = data.weekdays[di] === "S";  // True if this day column is a weekend
      return `
        <td class="${isWeekend ? "weekend" : ""}">
        <!-- td: One cell per day; "weekend" class applies subtle weekend tint -->
          <span class="shift-cell" style="background:${sc.bg};color:${sc.text}">
          <!-- shift-cell: Small colored badge showing the shift code; inline styles from SHIFT_COLORS -->
            ${code}
            <!-- The 1–2 character shift code (G, M1, E, N, CO, PL) -->
          </span>
        </td>
      `;
    }).join(""); // Joins all 31 cells for this employee's row

    return `
      <tr>
        <td>${row.name}</td>
        <!-- Sticky first-name cell: stays visible when scrolling right through all 31 day columns -->
        ${cells}
        <!-- 31 shift cells for this employee's month schedule -->
      </tr>
    `;
  }).join(""); // Joins all employee row strings into one HTML block

  document.getElementById("rosterBody").innerHTML = bodyRows;
  // Injects all roster rows into the #rosterBody tbody element
}

// ─────────────────────────────────────────────────────────────────────────────
// MOBILE SIDEBAR TOGGLE
// ─────────────────────────────────────────────────────────────────────────────

/**
 * initMobileMenu — Attaches a click listener to the mobile hamburger button
 * to toggle the "open" class on the sidebar (slides it in/out on narrow screens)
 */
function initMobileMenu() {
  const toggleBtn = document.getElementById("menuToggle"); // Gets the hamburger button element
  const sidebar   = document.getElementById("sidebar");    // Gets the sidebar aside element

  if (toggleBtn && sidebar) {                      // Guard: only proceed if both elements exist in the DOM
    toggleBtn.addEventListener("click", () => {    // Attaches a click event listener to the toggle button
      sidebar.classList.toggle("open");             // "open" adds left:0 to slide sidebar on-screen; removes it to slide off
    });
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// NAVIGATION EVENT BINDING
// ─────────────────────────────────────────────────────────────────────────────

/**
 * initNavigation — Attaches click handlers to all sidebar nav links
 * On click: prevents default anchor navigation, shows the correct section,
 * and lazy-loads its data if needed.
 */
function initNavigation() {
  document.querySelectorAll(".nav-link").forEach(link => {
    // querySelectorAll returns a NodeList of all elements with class "nav-link"
    // forEach iterates over each nav link to attach an individual click listener

    link.addEventListener("click", async (e) => {
      e.preventDefault();
      // Prevents the default anchor (<a href="#">) behavior — stops the page from scrolling to the top

      const section = link.dataset.section;
      // Reads the data-section attribute from the clicked link (e.g., "inventory")

      showSection(section);
      // Switches the visible content section and updates the topbar title and nav highlight

      // Lazy-load section data when the user first navigates to it
      // Each case calls the appropriate render function once the section becomes active
      if (section === "inventory") await renderInventory();  // Loads server inventory data on demand
      if (section === "disk")      await renderDisk();       // Loads disk usage data on demand
      if (section === "team")      await renderTeam();       // Loads team member data on demand
      if (section === "roster")    await renderRoster();     // Loads roster calendar data on demand
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SEARCH INPUT EVENT BINDING
// ─────────────────────────────────────────────────────────────────────────────

/**
 * initSearch — Attaches keyup listeners to both search inputs
 * so the table re-filters in real time with every keystroke
 */
function initSearch() {
  const invSearch = document.getElementById("inventorySearch");
  // Gets the search input in the Server Inventory section

  if (invSearch) {
    invSearch.addEventListener("keyup", renderInventoryTable);
    // "keyup" fires after each key press — calls renderInventoryTable() to re-filter the inventory rows
  }

  const teamSearch = document.getElementById("teamSearch");
  // Gets the search input in the Team Details section

  if (teamSearch) {
    teamSearch.addEventListener("keyup", renderTeamTable);
    // "keyup" fires after each key press — calls renderTeamTable() to re-filter the team rows
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// APPLICATION INITIALISATION
// ─────────────────────────────────────────────────────────────────────────────

/**
 * initApp — Main entry point called once the DOM is fully loaded
 * Orchestrates setup of navigation, mobile menu, search, and initial data rendering
 */
async function initApp() {
  initNavigation();    // Binds click handlers to all sidebar nav links
  initMobileMenu();    // Binds the mobile hamburger toggle click handler
  initSearch();        // Binds keyup handlers to inventory and team search inputs

  // Load initial data for the Overview page (default visible section on startup)
  await renderSummary();     // Fetches /api/summary and renders the five KPI stat cards
  await renderInventory();   // Fetches /api/inventory → needed for env tiles on Overview
  await renderDiskSummary(); // Fetches /api/disk and renders the mini progress bars on Overview
}

// ─────────────────────────────────────────────────────────────────────────────
// ENTRY POINT — DOM Ready Listener
// ─────────────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", initApp);
// DOMContentLoaded fires when the browser has fully parsed the HTML document and built the DOM tree
// (but before images and stylesheets have finished loading — fast and reliable for DOM manipulation)
// Calls initApp() which bootstraps the entire frontend application
