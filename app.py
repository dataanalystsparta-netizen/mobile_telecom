from __future__ import annotations

import re
from datetime import date, datetime
from html import escape

import streamlit as st
from supabase import create_client


LOGO_URL = "https://raw.githubusercontent.com/dataanalystsparta-netizen/logos/refs/heads/main/Gemini_Generated_Image_f8e0idf8e0idf8e0.png"


# =========================================================
# PAGE CONFIGURATION + VISUAL SYSTEM
# =========================================================
st.set_page_config(
    page_title="Sparta Mobile CRM",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_crm_theme() -> None:
    """Visual styling only: no business rules or database behaviour here."""
    st.markdown(
        """
        <style>
        :root {
            --crm-ink: #17263c;
            --crm-muted: #68788e;
            --crm-border: #e3e9f2;
            --crm-canvas: #f5f7fb;
            --crm-surface: #ffffff;
            --crm-primary: #4169e1;
            --crm-primary-dark: #2d4fb8;
            --crm-teal: #0f8b82;
        }
        html, body, [class*="css"] {
            font-family: Inter, "Segoe UI", system-ui, -apple-system, sans-serif;
        }
        .stApp {
            background: var(--crm-canvas);
            color: var(--crm-ink);
        }
        [data-testid="stHeader"] {
            background: rgba(245,247,251,.88);
            backdrop-filter: blur(12px);
        }
        [data-testid="stToolbar"] { right: 1.3rem; }
        .main .block-container {
            max-width: 1540px;
            padding-top: 1.65rem;
            padding-bottom: 3rem;
            padding-left: clamp(1.1rem, 3vw, 3.1rem);
            padding-right: clamp(1.1rem, 3vw, 3.1rem);
        }
        h1, h2, h3, h4 { color: var(--crm-ink); letter-spacing: -0.035em; }
        h1 { font-weight: 760; }
        h2, h3 { font-weight: 720; }
        p, li, label { line-height: 1.55; }
        [data-testid="stCaptionContainer"] { color: var(--crm-muted); }
        [data-testid="stSidebar"] {
            background: linear-gradient(165deg, #172941 0%, #102033 65%, #0b1828 100%);
            border-right: 1px solid rgba(255,255,255,.08);
        }
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.3rem; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] small { color: #eaf0fa !important; }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #a9bad0 !important; }
        [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.15); }
        [data-testid="stSidebar"] [data-testid="stRadio"] > label { display: none; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            border-radius: 10px;
            padding: .42rem .55rem;
            margin: .10rem 0;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background: rgba(255,255,255,.08);
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label p { font-weight: 560; }
        [data-testid="stSidebar"] [data-testid="stRadio"] input:checked + div { color: #fff; }
        [data-testid="stSidebar"] .stButton button {
            color: #f8fbff !important;
            background: rgba(255,255,255,.09) !important;
            border: 1px solid rgba(255,255,255,.18) !important;
        }
        [data-testid="stSidebar"] .stButton button:hover { background: rgba(255,255,255,.16) !important; }
        .crm-brand {
            display: flex; align-items: center; gap: .75rem;
            padding: .4rem .15rem .8rem;
        }
        .crm-brand-logo {
            width: 46px; height: 46px; flex: 0 0 46px; object-fit: contain;
            border-radius: 13px; padding: 3px; background: #fff;
            border: 1px solid rgba(255,255,255,.28);
            box-shadow: 0 8px 22px rgba(4,12,28,.24);
        }
        .crm-brand-name { font-size: 1.05rem; font-weight: 760; letter-spacing: -.025em; }
        .crm-brand-sub { color: #a9bad0; font-size: .74rem; margin-top: .12rem; }
        .crm-nav-label {
            color: #91a5bf; font-size: .68rem; font-weight: 800;
            letter-spacing: .14em; margin: 1.05rem .2rem .4rem;
        }
        .crm-user-card {
            border: 1px solid rgba(255,255,255,.13);
            background: rgba(255,255,255,.055); border-radius: 14px;
            padding: .9rem .85rem; margin-top: .3rem;
        }
        .crm-user-name { color: #fff; font-weight: 700; font-size: .94rem; }
        .crm-user-meta { color: #b7c7d9; font-size: .76rem; margin-top: .24rem; line-height: 1.5; }
        .crm-page-header {
            display: flex; justify-content: space-between; align-items: center; gap: 1rem;
            padding: 1.45rem 1.65rem; margin: 0 0 1.5rem;
            background: linear-gradient(120deg, #ffffff 0%, #f8faff 72%, #eef3ff 100%);
            border: 1px solid #e1e8f5; border-radius: 18px;
            box-shadow: 0 5px 22px rgba(28,48,84,.035);
        }
        .crm-eyebrow { color: var(--crm-primary); font-size: .68rem; font-weight: 850; letter-spacing: .15em; text-transform: uppercase; }
        .crm-page-title { color: var(--crm-ink); font-size: clamp(1.55rem, 2.2vw, 2.15rem); font-weight: 800; letter-spacing: -.055em; line-height: 1.18; margin-top: .35rem; }
        .crm-page-subtitle { color: var(--crm-muted); font-size: .91rem; margin-top: .42rem; }
        .crm-user-pill {
            display: inline-flex; align-items: center; gap: .45rem; white-space: nowrap;
            color: #304c8f; background: #edf2ff; border: 1px solid #dce5ff;
            border-radius: 999px; padding: .55rem .8rem; font-size: .75rem; font-weight: 750;
        }
        .crm-section-head { margin: .15rem 0 1rem; }
        .crm-section-kicker { font-size: .68rem; color: var(--crm-primary); text-transform: uppercase; letter-spacing: .13em; font-weight: 850; }
        .crm-section-title { font-size: 1.35rem; color: var(--crm-ink); font-weight: 780; letter-spacing: -.04em; margin-top: .25rem; }
        .crm-section-copy { font-size: .86rem; color: var(--crm-muted); margin-top: .25rem; }
        .crm-panel {
            background: #fff; border: 1px solid var(--crm-border); border-radius: 15px;
            padding: 1rem 1.1rem; box-shadow: 0 3px 12px rgba(25,47,82,.025);
        }
        .crm-soft-note { background: #f0f5ff; border: 1px solid #dce6ff; border-radius: 12px; padding: .8rem 1rem; color: #40557f; font-size: .86rem; }
        .crm-login-title { font-size: 2.15rem; font-weight: 820; letter-spacing: -.06em; line-height: 1.12; color: var(--crm-ink); }
        .crm-login-copy { color: var(--crm-muted); font-size: .95rem; margin: .65rem 0 1.3rem; }
        .crm-login-logo {
            width: 78px; height: 78px; object-fit: contain; display: block;
            border-radius: 21px; padding: 5px; background: #fff;
            border: 1px solid #e3e9f2;
            box-shadow: 0 10px 28px rgba(24,43,79,.10);
            margin-bottom: 1.15rem;
        }
        [data-testid="stMetric"] {
            background: #fff; border: 1px solid var(--crm-border); border-radius: 15px;
            padding: 1.05rem 1.15rem; box-shadow: 0 3px 12px rgba(25,47,82,.025);
        }
        [data-testid="stMetricLabel"] p { font-size: .78rem; color: var(--crm-muted); font-weight: 700; }
        [data-testid="stMetricValue"] { color: var(--crm-ink); font-weight: 780; letter-spacing: -.045em; }
        [data-testid="stForm"] {
            background: #fff; border: 1px solid var(--crm-border); border-radius: 16px;
            padding: 1.15rem 1.25rem 1rem; box-shadow: 0 4px 16px rgba(25,47,82,.025);
        }
        [data-testid="stExpander"] {
            background: #fff; border: 1px solid var(--crm-border); border-radius: 14px;
            overflow: hidden; box-shadow: 0 3px 10px rgba(25,47,82,.02);
        }
        [data-testid="stExpander"] details summary { padding: .88rem 1rem; font-weight: 680; }
        [data-testid="stExpander"] details[open] summary { border-bottom: 1px solid #edf0f5; background: #fbfcff; }
        [data-testid="stExpander"] details > div > div { padding-top: .65rem; }
        [data-testid="stTabs"] [role="tablist"] { gap: .35rem; border-bottom: 1px solid var(--crm-border); }
        [data-testid="stTabs"] button[role="tab"] { font-weight: 700; padding: .7rem .9rem; }
        [data-testid="stTabs"] button[aria-selected="true"] { color: var(--crm-primary); }
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
        [data-testid="stSelectbox"] div[data-baseweb="select"],
        [data-testid="stDateInput"] input, [data-testid="stNumberInput"] input {
            border-radius: 10px;
        }
        .stButton button, [data-testid="stFormSubmitButton"] button {
            border-radius: 10px; font-weight: 720; min-height: 2.65rem;
            transition: all .15s ease; border: 1px solid #dce3ef;
        }
        .stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {
            background: var(--crm-primary); border-color: var(--crm-primary); color: white;
            box-shadow: 0 4px 10px rgba(65,105,225,.15);
        }
        .stButton button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
            background: var(--crm-primary-dark); border-color: var(--crm-primary-dark); color: white;
        }
        .stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
            border-color: #b8c7e1; color: var(--crm-primary);
        }
        [data-testid="stDataFrame"] { border: 1px solid var(--crm-border); border-radius: 12px; overflow: hidden; }
        hr { border-color: #e5eaf2; margin: 1.15rem 0; }
        [data-testid="stAlert"] { border-radius: 12px; }
        .crm-status-line { display: flex; flex-wrap: wrap; gap: .45rem; margin: .25rem 0 .8rem; }
        .crm-chip { display: inline-flex; border-radius: 999px; padding: .3rem .62rem; font-size: .71rem; line-height: 1.25; font-weight: 780; border: 1px solid transparent; }
        .crm-chip-blue { color: #3154ac; background: #edf2ff; border-color: #dce5ff; }
        .crm-chip-green { color: #176c52; background: #e6f7ef; border-color: #ceefdf; }
        .crm-chip-amber { color: #8b5b08; background: #fff5dc; border-color: #f5e5b5; }
        .crm-chip-red { color: #a3363e; background: #fff0f0; border-color: #f7d5d7; }
        .crm-chip-gray { color: #59687c; background: #f1f4f8; border-color: #e1e6ed; }
        .crm-empty {
            border: 1px dashed #ccd6e5; border-radius: 15px; text-align: center;
            padding: 2rem 1.5rem; background: rgba(255,255,255,.7); color: var(--crm-muted);
        }
        .crm-empty-title { color: var(--crm-ink); font-size: 1rem; font-weight: 760; margin-bottom: .25rem; }
        .crm-footer { border-top: 1px solid var(--crm-border); margin-top: 2rem; padding-top: .9rem; color: #8390a2; font-size: .73rem; }
        @media (max-width: 800px) {
            .crm-page-header { align-items: flex-start; flex-direction: column; padding: 1.1rem; }
            .main .block-container { padding-top: 1rem; }
            [data-testid="stMetric"] { padding: .85rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_crm_theme()


# =========================================================
# CONSTANTS
# =========================================================
ROLES = {
    "Sales Agent": "agent",
    "Department Staff": "department_staff",
    "Manager": "manager",
    "Admin": "admin",
}

DEPARTMENTS = [
    "Sales",
    "Quality",
    "DD Setup",
    "Letter Sending",
    "Confirmation Call",
    "SIM + Hardware Provisioning",
    "Live authorisation",
    "Administration",
]

LIVE_AUTH_DEPARTMENT = "Live authorisation"

TERMINAL_STATUSES = {"Live", "Cancelled", "Rejected"}

COMMITTED_CALL_OUTCOMES = [
    "Select outcome",
    "Committed",
    "Not Committed",
    "Callback Requested",
    "No Answer",
    "Other",
]

NAVIGATION = [
    "Overview",
    "Sales Records",
    "New Sale",
]


# =========================================================
# DATABASE CONNECTIONS
# =========================================================
def get_supabase():
    if "supabase_client" not in st.session_state:
        st.session_state["supabase_client"] = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
        )
    return st.session_state["supabase_client"]


def get_admin_supabase():
    # Service-role client is used only by server-side admin functions.
    if "admin_supabase_client" not in st.session_state:
        st.session_state["admin_supabase_client"] = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_SERVICE_ROLE_KEY"],
        )
    return st.session_state["admin_supabase_client"]


try:
    supabase = get_supabase()
except Exception:
    st.error("Unable to connect to the CRM database.")
    st.stop()


# =========================================================
# GENERAL HELPERS
# =========================================================
def section_heading(title: str, description: str = "", kicker: str = "WORKSPACE") -> None:
    st.markdown(
        f"""
        <div class="crm-section-head">
          <div class="crm-section-kicker">{escape(kicker)}</div>
          <div class="crm-section-title">{escape(title)}</div>
          <div class="crm-section-copy">{escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def parse_db_date(value, default=None):
    """Convert Supabase date/datetime values into datetime.date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        text = value.strip()
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            try:
                return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
            except ValueError:
                pass
    return default


def format_date(value, fallback="—"):
    """Format database dates/timestamps consistently as DD-MM-YYYY."""
    parsed = parse_db_date(value)
    return parsed.strftime("%d-%m-%Y") if parsed else fallback


def sale_created_date(sale):
    """The current schema uses created_at as the application/sale date."""
    return parse_db_date(sale.get("created_at"))


def filter_sales_by_date(sales_to_filter, start_date, end_date):
    """Inclusive sale-date filter; undated records are excluded when filtering."""
    filtered = []
    for item in sales_to_filter:
        sale_date = sale_created_date(item)
        if sale_date and start_date <= sale_date <= end_date:
            filtered.append(item)
    return filtered


def normalise_date_range(selected, default_start, default_end):
    """Normalise Streamlit's date/range return values, including partial selections."""
    if isinstance(selected, (tuple, list)):
        if len(selected) >= 2:
            start = selected[0] if isinstance(selected[0], date) else default_start
            end = selected[1] if isinstance(selected[1], date) else default_end
        elif len(selected) == 1 and isinstance(selected[0], date):
            start = end = selected[0]
        else:
            start, end = default_start, default_end
    elif isinstance(selected, date):
        start = end = selected
    else:
        start, end = default_start, default_end
    return (start, end) if start <= end else (end, start)


def clean_text(value):
    """Return trimmed text or None for blank values."""
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def load_profile(user_id):
    result = (
        supabase.table("profiles")
        .select("id, full_name, username, role, department, is_active")
        .eq("id", str(user_id))
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_verified_session_user():
    try:
        response = supabase.auth.get_user()
        user = response.user
        if not user or str(user.id) != str(st.session_state.get("user_id")):
            return None
        return user
    except Exception:
        return None


def require_active_admin():
    user = get_verified_session_user()
    if not user:
        raise PermissionError("Authentication required.")
    profile = load_profile(user.id)
    if not profile or not profile["is_active"] or profile["role"] != "admin":
        raise PermissionError("Active Admin access is required.")
    return profile


def is_live_authorisation_employee(profile):
    return (
        bool(profile)
        and profile.get("is_active") is True
        and profile.get("role") == "department_staff"
        and profile.get("department") == LIVE_AUTH_DEPARTMENT
    )


def can_process_assigned_sale(profile, sale):
    """Preserve existing Admin/Manager oversight and department assignment rules."""
    role = profile.get("role")
    if role in ("admin", "manager"):
        return True
    return (
        role == "department_staff"
        and profile.get("department") == sale.get("assigned_department")
    )


def display_author(changed_by, profile, user_id):
    if not changed_by:
        return "System / unknown"
    if str(changed_by) == str(user_id):
        return (
            f"{profile.get('full_name') or 'Current user'} "
            f"(@{profile.get('username') or '-'})"
        )
    return f"User ID: {str(changed_by)[:8]}…"


def status_chip_class(status):
    """Semantic colour for a user-facing workflow status label."""
    value = (status or "").strip().lower()
    if any(token in value for token in ("cancel", "reject", "not committed")):
        return "crm-chip-red"
    if any(token in value for token in ("pending", "callback", "no answer", "not recorded")):
        return "crm-chip-amber"
    if value == "live" or any(token in value for token in ("approved", "done", "committed", "complete", "authorised")):
        return "crm-chip-green"
    return "crm-chip-blue"


def workflow_status_label(sale):
    """Readable stage-aware status, not just the database's generic status."""
    stage = str(sale.get("current_stage") or "").strip()
    status = str(sale.get("status") or "").strip()
    outcome = str(sale.get("committed_call") or "").strip()

    if status == "Cancelled":
        return "Cancelled"
    if status == "Rejected":
        return "Quality Rejected"
    if status == "Live":
        return "Live"
    if stage == "Quality":
        return "Quality Pending" if status == "Pending" else f"Quality {status or 'In Progress'}"
    if stage == "DD Setup":
        return "DD Setup Pending" if status == "Pending" else f"DD Setup {status or 'In Progress'}"
    if stage == "Letter Sending":
        return "Letter Sending Pending" if status == "Pending" else f"Letter Sending {status or 'In Progress'}"
    if stage == "Confirmation Call":
        if outcome and outcome != "Select outcome":
            return f"Confirmation Call {outcome}"
        return "Confirmation Call Pending"
    if stage == "SIM + Hardware Provisioning":
        if status == "Approved":
            return "Provisioning Pending"
        return f"Provisioning {status or 'Pending'}"
    if stage == "Live":
        return "Live Authorisation Pending" if status == "Pending" else f"Live Authorisation {status or 'In Progress'}"
    if stage:
        return f"{stage} {status}".strip()
    return status or "Unassigned"


def show_status_chips(stage, status, department, sale=None):
    sale = sale or {"current_stage": stage, "status": status}
    status_label = workflow_status_label(sale)
    chips = (
        f'<span class="crm-chip {status_chip_class(status_label)}">{escape(status_label)}</span>'
        f'<span class="crm-chip crm-chip-blue">{escape(str(stage or "-"))}</span>'
        f'<span class="crm-chip crm-chip-gray">{escape(str(department or "-"))}</span>'
    )
    st.markdown(f'<div class="crm-status-line">{chips}</div>', unsafe_allow_html=True)


def load_sale_history(sale_id):
    return (
        supabase.table("sale_history")
        .select(
            "id, changed_by, previous_stage, new_stage, action, remarks, created_at"
        )
        .eq("sale_id", str(sale_id))
        .order("created_at", desc=True)
        .limit(100)
        .execute()
        .data
        or []
    )


def load_sales_for_user(profile, user_id):
    """Load all records visible to this role in pages, not an arbitrary first 200."""
    def base_query():
        query = (
            supabase.table("sales")
            .select(
                "id, customer_name, customer_phone, created_by, assigned_department, "
                "current_stage, status, rejection_reason, created_at, updated_at, "
                "address, post_code, sort_code, account_number, bank_name, "
                "package_offered, contract_duration, dd_reference_number, payment_date, "
                "letter_sent_date, committed_call, committed_call_comments, "
                "provisioning_date, sim_number, live_date, cancellation_reason, "
                "cancellation_date, cancelled_by"
            )
            .order("created_at", desc=True)
        )
        role = profile.get("role")
        if role == "agent":
            query = query.eq("created_by", str(user_id))
        elif role == "department_staff":
            query = query.eq("assigned_department", profile.get("department"))
        return query

    rows = []
    page_size = 1000
    offset = 0
    while True:
        batch = base_query().range(offset, offset + page_size - 1).execute().data or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def load_history_for_sales(sale_ids):
    """Load stage history for a collection of visible sales to audit stage completions."""
    ids = [str(sale_id) for sale_id in sale_ids if sale_id]
    if not ids:
        return []
    all_rows = []
    # Moderate IN-list size to avoid long request URLs on larger installations.
    for index in range(0, len(ids), 75):
        id_chunk = ids[index:index + 75]
        offset = 0
        page_size = 1000
        while True:
            response = (
                supabase.table("sale_history")
                .select("sale_id, changed_by, previous_stage, new_stage, action, remarks, created_at")
                .in_("sale_id", id_chunk)
                .order("created_at", desc=False)
                .range(offset, offset + page_size - 1)
                .execute()
            )
            batch = response.data or []
            all_rows.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
    return all_rows


def build_stage_breakdown(stage_sales, history_rows):
    """Count current queue and completed historical milestones by stage/status."""
    stage_names = [
        "Quality",
        "DD Setup",
        "Letter Sending",
        "Confirmation Call",
        "SIM + Hardware Provisioning",
        "Live Authorisation",
    ]
    buckets = {
        stage: {key: set() for key in ("Pending", "Approved / Done", "Rejected", "Cancelled", "Live")}
        for stage in stage_names
    }
    sale_by_id = {str(s.get("id")): s for s in stage_sales if s.get("id")}

    # Current records represent the application's present state.
    for sale_id, sale in sale_by_id.items():
        stage = sale.get("current_stage")
        status = sale.get("status")
        if status == "Rejected":
            buckets["Quality"]["Rejected"].add(sale_id)
        elif status == "Cancelled":
            row_stage = "Live Authorisation" if stage == "Live" else stage
            if row_stage in buckets:
                buckets[row_stage]["Cancelled"].add(sale_id)
        elif status == "Live":
            buckets["Live Authorisation"]["Live"].add(sale_id)
        elif stage == "Quality" and status == "Pending":
            buckets["Quality"]["Pending"].add(sale_id)
        elif stage == "DD Setup" and status == "Pending":
            buckets["DD Setup"]["Pending"].add(sale_id)
        elif stage == "Letter Sending" and status == "Pending":
            buckets["Letter Sending"]["Pending"].add(sale_id)
        elif stage == "Confirmation Call" and status == "Pending":
            buckets["Confirmation Call"]["Pending"].add(sale_id)
        elif stage == "SIM + Hardware Provisioning" and status in ("Approved", "Pending"):
            buckets["SIM + Hardware Provisioning"]["Pending"].add(sale_id)
        elif stage == "Live" and status == "Pending":
            buckets["Live Authorisation"]["Pending"].add(sale_id)

    # Stage completions remain visible after the application moves to a later stage.
    for event in history_rows:
        sale_id = str(event.get("sale_id") or "")
        if sale_id not in sale_by_id:
            continue
        action = str(event.get("action") or "").strip().lower()
        previous = str(event.get("previous_stage") or "").strip()
        new_stage = str(event.get("new_stage") or "").strip()

        if previous == "Quality" and ("approv" in action or new_stage == "DD Setup"):
            buckets["Quality"]["Approved / Done"].add(sale_id)
        if previous == "Quality" and ("reject" in action or new_stage == "Rejected"):
            buckets["Quality"]["Rejected"].add(sale_id)
        if (previous == "DD Setup" and new_stage == "Letter Sending") or "complete dd setup" in action:
            buckets["DD Setup"]["Approved / Done"].add(sale_id)
        if (previous == "Letter Sending" and new_stage == "Confirmation Call") or action == "letter sent":
            buckets["Letter Sending"]["Approved / Done"].add(sale_id)
        if previous == "Confirmation Call" and new_stage == "SIM + Hardware Provisioning":
            buckets["Confirmation Call"]["Approved / Done"].add(sale_id)
        if "approved" in action and previous == "Confirmation Call":
            buckets["Confirmation Call"]["Approved / Done"].add(sale_id)
        if (previous == "SIM + Hardware Provisioning" and new_stage == "Live") or "complete provisioning" in action:
            buckets["SIM + Hardware Provisioning"]["Approved / Done"].add(sale_id)

    rows = []
    for stage in stage_names:
        values = buckets[stage]
        # A sale may count in multiple stages over its life; each row is a stage-specific audit.
        row = {"Stage": stage}
        for key in ("Pending", "Approved / Done", "Rejected", "Cancelled", "Live"):
            row[key] = len(values[key])
        row["Total in stage"] = len(set().union(*values.values()))
        rows.append(row)
    return rows


# =========================================================
# WORKFLOW RPC
# =========================================================
def call_workflow(sale_id, action, remarks=None, details=None):
    """Call process_sale_stage; the database remains the authority for permissions."""
    details = details or {}
    payload = {
        "p_sale_id": str(sale_id),
        "p_action": action,
        "p_remarks": clean_text(remarks),
        "p_dd_reference_number": None,
        "p_payment_date": None,
        "p_letter_sent_date": None,
        "p_committed_call": None,
        "p_committed_call_comments": None,
        "p_provisioning_date": None,
        "p_sim_number": None,
        "p_live_date": None,
    }
    allowed_detail_keys = {
        "p_dd_reference_number",
        "p_payment_date",
        "p_letter_sent_date",
        "p_committed_call",
        "p_committed_call_comments",
        "p_provisioning_date",
        "p_sim_number",
        "p_live_date",
    }
    for key, value in details.items():
        if key not in allowed_detail_keys:
            raise ValueError(f"Unsupported workflow field: {key}")
        if isinstance(value, date):
            value = value.isoformat()
        payload[key] = value
    return supabase.rpc("process_sale_stage", payload).execute()


def stage_action_options(sale, current_profile, committed_call=None):
    stage = sale.get("current_stage")
    status = sale.get("status")
    assigned_department = sale.get("assigned_department")

    if status in TERMINAL_STATUSES:
        return []

    if stage == "DD Setup" and status == "Pending":
        return [("Complete DD Setup", "Complete DD Setup → Letter Sending")]

    if stage == "Letter Sending" and status == "Pending":
        return [("Letter Sent", "Mark Letter Sent → Confirmation Call")]

    if stage == "Confirmation Call" and status == "Pending":
        options = [("Record Call Details", "Save Committed Call Details")]
        if committed_call == "Committed":
            options.append(("Approved", "Approve → SIM + Hardware Provisioning"))
        options.append(("Cancelled", "Cancel Application"))
        return options

    if stage == "SIM + Hardware Provisioning" and status == "Approved":
        return [("Complete Provisioning", "Complete Provisioning → Live Authorisation")]

    if (
        stage == "Live"
        and status == "Pending"
        and assigned_department == LIVE_AUTH_DEPARTMENT
        and current_profile.get("role") == "department_staff"
        and current_profile.get("department") == LIVE_AUTH_DEPARTMENT
        and current_profile.get("is_active") is True
    ):
        return [("Live", "Authorise Sale as Live"), ("Cancelled", "Cancel Application")]

    return []


# =========================================================
# AUTHENTICATION
# =========================================================
if "user_id" in st.session_state and not get_verified_session_user():
    st.session_state.clear()
    st.rerun()


if "user_id" not in st.session_state:
    left, login_col, right = st.columns([1, 1.05, 1])
    with login_col:
        st.markdown(
            f"""
            <div style="padding:2.1rem .2rem .8rem">
              <img class="crm-login-logo" src="{LOGO_URL}" alt="Sparta Mobile CRM logo">
              <div class="crm-eyebrow">MOBILE SALES OPERATIONS</div>
              <div class="crm-login-title" style="margin-top:.45rem">Welcome back.</div>
              <div class="crm-login-copy">Sign in to access your sales workspace and assigned operations.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign in to Sparta Mobile CRM", type="primary", width="stretch")

        if submitted:
            username = username.strip().lower()
            if not username or not password:
                st.warning("Enter your username and password.")
            else:
                try:
                    admin_client = get_admin_supabase()
                    profile_result = (
                        admin_client.table("profiles")
                        .select("id, username, is_active")
                        .eq("username", username)
                        .limit(1)
                        .execute()
                    )
                    login_profile = profile_result.data[0] if profile_result.data else None

                    if not login_profile or not login_profile["is_active"]:
                        st.error("Invalid username or password.")
                    else:
                        auth_result = admin_client.auth.admin.get_user_by_id(str(login_profile["id"]))
                        auth_user = auth_result.user
                        auth_email = getattr(auth_user, "email", None) if auth_user else None
                        if not auth_email:
                            st.error("Unable to authenticate this account.")
                        else:
                            response = supabase.auth.sign_in_with_password({"email": auth_email, "password": password})
                            if not response.user:
                                st.error("Invalid username or password.")
                            else:
                                loaded_profile = load_profile(response.user.id)
                                if not loaded_profile or not loaded_profile["is_active"]:
                                    supabase.auth.sign_out()
                                    st.error("Your account is inactive or has no CRM profile.")
                                else:
                                    st.session_state["user_id"] = str(response.user.id)
                                    st.session_state["profile"] = loaded_profile
                                    st.rerun()
                except Exception:
                    st.error("Sign-in failed. Check your credentials and try again.")
    st.stop()


# =========================================================
# VERIFY CURRENT USER
# =========================================================
authenticated_user = get_verified_session_user()
if not authenticated_user:
    st.session_state.clear()
    st.rerun()

try:
    profile = load_profile(authenticated_user.id)
    if not profile or not profile["is_active"]:
        supabase.auth.sign_out()
        st.session_state.clear()
        st.error("Your CRM account is inactive or unavailable.")
        st.stop()
    st.session_state["profile"] = profile
except Exception:
    st.error("Unable to verify your CRM profile.")
    st.stop()

profile = st.session_state["profile"]
role = profile["role"]
user_id = str(profile["id"])
user_department = profile.get("department")
is_live_auth_user = is_live_authorisation_employee(profile)


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
nav_options = NAVIGATION + (["Cancellation Register", "User Management"] if role == "admin" else [])
if st.session_state.get("crm_navigation") not in nav_options:
    st.session_state["crm_navigation"] = "Overview"
if role != "admin" and st.session_state.get("crm_navigation") == "Cancellation Register":
    st.session_state["crm_navigation"] = "Overview"
with st.sidebar:
    st.markdown(
        f"""
        <div class="crm-brand">
          <img class="crm-brand-logo" src="{LOGO_URL}" alt="Sparta Mobile CRM logo">
          <div><div class="crm-brand-name">Sparta Mobile CRM</div><div class="crm-brand-sub">Mobile sales operations</div></div>
        </div>
        <div class="crm-nav-label">WORKSPACE</div>
        """,
        unsafe_allow_html=True,
    )
    selected_page = st.radio(
        "Navigation",
        nav_options,
        key="crm_navigation",
        label_visibility="collapsed",
    )
    if selected_page == "Cancellation Register" and role != "admin":
        selected_page = "Overview"
        st.session_state["crm_navigation"] = "Overview"
    st.divider()
    st.markdown('<div class="crm-nav-label">SIGNED-IN USER</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="crm-user-card">'
        f'<div class="crm-user-name">{escape(profile.get("full_name") or "User")}</div>'
        f'<div class="crm-user-meta">@{escape(profile.get("username") or "-")}<br>'
        f'{escape(role.replace("_", " ").title())}<br>{escape(user_department or "No department")}</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("↪  Sign out", width="stretch"):
        try:
            supabase.auth.sign_out()
        finally:
            st.session_state.clear()
            st.rerun()


# =========================================================
# GLOBAL PAGE HEADER
# =========================================================
if role == "admin":
    role_title = "Admin Dashboard"
    role_subtitle = "Organisation-wide sales management and oversight"
elif role == "manager":
    role_title = "Manager Dashboard"
    role_subtitle = "Sales oversight and workflow monitoring"
elif role == "department_staff" and is_live_auth_user:
    role_title = "Live Authorisation"
    role_subtitle = "Review pending sales and record the final decision"
elif role == "department_staff":
    role_title = "Department Operations"
    role_subtitle = f"Manage the {user_department or 'assigned'} workflow queue"
elif role == "agent":
    role_title = "My Sales Workspace"
    role_subtitle = "Create applications and follow their progress"
else:
    st.error("Unrecognised account role.")
    st.stop()

st.markdown(
    f"""
    <div class="crm-page-header">
      <div>
        <div class="crm-eyebrow">SPARTA MOBILE CRM · OPERATIONS</div>
        <div class="crm-page-title">{escape(role_title)}</div>
        <div class="crm-page-subtitle">{escape(role_subtitle)}</div>
      </div>
      <div class="crm-user-pill">●&nbsp; {escape(role.replace('_', ' ').upper())}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# OVERVIEW / SALES DATA LOAD
# =========================================================
sales = []
sales_load_error = None
try:
    sales = load_sales_for_user(profile, user_id)
except Exception as exc:
    sales_load_error = exc


if selected_page == "Overview":
    section_heading(
        "Overview",
        "Filter by application date and see current queues alongside completed stage outcomes.",
        "AT A GLANCE",
    )
    if sales_load_error:
        st.error(f"Unable to load sales records. Check database access policies and schema migration. Details: {sales_load_error}")
    else:
        available_dates = [sale_created_date(item) for item in sales]
        available_dates = [item for item in available_dates if item]
        default_end = max([date.today(), *available_dates])
        default_start = min(available_dates) if available_dates else default_end

        filter_cols = st.columns([1.6, 1, 1])
        with filter_cols[0]:
            selected_dates = st.date_input(
                "Sale date range",
                value=(default_start, default_end),
                format="DD-MM-YYYY",
                key="overview_sale_date_range",
                help="Uses the application creation date recorded in the CRM.",
            )
        with filter_cols[1]:
            st.caption("DATE BASIS")
            st.markdown("**Application created**")
        with filter_cols[2]:
            st.caption("RECORDS AVAILABLE")
            st.markdown(f"**{len(sales):,}**")
        filter_start, filter_end = normalise_date_range(
            selected_dates, default_start, default_end
        )

        dashboard_sales = filter_sales_by_date(sales, filter_start, filter_end)
        st.caption(f"Showing applications created {filter_start:%d-%m-%Y} to {filter_end:%d-%m-%Y} · {len(dashboard_sales):,} matching application(s).")

        total_sales = len(dashboard_sales)
        pending_count = sum(1 for item in dashboard_sales if item.get("status") == "Pending")
        approved_count = sum(1 for item in dashboard_sales if item.get("status") == "Approved")
        live_count = sum(1 for item in dashboard_sales if item.get("status") == "Live")
        cancelled_count = sum(1 for item in dashboard_sales if item.get("status") == "Cancelled")
        rejected_count = sum(1 for item in dashboard_sales if item.get("status") == "Rejected")

        metric_row_one = st.columns(3)
        metric_row_one[0].metric("Applications", f"{total_sales:,}")
        metric_row_one[1].metric("Pending", f"{pending_count:,}")
        metric_row_one[2].metric("Approved / in progress", f"{approved_count:,}")
        metric_row_two = st.columns(3)
        metric_row_two[0].metric("Live", f"{live_count:,}")
        metric_row_two[1].metric("Cancelled", f"{cancelled_count:,}")
        metric_row_two[2].metric("Rejected", f"{rejected_count:,}")

        # Load audit history for these applications so stage completions remain
        # visible even after the application has moved to a later stage.
        history_rows = []
        history_error = None
        try:
            history_rows = load_history_for_sales([item.get("id") for item in dashboard_sales])
        except Exception as exc:
            history_error = exc

        st.write("")
        section_heading(
            "Stage and status breakdown",
            "Counts by workflow stage. Completed outcomes are taken from stage history, while Pending reflects the current queue.",
            "PIPELINE DETAIL",
        )
        stage_rows = build_stage_breakdown(dashboard_sales, history_rows)
        st.dataframe(stage_rows, width="stretch", hide_index=True)
        if history_error:
            st.warning(
                "Stage history could not be loaded. Counts for completed stages may be incomplete; check sale_history SELECT access. "
                f"Details: {history_error}"
            )

        left, right = st.columns([1.05, 1])
        with left:
            section_heading("Confirmation call outcomes", "Call outcomes recorded across the selected applications.", "CALL RESULTS")
            call_stage_ids = set()
            for item in dashboard_sales:
                item_id = str(item.get("id") or "")
                current_stage = item.get("current_stage")
                if current_stage in ("Confirmation Call", "SIM + Hardware Provisioning", "Live") or item.get("committed_call"):
                    call_stage_ids.add(item_id)
            for event in history_rows:
                if event.get("previous_stage") == "Confirmation Call" or event.get("new_stage") == "Confirmation Call":
                    call_stage_ids.add(str(event.get("sale_id") or ""))
            call_stage_sales = [item for item in dashboard_sales if str(item.get("id") or "") in call_stage_ids]
            call_outcomes = ["Committed", "Not Committed", "Callback Requested", "No Answer", "Other", "Not recorded"]
            outcome_rows = []
            for outcome in call_outcomes:
                if outcome == "Not recorded":
                    count = sum(1 for item in call_stage_sales if not item.get("committed_call") or item.get("committed_call") == "Select outcome")
                else:
                    count = sum(1 for item in call_stage_sales if item.get("committed_call") == outcome)
                outcome_rows.append({"Call outcome": outcome, "Applications": count})
            st.dataframe(outcome_rows, width="stretch", hide_index=True)
            st.caption(f"Confirmation Call reached by {len(call_stage_sales):,} application(s) in this date range.")
        with right:
            section_heading("Recently updated", "Most recently changed applications in your visible queue.", "RECENT ACTIVITY")
            recently_updated = sorted(
                dashboard_sales,
                key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""),
                reverse=True,
            )[:6]
            if recently_updated:
                for item in recently_updated:
                    customer = item.get("customer_name") or "Unnamed sale"
                    stage_name = item.get("current_stage") or "-"
                    status_name = item.get("status") or "-"
                    dept = item.get("assigned_department") or "-"
                    with st.container(border=True):
                        st.markdown(f"**{escape(customer)}**")
                        show_status_chips(stage_name, status_name, dept, sale=item)
                        st.caption(f"Updated {format_date(item.get('updated_at') or item.get('created_at'))}")
            else:
                st.markdown('<div class="crm-empty"><div class="crm-empty-title">No applications in this date range</div>Adjust the date filter to view other applications.</div>', unsafe_allow_html=True)

        st.write("")
        quick_cols = st.columns(3 if role == "admin" else 2)
        with quick_cols[0]:
            st.markdown('<div class="crm-panel"><b>Sales records</b><br><span style="color:#68788e;font-size:.85rem">Search applications and review their history.</span></div>', unsafe_allow_html=True)
        with quick_cols[1]:
            st.markdown('<div class="crm-panel"><b>New application</b><br><span style="color:#68788e;font-size:.85rem">Capture customer and sales details.</span></div>', unsafe_allow_html=True)
        if role == "admin":
            with quick_cols[2]:
                st.markdown('<div class="crm-panel"><b>Administration</b><br><span style="color:#68788e;font-size:.85rem">Manage employee accounts and review cancellations.</span></div>', unsafe_allow_html=True)


# =========================================================
# ADMIN USER MANAGEMENT
# =========================================================
if selected_page == "User Management" and role == "admin":
    section_heading("User management", "Create employee accounts and review current access assignments.", "ADMINISTRATION")
    with st.expander("＋  Create new employee", expanded=False):
        with st.form("create_user_form", clear_on_submit=True):
            full_name = st.text_input("Employee full name *")
            new_username = st.text_input("Username *", help="3–32 characters: letters, numbers, dots, underscores or hyphens.")
            form_cols = st.columns(2)
            with form_cols[0]:
                new_password = st.text_input("Initial password *", type="password")
            with form_cols[1]:
                confirm_password = st.text_input("Confirm password *", type="password")
            form_cols = st.columns(2)
            with form_cols[0]:
                selected_role_label = st.selectbox("Role *", list(ROLES.keys()))
            with form_cols[1]:
                department = st.selectbox("Department *", DEPARTMENTS)
            create_user = st.form_submit_button("Create employee account", type="primary", width="stretch")

        if create_user:
            full_name = full_name.strip()
            new_username = new_username.strip().lower()
            valid_username = bool(re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,31}", new_username))
            if not full_name:
                st.warning("Employee full name is required.")
            elif not valid_username:
                st.warning("Username must be 3–32 characters and contain only letters, numbers, dots, underscores or hyphens.")
            elif len(new_password) < 8:
                st.warning("Password must be at least 8 characters.")
            elif new_password != confirm_password:
                st.warning("Passwords do not match.")
            else:
                created_user_id = None
                try:
                    require_active_admin()
                    admin_client = get_admin_supabase()
                    duplicate = admin_client.table("profiles").select("id").eq("username", new_username).limit(1).execute()
                    if duplicate.data:
                        st.warning("That username already exists.")
                    else:
                        internal_email = f"{new_username}@crm-login.invalid"
                        auth_response = admin_client.auth.admin.create_user({
                            "email": internal_email,
                            "password": new_password,
                            "email_confirm": True,
                            "user_metadata": {"full_name": full_name, "username": new_username},
                        })
                        if not auth_response.user:
                            st.error("Unable to create the Auth account.")
                        else:
                            created_user_id = str(auth_response.user.id)
                            admin_client.table("profiles").update({
                                "full_name": full_name,
                                "username": new_username,
                                "role": ROLES[selected_role_label],
                                "department": department,
                                "is_active": True,
                            }).eq("id", created_user_id).execute()
                            st.success(f"Created account for {full_name}. Username: {new_username}")
                            st.info("Share the initial password securely with the employee.")
                            st.rerun()
                except PermissionError:
                    st.error("Only an active Admin can create users.")
                except Exception:
                    if created_user_id:
                        try:
                            require_active_admin()
                            get_admin_supabase().auth.admin.delete_user(created_user_id)
                        except Exception:
                            pass
                    st.error("Account creation failed. Check Supabase Auth, the profile trigger, and database settings.")

    st.write("")
    section_heading("Employee directory", "Current employee roles, departments, and account status.", "TEAM ACCESS")
    try:
        require_active_admin()
        users_result = get_admin_supabase().table("profiles").select(
            "id, full_name, username, role, department, is_active, created_at"
        ).order("full_name").limit(500).execute()
        all_users = users_result.data or []
        users = list(all_users)
        if users:
            search_user = st.text_input("Search employees", placeholder="Name, username, role or department…", key="user_search")
            search_lower = search_user.strip().lower()
            if search_lower:
                users = [u for u in users if search_lower in " ".join(str(u.get(k) or "") for k in ("full_name", "username", "role", "department")).lower()]
            st.caption(f"Showing {len(users)} employee account(s)")
            st.dataframe([
                {
                    "Employee": u.get("full_name") or "-",
                    "Username": u.get("username") or "-",
                    "Role": (u.get("role") or "-").replace("_", " ").title(),
                    "Department": u.get("department") or "-",
                    "Active": "Yes" if u.get("is_active") else "No",
                    "Created": format_date(u.get("created_at")),
                } for u in users
            ], width="stretch", hide_index=True)
        else:
            st.info("No employee profiles were found.")

        st.write("")
        section_heading(
            "Remove or deactivate access",
            "Deactivation preserves sales and audit records. Permanent deletion is allowed only for accounts with no linked sales or workflow history.",
            "ACCOUNT CONTROL",
        )
        manageable_users = [u for u in all_users if str(u.get("id")) != user_id]
        if not manageable_users:
            st.info("There are no other employee accounts to manage.")
        else:
            with st.container(border=True):
                chosen_user_label_map = {
                    f"{u.get('full_name') or 'Unnamed'} (@{u.get('username') or '-'}) · {(u.get('role') or '-').replace('_', ' ').title()}": u
                    for u in manageable_users
                }
                chosen_user_label = st.selectbox(
                    "Employee account",
                    list(chosen_user_label_map.keys()),
                    key="account_control_employee",
                )
                target_user = chosen_user_label_map[chosen_user_label]
                target_id = str(target_user.get("id"))
                target_username = str(target_user.get("username") or "")
                target_is_admin = target_user.get("role") == "admin"
                action_cols = st.columns([1, 1.5])
                with action_cols[0]:
                    account_action = st.radio(
                        "Action",
                        ["Deactivate account", "Permanently delete account"],
                        key="account_control_action",
                    )
                with action_cols[1]:
                    st.caption("SELECTED ACCOUNT")
                    st.markdown(f"**{escape(target_user.get('full_name') or 'Unnamed')}**")
                    st.caption(
                        f"@{target_username} · {'Active' if target_user.get('is_active') else 'Inactive'}"
                    )

                if account_action == "Deactivate account":
                    st.warning("The employee will no longer be able to use the CRM. Their sales and history will remain available for audit.")
                    if st.button("Deactivate employee", key="deactivate_employee_button", type="secondary", width="stretch"):
                        try:
                            require_active_admin()
                            if target_is_admin:
                                active_admins = (
                                    get_admin_supabase().table("profiles")
                                    .select("id")
                                    .eq("role", "admin")
                                    .eq("is_active", True)
                                    .execute().data or []
                                )
                                if len(active_admins) <= 1:
                                    st.error("The last active Admin account cannot be deactivated.")
                                    st.stop()
                            get_admin_supabase().table("profiles").update({"is_active": False}).eq("id", target_id).execute()
                            st.success(f"Access deactivated for @{target_username}. Sales and audit history were preserved.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Unable to deactivate this account. Details: {exc}")
                else:
                    st.warning("Permanent deletion cannot be undone. To protect customer records and audit history, accounts referenced by sales or workflow events cannot be permanently deleted; deactivate those accounts instead.")
                    confirm_username = st.text_input(
                        f"Type {target_username} to confirm permanent deletion",
                        key="delete_employee_username_confirmation",
                    )
                    confirm_delete = st.checkbox(
                        "I understand this permanently removes the employee's login account.",
                        key="delete_employee_acknowledgement",
                    )
                    if st.button("Permanently delete employee", key="delete_employee_button", type="primary", width="stretch"):
                        if target_is_admin:
                            active_admins = (
                                get_admin_supabase().table("profiles")
                                .select("id")
                                .eq("role", "admin")
                                .eq("is_active", True)
                                .execute().data or []
                            )
                            if target_user.get("is_active") and len(active_admins) <= 1:
                                st.error("The last active Admin account cannot be deleted.")
                                st.stop()
                        if confirm_username.strip().lower() != target_username.lower():
                            st.warning("The confirmation username does not match.")
                        elif not confirm_delete:
                            st.warning("Please acknowledge the permanent deletion warning.")
                        else:
                            try:
                                require_active_admin()
                                admin_client = get_admin_supabase()
                                sales_refs = (
                                    admin_client.table("sales")
                                    .select("id", count="exact")
                                    .eq("created_by", target_id)
                                    .limit(1)
                                    .execute()
                                )
                                history_refs = (
                                    admin_client.table("sale_history")
                                    .select("id", count="exact")
                                    .eq("changed_by", target_id)
                                    .limit(1)
                                    .execute()
                                )
                                if (sales_refs.count or 0) > 0 or (history_refs.count or 0) > 0:
                                    st.error(
                                        "This account is referenced by sales or workflow history, so it cannot be permanently deleted without risking the audit trail. "
                                        "Choose Deactivate account instead."
                                    )
                                else:
                                    admin_client.auth.admin.delete_user(target_id)
                                    # Auth deletion generally cascades to profiles; this is a safe no-op if already removed.
                                    admin_client.table("profiles").delete().eq("id", target_id).execute()
                                    st.success(f"Employee account @{target_username} was permanently deleted.")
                                    st.rerun()
                            except Exception as exc:
                                st.error(f"Unable to delete this account. Details: {exc}")
    except Exception as exc:
        st.error(f"Unable to load or manage employee accounts. Details: {exc}")


# =========================================================
# CREATE NEW SALE
# =========================================================
if selected_page == "New Sale":
    section_heading("Create a new sale", "Capture the customer, banking, and package details in one organised form.", "NEW APPLICATION")
    st.markdown('<div class="crm-soft-note">New applications enter the <b>Quality</b> stage with a Pending status.</div>', unsafe_allow_html=True)
    st.write("")
    with st.form("new_sale_form", clear_on_submit=True):
        st.markdown("#### Customer information")
        cols = st.columns(2)
        with cols[0]:
            customer_name = st.text_input("Customer name *")
            customer_phone = st.text_input("Customer phone number")
            address = st.text_input("Address")
        with cols[1]:
            post_code = st.text_input("Post code")
            bank_name = st.text_input("Bank name")
        st.divider()
        st.markdown("#### Banking details")
        bank_cols = st.columns(2)
        with bank_cols[0]:
            sort_code = st.text_input("Sort code · digits only", max_chars=20, help="Numbers only; leading zeroes are preserved.")
        with bank_cols[1]:
            account_number = st.text_input("Account number · digits only", max_chars=30, help="Numbers only; leading zeroes are preserved.")
        st.divider()
        st.markdown("#### Package details")
        package_cols = st.columns(2)
        with package_cols[0]:
            package_offered = st.text_input("Package offered")
        with package_cols[1]:
            contract_duration = st.text_input("Contract duration")
        create_sale = st.form_submit_button("＋  Create sale", type="primary", width="stretch")

    if create_sale:
        clean_sort_code = sort_code.strip()
        clean_account_number = account_number.strip()
        if not customer_name.strip():
            st.warning("Customer name is required.")
        elif clean_sort_code and not re.fullmatch(r"[0-9]+", clean_sort_code):
            st.warning("Sort code must contain digits only. Do not enter spaces or hyphens.")
        elif clean_account_number and not re.fullmatch(r"[0-9]+", clean_account_number):
            st.warning("Account number must contain digits only.")
        else:
            try:
                sale_result = supabase.table("sales").insert({
                    "customer_name": customer_name.strip(),
                    "customer_phone": clean_text(customer_phone),
                    "address": clean_text(address),
                    "post_code": clean_text(post_code),
                    "sort_code": clean_text(clean_sort_code),
                    "account_number": clean_text(clean_account_number),
                    "bank_name": clean_text(bank_name),
                    "package_offered": clean_text(package_offered),
                    "contract_duration": clean_text(contract_duration),
                    "created_by": user_id,
                    "assigned_department": "Quality",
                    "current_stage": "Quality",
                    "status": "Pending",
                }).execute()
                if sale_result.data:
                    sale = sale_result.data[0]
                    try:
                        supabase.table("sale_history").insert({
                            "sale_id": sale["id"],
                            "changed_by": user_id,
                            "previous_stage": None,
                            "new_stage": "Quality",
                            "action": "Sale Created",
                            "remarks": "Application created with customer and sales details.",
                        }).execute()
                        st.success(f"Sale created successfully. Reference: {sale['id']}")
                    except Exception:
                        st.warning("The sale was created, but its history entry could not be saved.")
                    st.rerun()
                else:
                    st.error("The sale could not be created.")
            except Exception as exc:
                st.error(f"Unable to create the sale. Check database permissions and field constraints. Details: {exc}")


# =========================================================
# SALES RECORDS
# =========================================================
if selected_page == "Sales Records":
    section_heading("Sales records", "Search applications, follow stage progression, and access relevant actions without opening every record.", "APPLICATION WORKSPACE")
    if sales_load_error:
        st.error(f"Unable to load sales records. Check database access policies and schema migration. Details: {sales_load_error}")
    else:
        # Existing queue metric for the Live authorisation team.
        if is_live_auth_user:
            pending_live_count = sum(
                1 for sale in sales
                if sale.get("current_stage") == "Live"
                and sale.get("status") == "Pending"
                and sale.get("assigned_department") == LIVE_AUTH_DEPARTMENT
            )
            st.metric("Pending Live authorisations", pending_live_count)
            st.caption("Only pending sales assigned to Live authorisation are eligible for a final decision.")

        record_dates = [sale_created_date(item) for item in sales]
        record_dates = [item for item in record_dates if item]
        record_default_end = max([date.today(), *record_dates])
        record_default_start = min(record_dates) if record_dates else record_default_end
        record_date_cols = st.columns([1.6, 1, 1])
        with record_date_cols[0]:
            record_date_range = st.date_input(
                "Sale date range",
                value=(record_default_start, record_default_end),
                format="DD-MM-YYYY",
                key="records_sale_date_range",
            )
        with record_date_cols[1]:
            st.caption("DATE BASIS")
            st.markdown("**Application created**")
        with record_date_cols[2]:
            st.caption("RECORDS AVAILABLE")
            st.markdown(f"**{len(sales):,}**")
        record_start, record_end = normalise_date_range(
            record_date_range, record_default_start, record_default_end
        )
        date_filtered_sales = filter_sales_by_date(sales, record_start, record_end)
        st.caption(f"Applications created {record_start:%d-%m-%Y} to {record_end:%d-%m-%Y}.")

        filter_cols = st.columns([2.2, 1, 1])
        with filter_cols[0]:
            search_sales = st.text_input("Search applications", placeholder="Customer, phone, reference, stage…", key="sales_search")
        with filter_cols[1]:
            stage_values = sorted({str(s.get("current_stage") or "-") for s in date_filtered_sales})
            chosen_stage = st.selectbox("Stage", ["All stages"] + stage_values, key="sales_stage_filter")
        with filter_cols[2]:
            status_values = sorted({workflow_status_label(s) for s in date_filtered_sales})
            chosen_status = st.selectbox("Status", ["All statuses"] + status_values, key="sales_status_filter")

        visible_sales = list(date_filtered_sales)
        search_text = search_sales.strip().lower()
        if search_text:
            def matches_search(item):
                haystack = " ".join(str(item.get(key) or "") for key in (
                    "id", "customer_name", "customer_phone", "current_stage",
                    "assigned_department", "status", "post_code", "bank_name",
                )).lower()
                return search_text in haystack
            visible_sales = [item for item in visible_sales if matches_search(item)]
        if chosen_stage != "All stages":
            visible_sales = [item for item in visible_sales if (item.get("current_stage") or "-") == chosen_stage]
        if chosen_status != "All statuses":
            visible_sales = [item for item in visible_sales if workflow_status_label(item) == chosen_status]

        summary_cols = st.columns(3)
        summary_cols[0].metric("Visible records", len(visible_sales))
        summary_cols[1].metric("Pending", sum(1 for s in visible_sales if s.get("status") == "Pending"))
        summary_cols[2].metric("Closed", sum(1 for s in visible_sales if s.get("status") in ("Live", "Cancelled", "Rejected")))
        st.write("")

        if not visible_sales:
            st.markdown('<div class="crm-empty"><div class="crm-empty-title">No matching applications</div>Try a different search term or change the stage/status filters.</div>', unsafe_allow_html=True)
        else:
            st.caption(f"Showing {len(visible_sales)} of {len(date_filtered_sales)} records in the selected date range ({len(sales)} records available to your account). Open a record to see its details and permitted actions.")

        for sale in visible_sales:
            sale_id = str(sale["id"])
            stage = sale.get("current_stage") or "-"
            status = sale.get("status") or "-"
            assigned_department = sale.get("assigned_department") or "-"
            customer = sale.get("customer_name") or "Unnamed sale"
            is_terminal = status in TERMINAL_STATUSES
            is_quality_review = stage == "Quality" and assigned_department == "Quality" and status == "Pending"
            is_live_authorisation_record = stage == "Live" and assigned_department == LIVE_AUTH_DEPARTMENT and status == "Pending"

            with st.expander(f"{customer}   ·   {workflow_status_label(sale)}", expanded=False):
                show_status_chips(stage, status, assigned_department, sale=sale)
                if role == "admin":
                    overview_tab, admin_tab, history_tab = st.tabs([
                        "Overview & workflow", "Cancellation override", "History"
                    ])
                else:
                    overview_tab, history_tab = st.tabs(["Overview & workflow", "History"])
                    admin_tab = None

                # -----------------------------------------
                # COMPACT OVERVIEW + WORKFLOW
                # -----------------------------------------
                with overview_tab:
                    if is_terminal and status == "Cancelled":
                        st.error(
                            "Cancelled · "
                            f"{sale.get('cancellation_reason') or sale.get('rejection_reason') or 'No reason recorded'}"
                        )
                        st.caption(f"Cancellation date: {format_date(sale.get('cancellation_date'))}")
                    elif status == "Rejected" and sale.get("rejection_reason"):
                        st.error(f"Rejected · {sale['rejection_reason']}")
                    elif status == "Live":
                        st.success(f"Authorised as Live · {format_date(sale.get('live_date'), fallback='date not recorded')}")

                    info_cols = st.columns([1.25, 1.25, 1.5])
                    with info_cols[0]:
                        st.caption("CUSTOMER")
                        st.markdown(f"**{escape(customer)}**")
                        st.caption(sale.get("customer_phone") or "No phone number")
                    with info_cols[1]:
                        st.caption("CURRENT WORKFLOW")
                        st.markdown(f"**{escape(stage)}**")
                        st.caption(f"Assigned to {escape(assigned_department)}")
                    with info_cols[2]:
                        st.caption("REFERENCE / UPDATED")
                        st.markdown(
                            f'<div style="font-size:.76rem;line-height:1.45;overflow-wrap:anywhere">{escape(sale_id)}</div>',
                            unsafe_allow_html=True,
                        )
                        st.caption(f"Updated {format_date(sale.get('updated_at') or sale.get('created_at'))}")

                    # Long, mostly reference-only fields remain available without
                    # taking over the accordion every time it is opened.
                    with st.expander("View full customer, banking and workflow details", expanded=False):
                        st.markdown("**Customer & sales details**")
                        customer_fields = [
                            ("Address", "address"),
                            ("Post code", "post_code"),
                            ("Sort code", "sort_code"),
                            ("Account number", "account_number"),
                            ("Bank name", "bank_name"),
                            ("Package offered", "package_offered"),
                            ("Contract duration", "contract_duration"),
                        ]
                        detail_cols = st.columns(3)
                        for index, (label, field_name) in enumerate(customer_fields):
                            value = sale.get(field_name)
                            if field_name in {"payment_date", "letter_sent_date", "provisioning_date", "live_date"}:
                                value = format_date(value)
                            with detail_cols[index % 3]:
                                st.caption(label)
                                st.write(value if value not in (None, "") else "—")

                        st.divider()
                        st.markdown("**Workflow milestones**")
                        stage_fields = [
                            ("DD reference number", "dd_reference_number"),
                            ("Payment date", "payment_date"),
                            ("Letter sent date", "letter_sent_date"),
                            ("Committed call", "committed_call"),
                            ("Committed call comments", "committed_call_comments"),
                            ("Provisioning date", "provisioning_date"),
                            ("SIM number", "sim_number"),
                            ("Live date", "live_date"),
                        ]
                        milestone_cols = st.columns(3)
                        for index, (label, field_name) in enumerate(stage_fields):
                            value = sale.get(field_name)
                            if field_name in {"payment_date", "letter_sent_date", "provisioning_date", "live_date"}:
                                value = format_date(value)
                            with milestone_cols[index % 3]:
                                st.caption(label)
                                st.write(value if value not in (None, "") else "—")

                    if not is_terminal:
                        st.markdown("#### Workflow actions")

                    if is_terminal:
                        st.markdown('<div class="crm-soft-note">This record is closed. Standard workflow actions and comments are disabled for terminal statuses.</div>', unsafe_allow_html=True)
                    else:
                        if is_quality_review and (
                            role == "admin" or (role == "department_staff" and user_department == "Quality")
                        ):
                            st.markdown("#### Quality review")
                            quality_cols = st.columns([1, 2])
                            with quality_cols[0]:
                                decision = st.radio("Decision", ["Approve", "Reject"], horizontal=True, key=f"quality_decision_{sale_id}")
                            with quality_cols[1]:
                                quality_remarks = st.text_area(
                                    "Remarks" if decision == "Approve" else "Rejection reason *",
                                    key=f"quality_remarks_{sale_id}",
                                    placeholder="Enter review notes…" if decision == "Approve" else "Explain why this application is rejected…",
                                )
                            if st.button("Submit quality decision", key=f"quality_submit_{sale_id}", type="primary", width="stretch"):
                                if decision == "Reject" and not quality_remarks.strip():
                                    st.warning("A rejection reason is required.")
                                else:
                                    try:
                                        supabase.rpc("review_sale_quality", {
                                            "p_sale_id": sale_id,
                                            "p_decision": "Approved" if decision == "Approve" else "Rejected",
                                            "p_remarks": quality_remarks.strip() or None,
                                        }).execute()
                                        st.success(f"Quality decision submitted: {decision}.")
                                        st.rerun()
                                    except Exception as exc:
                                        st.error(f"The Quality decision could not be saved. Details: {exc}")

                        if can_process_assigned_sale(profile, sale):
                            stage_details = {}
                            selected_call_outcome = None

                            if stage == "DD Setup" and status == "Pending":
                                st.markdown("#### DD setup details")
                                dd_cols = st.columns(2)
                                with dd_cols[0]:
                                    dd_reference_number = st.text_input(
                                        "DD reference number *",
                                        value=sale.get("dd_reference_number") or "",
                                        key=f"dd_reference_{sale_id}",
                                    )
                                with dd_cols[1]:
                                    payment_date = st.date_input(
                                        "Payment date *",
                                        value=parse_db_date(sale.get("payment_date"), default=date.today()),
                                        format="DD-MM-YYYY",
                                        key=f"payment_date_{sale_id}",
                                    )
                                stage_details.update({
                                    "p_dd_reference_number": dd_reference_number.strip() or None,
                                    "p_payment_date": payment_date,
                                })

                            elif stage == "Confirmation Call" and status == "Pending":
                                st.markdown("#### Committed call details")
                                existing_outcome = sale.get("committed_call") or ""
                                default_outcome = existing_outcome if existing_outcome in COMMITTED_CALL_OUTCOMES else "Select outcome"
                                selected_call_outcome = st.selectbox(
                                    "Committed call *",
                                    COMMITTED_CALL_OUTCOMES,
                                    index=COMMITTED_CALL_OUTCOMES.index(default_outcome),
                                    key=f"committed_call_{sale_id}",
                                )
                                committed_call_comments = st.text_area(
                                    "Committed call comments",
                                    value=sale.get("committed_call_comments") or "",
                                    key=f"committed_call_comments_{sale_id}",
                                    placeholder="Record the call outcome, customer response, and relevant comments…",
                                )
                                stage_details.update({
                                    "p_committed_call": None if selected_call_outcome == "Select outcome" else selected_call_outcome,
                                    "p_committed_call_comments": committed_call_comments.strip() or None,
                                })

                            elif stage == "SIM + Hardware Provisioning" and status == "Approved":
                                st.markdown("#### SIM and hardware provisioning")
                                prov_cols = st.columns(2)
                                with prov_cols[0]:
                                    provisioning_date = st.date_input(
                                        "Provisioning date *",
                                        value=parse_db_date(sale.get("provisioning_date"), default=date.today()),
                                        format="DD-MM-YYYY",
                                        key=f"provisioning_date_{sale_id}",
                                    )
                                with prov_cols[1]:
                                    sim_number = st.text_input(
                                        "SIM number *",
                                        value=sale.get("sim_number") or "",
                                        key=f"sim_number_{sale_id}",
                                    )
                                stage_details.update({
                                    "p_provisioning_date": provisioning_date,
                                    "p_sim_number": sim_number.strip() or None,
                                })

                            options = stage_action_options(sale, profile, committed_call=selected_call_outcome)
                            if options:
                                st.divider()
                                st.markdown("#### Process application")
                                if is_live_auth_user and is_live_authorisation_record:
                                    st.markdown('<div class="crm-soft-note">Final decision: authorise this sale as Live or cancel it. These actions are restricted to Live authorisation staff.</div>', unsafe_allow_html=True)
                                if stage == "Letter Sending" and status == "Pending":
                                    st.caption("The Letter Sent Date will be recorded automatically when you mark the letter as sent.")
                                if stage == "Live" and status == "Pending" and is_live_auth_user:
                                    st.caption("The Live Date will be recorded automatically when you authorise the sale.")

                                action_labels = [label for _, label in options]
                                selected_label = st.selectbox("Action", action_labels, key=f"workflow_action_{sale_id}")
                                selected_action = next(action for action, label in options if label == selected_label)
                                workflow_remarks = st.text_area(
                                    "Cancellation reason *" if selected_action == "Cancelled" else "Additional remarks (optional)",
                                    key=f"workflow_remarks_{sale_id}",
                                    placeholder="Explain why this application is being cancelled…" if selected_action == "Cancelled" else "Add any additional details…",
                                )
                                if st.button("Submit action", key=f"workflow_submit_{sale_id}", type="primary", width="stretch"):
                                    validation_error = None
                                    if selected_action == "Cancelled" and not workflow_remarks.strip():
                                        validation_error = "A cancellation reason is required."
                                    elif stage == "DD Setup" and selected_action == "Complete DD Setup" and not dd_reference_number.strip():
                                        validation_error = "DD reference number is required."
                                    elif stage == "Confirmation Call" and selected_action == "Record Call Details" and selected_call_outcome in (None, "Select outcome"):
                                        validation_error = "Select a Committed Call outcome."
                                    elif stage == "Confirmation Call" and selected_action == "Approved" and selected_call_outcome != "Committed":
                                        validation_error = "The Committed Call outcome must be Committed before approval."
                                    elif stage == "SIM + Hardware Provisioning" and selected_action == "Complete Provisioning" and not sim_number.strip():
                                        validation_error = "SIM number is required."

                                    if validation_error:
                                        st.warning(validation_error)
                                    else:
                                        if selected_action == "Letter Sent":
                                            stage_details["p_letter_sent_date"] = date.today()
                                        if selected_action == "Live":
                                            stage_details["p_live_date"] = date.today()
                                        try:
                                            call_workflow(sale_id, selected_action, workflow_remarks, details=stage_details)
                                            st.success("Application updated successfully.")
                                            st.rerun()
                                        except Exception as exc:
                                            st.error(f"The action could not be saved. Refresh and check the stage, status, required fields and permissions. Details: {exc}")
                            elif stage == "Quality" and status == "Pending" and role not in ("admin", "manager") and user_department != "Quality":
                                st.caption("This application is awaiting Quality review.")

                            # General comments are optional so they do not dominate the application view.
                            with st.expander("＋ Add a comment", expanded=False):
                                comment = st.text_area("Comment", key=f"comment_text_{sale_id}", placeholder="Add a stage comment or update…")
                                if st.button("Save comment", key=f"comment_submit_{sale_id}", width="stretch"):
                                    if not comment.strip():
                                        st.warning("Enter a comment before saving.")
                                    else:
                                        try:
                                            call_workflow(sale_id, "Add Comment", comment)
                                            st.success("Comment saved to application history.")
                                            st.rerun()
                                        except Exception as exc:
                                            st.error(f"The comment could not be saved. Details: {exc}")
                        else:
                            st.info("This record is visible to you, but processing is restricted to its assigned department.")


                # -----------------------------------------
                # ADMIN CANCELLATION OVERRIDE TAB
                # -----------------------------------------
                if admin_tab is not None:
                    with admin_tab:
                        st.markdown("#### Cancellation override")
                        st.warning("This action cancels the sale regardless of its current stage or status, including a sale already authorised as Live.")
                        existing_cancel_date = parse_db_date(sale.get("cancellation_date"), default=date.today())
                        existing_cancel_reason = (
                            sale.get("cancellation_reason")
                            or (sale.get("rejection_reason") if status == "Cancelled" else "")
                            or ""
                        )
                        admin_cancel_reason = st.text_area(
                            "Cancellation reason *",
                            value=existing_cancel_reason,
                            key=f"admin_cancel_reason_{sale_id}",
                            placeholder="Enter the reason for cancelling this sale…",
                        )
                        admin_cancel_date = st.date_input(
                            "Cancellation date *",
                            value=existing_cancel_date,
                            format="DD-MM-YYYY",
                            key=f"admin_cancel_date_{sale_id}",
                        )
                        cancel_button_label = "Update cancellation record" if status == "Cancelled" else "Cancel sale — admin override"
                        if st.button(cancel_button_label, key=f"admin_cancel_submit_{sale_id}", type="secondary", width="stretch"):
                            if not admin_cancel_reason.strip():
                                st.warning("A cancellation reason is required.")
                            else:
                                try:
                                    require_active_admin()
                                    supabase.rpc("admin_cancel_sale", {
                                        "p_sale_id": sale_id,
                                        "p_reason": admin_cancel_reason.strip(),
                                        "p_cancellation_date": admin_cancel_date.isoformat(),
                                    }).execute()
                                    st.success("Sale cancelled. Its status has been set to Cancelled, and the reason and date have been recorded.")
                                    st.rerun()
                                except Exception as exc:
                                    st.error(f"The Admin cancellation could not be saved. Details: {exc}")

                # -----------------------------------------
                # HISTORY TAB
                # -----------------------------------------
                with history_tab:
                    st.markdown("#### Application history")
                    try:
                        history = load_sale_history(sale_id)
                        if not history:
                            st.markdown('<div class="crm-empty"><div class="crm-empty-title">No history yet</div>Workflow events and comments will appear here.</div>', unsafe_allow_html=True)
                        else:
                            for entry in history:
                                with st.container(border=True):
                                    action_name = entry.get("action") or "Update"
                                    created_at = format_date(entry.get("created_at"))
                                    st.markdown(f"**{action_name}**")
                                    st.caption(f"{created_at} · By {display_author(entry.get('changed_by'), profile, user_id)}")
                                    previous_stage = entry.get("previous_stage")
                                    new_stage = entry.get("new_stage")
                                    if previous_stage != new_stage:
                                        st.caption(f"Stage: {previous_stage or '—'} → {new_stage or '—'}")
                                    if entry.get("remarks"):
                                        st.write(entry["remarks"])
                    except Exception as exc:
                        st.warning(f"History could not be loaded. Check sale_history SELECT policies. Details: {exc}")


# =========================================================
# CANCELLATION REGISTER
# =========================================================
if selected_page == "Cancellation Register" and role == "admin":
    section_heading("Cancellation register", "A read-only audit view of cancelled applications across departments.", "AUDIT & OVERSIGHT")
    st.markdown('<div class="crm-soft-note">This register is for visibility and audit. Cancelled applications cannot be processed further through the normal workflow.</div>', unsafe_allow_html=True)
    st.write("")
    try:
        cancellation_result = supabase.rpc("list_cancelled_sales", {}).execute()
        cancelled_sales = cancellation_result.data or []
        summary_cols = st.columns(3)
        summary_cols[0].metric("Cancelled applications", len(cancelled_sales))
        summary_cols[1].metric("Departments represented", len({row.get("assigned_department") for row in cancelled_sales if row.get("assigned_department")}))
        summary_cols[2].metric("Stages represented", len({row.get("current_stage") for row in cancelled_sales if row.get("current_stage")}))

        if cancelled_sales:
            search_cancelled = st.text_input("Search cancellation register", placeholder="Customer, reason, stage, department or reference…", key="cancellation_search")
            search_lower = search_cancelled.strip().lower()
            rows = []
            for row in cancelled_sales:
                row_values = [row.get(k) for k in ("customer_name", "current_stage", "assigned_department", "cancellation_reason", "cancellation_date", "id")]
                if search_lower and search_lower not in " ".join(str(v or "") for v in row_values).lower():
                    continue
                rows.append({
                    "Customer": row.get("customer_name") or "-",
                    "Stage at cancellation": row.get("current_stage") or "-",
                    "Assigned department": row.get("assigned_department") or "-",
                    "Status": row.get("status") or "-",
                    "Cancellation reason": row.get("cancellation_reason") or "-",
                    "Cancellation date": format_date(row.get("cancellation_date")),
                    "Created": format_date(row.get("created_at")),
                    "Reference": row.get("id") or "-",
                })
            st.caption(f"Showing {len(rows)} of {len(cancelled_sales)} cancelled record(s).")
            st.dataframe(rows, width="stretch", hide_index=True)
        else:
            st.markdown('<div class="crm-empty"><div class="crm-empty-title">No cancellations recorded</div>Cancelled applications will appear here automatically.</div>', unsafe_allow_html=True)
    except Exception as exc:
        st.warning(f"The cancellation register could not be loaded. Confirm that the backend migration has been run. Details: {exc}")


# =========================================================
# FOOTER
# =========================================================
st.markdown(
    '<div class="crm-footer">Sparta Mobile CRM · Secure department workflow · Application history and audit trail</div>',
    unsafe_allow_html=True,
)
