import re
from datetime import date

import streamlit as st
from supabase import create_client


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Sales CRM",
    page_icon="📋",
    layout="wide",
)


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

TERMINAL_STATUSES = {
    "Live",
    "Cancelled",
    "Rejected",
}

COMMITTED_CALL_OUTCOMES = [
    "Select outcome",
    "Committed",
    "Not Committed",
    "Callback Requested",
    "No Answer",
    "Other",
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
    # Server-side only: username resolution and admin user management.
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
def parse_db_date(value, default=None):
    """Convert a Supabase date/datetime value into datetime.date."""
    if isinstance(value, date):
        return value

    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            pass

    return default


def clean_text(value):
    """Return trimmed text or None for blank values."""
    if value is None:
        return None

    value = str(value).strip()
    return value or None


def load_profile(user_id):
    result = (
        supabase.table("profiles")
        .select(
            "id, full_name, username, role, department, is_active"
        )
        .eq("id", str(user_id))
        .limit(1)
        .execute()
    )

    return result.data[0] if result.data else None


def get_verified_session_user():
    try:
        response = supabase.auth.get_user()
        user = response.user

        if (
            not user
            or str(user.id)
            != str(st.session_state.get("user_id"))
        ):
            return None

        return user

    except Exception:
        return None


def require_active_admin():
    user = get_verified_session_user()

    if not user:
        raise PermissionError("Authentication required.")

    profile = load_profile(user.id)

    if (
        not profile
        or not profile["is_active"]
        or profile["role"] != "admin"
    ):
        raise PermissionError(
            "Active Admin access is required."
        )

    return profile


def is_live_authorisation_employee(profile):
    return (
        bool(profile)
        and profile.get("is_active") is True
        and profile.get("role") == "department_staff"
        and profile.get("department") == LIVE_AUTH_DEPARTMENT
    )


def can_process_assigned_sale(profile, sale):
    """
    Preserve existing Admin/Manager oversight.
    Live authorisation buttons are independently restricted below.
    """
    role = profile.get("role")

    if role in ("admin", "manager"):
        return True

    return (
        role == "department_staff"
        and profile.get("department")
        == sale.get("assigned_department")
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


# =========================================================
# WORKFLOW RPC
# =========================================================
def call_workflow(
    sale_id,
    action,
    remarks=None,
    details=None,
):
    """
    Call process_sale_stage with all expected RPC parameters.

    Dates are converted to ISO strings for PostgREST.
    The database function validates the stage, status,
    department and permissions again before committing changes.
    """
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
            raise ValueError(
                f"Unsupported workflow field: {key}"
            )

        if isinstance(value, date):
            value = value.isoformat()

        payload[key] = value

    return supabase.rpc(
        "process_sale_stage",
        payload,
    ).execute()


def load_sale_history(sale_id):
    return (
        supabase.table("sale_history")
        .select(
            "id, changed_by, previous_stage, new_stage, "
            "action, remarks, created_at"
        )
        .eq("sale_id", str(sale_id))
        .order("created_at", desc=True)
        .limit(100)
        .execute()
        .data
        or []
    )


# =========================================================
# STAGE ACTION OPTIONS
# =========================================================
def stage_action_options(sale, committed_call=None):
    stage = sale.get("current_stage")
    status = sale.get("status")
    assigned_department = sale.get("assigned_department")

    # Never show ordinary workflow actions for a terminal outcome.
    if status in TERMINAL_STATUSES:
        return []

    if stage == "DD Setup" and status == "Pending":
        return [
            (
                "Complete DD Setup",
                "Complete DD Setup → Letter Sending",
            )
        ]

    if stage == "Letter Sending" and status == "Pending":
        return [
            (
                "Letter Sent",
                "Mark Letter Sent → Confirmation Call",
            )
        ]

    if stage == "Confirmation Call" and status == "Pending":
        options = [
            (
                "Record Call Details",
                "Save Committed Call Details",
            )
        ]

        # A sale can only be approved after a Committed outcome.
        if committed_call == "Committed":
            options.append(
                (
                    "Approved",
                    "Approve → SIM + Hardware Provisioning",
                )
            )

        options.append(
            (
                "Cancelled",
                "Cancel Application",
            )
        )

        return options

    if (
        stage == "SIM + Hardware Provisioning"
        and status == "Approved"
    ):
        return [
            (
                "Complete Provisioning",
                "Complete Provisioning → Live Authorisation",
            )
        ]

    # Exclusive Live authorisation.
    if (
        stage == "Live"
        and status == "Pending"
        and assigned_department == LIVE_AUTH_DEPARTMENT
        and profile.get("role") == "department_staff"
        and profile.get("department") == LIVE_AUTH_DEPARTMENT
        and profile.get("is_active") is True
    ):
        return [
            (
                "Live",
                "Authorise Sale as Live",
            ),
            (
                "Cancelled",
                "Cancel Application",
            ),
        ]

    return []


# =========================================================
# USERNAME LOGIN
# =========================================================
if "user_id" in st.session_state:
    if not get_verified_session_user():
        st.session_state.clear()
        st.rerun()


if "user_id" not in st.session_state:
    st.title("📋 Sales CRM")
    st.caption("Secure sales and operations management")
    st.subheader("Sign in")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input(
            "Password",
            type="password",
        )

        submitted = st.form_submit_button(
            "Sign in",
            use_container_width=True,
        )

    if submitted:
        username = username.strip().lower()

        if not username or not password:
            st.warning(
                "Enter your username and password."
            )

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

                login_profile = (
                    profile_result.data[0]
                    if profile_result.data
                    else None
                )

                if (
                    not login_profile
                    or not login_profile["is_active"]
                ):
                    st.error(
                        "Invalid username or password."
                    )

                else:
                    auth_result = (
                        admin_client.auth.admin.get_user_by_id(
                            str(login_profile["id"])
                        )
                    )

                    auth_user = auth_result.user
                    auth_email = (
                        getattr(auth_user, "email", None)
                        if auth_user
                        else None
                    )

                    if not auth_email:
                        st.error(
                            "Unable to authenticate this account."
                        )

                    else:
                        response = (
                            supabase.auth.sign_in_with_password({
                                "email": auth_email,
                                "password": password,
                            })
                        )

                        if not response.user:
                            st.error(
                                "Invalid username or password."
                            )

                        else:
                            profile = load_profile(
                                response.user.id
                            )

                            if (
                                not profile
                                or not profile["is_active"]
                            ):
                                supabase.auth.sign_out()

                                st.error(
                                    "Your account is inactive "
                                    "or has no CRM profile."
                                )

                            else:
                                st.session_state["user_id"] = (
                                    str(response.user.id)
                                )
                                st.session_state["profile"] = profile
                                st.rerun()

            except Exception:
                st.error(
                    "Sign-in failed. Check your credentials "
                    "and try again."
                )

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

        st.error(
            "Your CRM account is inactive or unavailable."
        )
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
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("📋 Sales CRM")
    st.divider()

    st.write(
        f"**User:** {profile.get('full_name') or '-'}"
    )
    st.write(
        f"**Username:** {profile.get('username') or '-'}"
    )
    st.write(
        f"**Role:** {role.replace('_', ' ').title()}"
    )
    st.write(
        f"**Department:** {user_department or '-'}"
    )

    st.divider()

    if st.button(
        "Sign out",
        use_container_width=True,
    ):
        try:
            supabase.auth.sign_out()
        finally:
            st.session_state.clear()
            st.rerun()


# =========================================================
# DASHBOARD HEADER
# =========================================================
if role == "admin":
    st.title("🛡️ Admin Dashboard")
    st.caption(
        "Organisation-wide sales management and oversight"
    )

elif role == "manager":
    st.title("📊 Manager Dashboard")
    st.caption("Sales oversight and workflow monitoring")

elif role == "department_staff":
    if is_live_auth_user:
        st.title("✅ Live Authorisation Dashboard")
        st.caption(
            "Review pending sales and authorise their final status"
        )
    else:
        st.title("📂 Department Dashboard")
        st.caption("Department operations")

elif role == "agent":
    st.title("💼 My Sales Dashboard")
    st.caption("Your sales and application progress")

else:
    st.error("Unrecognised account role.")
    st.stop()


# =========================================================
# ADMIN USER MANAGEMENT
# =========================================================
if role == "admin":
    st.divider()
    st.subheader("👥 User Management")

    with st.expander(
        "➕ Create New User",
        expanded=False,
    ):
        with st.form(
            "create_user_form",
            clear_on_submit=True,
        ):
            full_name = st.text_input(
                "Employee Full Name *"
            )
            new_username = st.text_input(
                "Username *"
            )
            new_password = st.text_input(
                "Initial Password *",
                type="password",
            )
            confirm_password = st.text_input(
                "Confirm Password *",
                type="password",
            )
            selected_role_label = st.selectbox(
                "Role *",
                list(ROLES.keys()),
            )
            department = st.selectbox(
                "Department *",
                DEPARTMENTS,
            )

            create_user = st.form_submit_button(
                "Create Employee Account",
                use_container_width=True,
            )

        if create_user:
            full_name = full_name.strip()
            new_username = new_username.strip().lower()

            valid_username = bool(
                re.fullmatch(
                    r"[a-z0-9][a-z0-9._-]{2,31}",
                    new_username,
                )
            )

            if not full_name:
                st.warning(
                    "Employee Full Name is required."
                )

            elif not valid_username:
                st.warning(
                    "Username must be 3–32 characters and "
                    "contain only letters, numbers, dots, "
                    "underscores or hyphens."
                )

            elif len(new_password) < 8:
                st.warning(
                    "Password must be at least 8 characters."
                )

            elif new_password != confirm_password:
                st.warning("Passwords do not match.")

            else:
                created_user_id = None

                try:
                    require_active_admin()
                    admin_client = get_admin_supabase()

                    duplicate = (
                        admin_client.table("profiles")
                        .select("id")
                        .eq("username", new_username)
                        .limit(1)
                        .execute()
                    )

                    if duplicate.data:
                        st.warning(
                            "That username already exists."
                        )

                    else:
                        internal_email = (
                            f"{new_username}@crm-login.invalid"
                        )

                        auth_response = (
                            admin_client.auth.admin.create_user({
                                "email": internal_email,
                                "password": new_password,
                                "email_confirm": True,
                                "user_metadata": {
                                    "full_name": full_name,
                                    "username": new_username,
                                },
                            })
                        )

                        if not auth_response.user:
                            st.error(
                                "Unable to create the Auth account."
                            )

                        else:
                            created_user_id = str(
                                auth_response.user.id
                            )

                            (
                                admin_client.table("profiles")
                                .update({
                                    "full_name": full_name,
                                    "username": new_username,
                                    "role": ROLES[
                                        selected_role_label
                                    ],
                                    "department": department,
                                    "is_active": True,
                                })
                                .eq("id", created_user_id)
                                .execute()
                            )

                            st.success(
                                f"Created account for {full_name}. "
                                f"Username: {new_username}"
                            )
                            st.info(
                                "Share the initial password "
                                "securely with the employee."
                            )
                            st.rerun()

                except PermissionError:
                    st.error(
                        "Only an active Admin can create users."
                    )

                except Exception:
                    if created_user_id:
                        try:
                            require_active_admin()
                            (
                                get_admin_supabase()
                                .auth.admin.delete_user(
                                    created_user_id
                                )
                            )
                        except Exception:
                            pass

                    st.error(
                        "Account creation failed. Check Supabase "
                        "Auth, the profile trigger, and database "
                        "settings."
                    )

    st.markdown("#### Existing Employees")

    try:
        require_active_admin()

        users_result = (
            get_admin_supabase()
            .table("profiles")
            .select(
                "full_name, username, role, department, "
                "is_active, created_at"
            )
            .order("full_name")
            .limit(500)
            .execute()
        )

        users = users_result.data or []

        if users:
            st.dataframe(
                [
                    {
                        "Employee": (
                            employee.get("full_name") or "-"
                        ),
                        "Username": (
                            employee.get("username") or "-"
                        ),
                        "Role": (
                            (employee.get("role") or "-")
                            .replace("_", " ")
                            .title()
                        ),
                        "Department": (
                            employee.get("department") or "-"
                        ),
                        "Active": (
                            "Yes"
                            if employee.get("is_active")
                            else "No"
                        ),
                        "Created": (
                            employee.get("created_at") or "-"
                        ),
                    }
                    for employee in users
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No employee profiles were found.")

    except Exception:
        st.error("Unable to load the employee list.")


# =========================================================
# CREATE NEW SALE — GENERAL SALES DETAILS
# =========================================================
st.divider()
st.subheader("➕ Create New Sale")

with st.form(
    "new_sale_form",
    clear_on_submit=True,
):
    customer_name = st.text_input("Customer Name *")
    customer_phone = st.text_input("Customer Phone Number")

    col1, col2 = st.columns(2)

    with col1:
        address = st.text_input("Address")
        post_code = st.text_input("Post code")
        sort_code = st.text_input(
            "Sort Code (numbers only)",
            max_chars=20,
        )
        account_number = st.text_input(
            "Account Number (numbers only)",
            max_chars=30,
        )

    with col2:
        bank_name = st.text_input("Bank Name")
        package_offered = st.text_input("Package Offered")
        contract_duration = st.text_input("Contract Duration")

    create_sale = st.form_submit_button(
        "Create Sale",
        use_container_width=True,
    )


if create_sale:
    # Keep the bank fields as text to preserve leading zeroes,
    # but reject any non-digit characters.
    clean_sort_code = sort_code.strip()
    clean_account_number = account_number.strip()

    if not customer_name.strip():
        st.warning("Customer Name is required.")

    elif (
        clean_sort_code
        and not re.fullmatch(r"[0-9]+", clean_sort_code)
    ):
        st.warning(
            "Sort Code must contain digits only. "
            "Do not enter spaces or hyphens."
        )

    elif (
        clean_account_number
        and not re.fullmatch(
            r"[0-9]+",
            clean_account_number,
        )
    ):
        st.warning(
            "Account Number must contain digits only."
        )

    else:
        try:
            sale_result = (
                supabase.table("sales")
                .insert({
                    "customer_name": customer_name.strip(),
                    "customer_phone": clean_text(customer_phone),
                    "address": clean_text(address),
                    "post_code": clean_text(post_code),
                    "sort_code": clean_text(clean_sort_code),
                    "account_number": clean_text(
                        clean_account_number
                    ),
                    "bank_name": clean_text(bank_name),
                    "package_offered": clean_text(
                        package_offered
                    ),
                    "contract_duration": clean_text(
                        contract_duration
                    ),
                    "created_by": user_id,
                    "assigned_department": "Quality",
                    "current_stage": "Quality",
                    "status": "Pending",
                })
                .execute()
            )

            if sale_result.data:
                sale = sale_result.data[0]

                try:
                    (
                        supabase.table("sale_history")
                        .insert({
                            "sale_id": sale["id"],
                            "changed_by": user_id,
                            "previous_stage": None,
                            "new_stage": "Quality",
                            "action": "Sale Created",
                            "remarks": (
                                "Application created with "
                                "customer and sales details."
                            ),
                        })
                        .execute()
                    )

                    st.success(
                        "Sale created successfully. "
                        f"Reference: {sale['id']}"
                    )

                except Exception:
                    st.warning(
                        "The sale was created, but its "
                        "history entry could not be saved."
                    )

                st.rerun()

            else:
                st.error("The sale could not be created.")

        except Exception as exc:
            st.error(
                "Unable to create the sale. Check database "
                f"permissions and field constraints. Details: {exc}"
            )


# =========================================================
# LOAD AND DISPLAY SALES
# =========================================================
st.divider()
st.subheader("📋 Sales Records")

try:
    query = (
        supabase.table("sales")
        .select(
            "id, customer_name, customer_phone, created_by, "
            "assigned_department, current_stage, status, "
            "rejection_reason, created_at, updated_at, "
            "address, post_code, sort_code, account_number, "
            "bank_name, package_offered, contract_duration, "
            "dd_reference_number, payment_date, "
            "letter_sent_date, committed_call, "
            "committed_call_comments, provisioning_date, "
            "sim_number, live_date, cancellation_reason, "
            "cancellation_date, cancelled_by"
        )
        .order("created_at", desc=True)
    )

    if role == "agent":
        query = query.eq("created_by", user_id)

    elif role == "department_staff":
        query = query.eq(
            "assigned_department",
            user_department,
        )

    sales = (
        query.limit(200)
        .execute()
        .data
        or []
    )

    # -----------------------------------------------------
    # LIVE AUTHORISATION SUMMARY
    # -----------------------------------------------------
    if is_live_auth_user:
        pending_live_count = sum(
            1
            for sale in sales
            if sale.get("current_stage") == "Live"
            and sale.get("status") == "Pending"
            and sale.get("assigned_department")
            == LIVE_AUTH_DEPARTMENT
        )

        st.metric(
            "Pending Live Authorisations",
            pending_live_count,
        )

        st.caption(
            "Only pending sales assigned to Live authorisation "
            "are eligible for a final decision."
        )

    if not sales:
        if is_live_auth_user:
            st.info(
                "No sales are currently assigned to "
                "Live authorisation."
            )
        else:
            st.info(
                "No sales records are available to display."
            )

    # -----------------------------------------------------
    # INDIVIDUAL SALE RECORDS
    # -----------------------------------------------------
    for sale in sales:
        sale_id = str(sale["id"])
        stage = sale.get("current_stage") or "-"
        status = sale.get("status") or "-"
        assigned_department = (
            sale.get("assigned_department") or "-"
        )

        is_terminal = status in TERMINAL_STATUSES

        is_quality_review = (
            stage == "Quality"
            and assigned_department == "Quality"
            and status == "Pending"
        )

        is_live_authorisation_record = (
            stage == "Live"
            and assigned_department == LIVE_AUTH_DEPARTMENT
            and status == "Pending"
        )

        with st.expander(
            f"{sale.get('customer_name') or 'Unnamed Sale'}"
            f" — {stage} — {status}"
        ):
            # ---------------------------------------------
            # BASIC DETAILS
            # ---------------------------------------------
            st.write(f"**Reference:** {sale_id}")
            st.write(
                f"**Customer:** "
                f"{sale.get('customer_name') or '-'}"
            )
            st.write(
                f"**Phone:** "
                f"{sale.get('customer_phone') or '-'}"
            )
            st.write(f"**Department:** {assigned_department}")
            st.write(f"**Stage:** {stage}")
            st.write(f"**Status:** {status}")
            st.write(
                f"**Created:** {sale.get('created_at') or '-'}"
            )

            # ---------------------------------------------
            # CUSTOMER AND SALES DETAILS
            # ---------------------------------------------
            st.divider()
            st.markdown("#### Customer and Sales Details")

            customer_fields = [
                ("Address", "address"),
                ("Post code", "post_code"),
                ("Sort Code", "sort_code"),
                ("Account Number", "account_number"),
                ("Bank Name", "bank_name"),
                ("Package Offered", "package_offered"),
                ("Contract Duration", "contract_duration"),
            ]

            for label, field_name in customer_fields:
                value = sale.get(field_name)
                st.write(
                    f"**{label}:** {value if value not in (None, '') else '-'}"
                )

            # ---------------------------------------------
            # STAGE DATA
            # ---------------------------------------------
            st.divider()
            st.markdown("#### Workflow Details")

            stage_fields = [
                ("DD Reference Number", "dd_reference_number"),
                ("Payment Date", "payment_date"),
                ("Letter Sent Date", "letter_sent_date"),
                ("Committed Call", "committed_call"),
                (
                    "Committed Call Comments",
                    "committed_call_comments",
                ),
                ("Provisioning Date", "provisioning_date"),
                ("SIM Number", "sim_number"),
                ("Live Date", "live_date"),
            ]

            for label, field_name in stage_fields:
                value = sale.get(field_name)
                st.write(
                    f"**{label}:** {value if value not in (None, '') else '-'}"
                )

            # ---------------------------------------------
            # CANCELLATION INFORMATION
            # ---------------------------------------------
            if is_terminal and status == "Cancelled":
                st.error("This sale has been cancelled.")

                st.write(
                    "**Cancellation Reason:** "
                    f"{sale.get('cancellation_reason') or sale.get('rejection_reason') or '-'}"
                )

                st.write(
                    "**Cancellation Date:** "
                    f"{sale.get('cancellation_date') or '-'}"
                )

            elif status == "Rejected" and sale.get("rejection_reason"):
                st.error(
                    f"**Rejection reason:** "
                    f"{sale['rejection_reason']}"
                )

            elif status == "Live":
                st.success(
                    f"Sale authorised as Live on "
                    f"{sale.get('live_date') or 'date not recorded'}."
                )

            # ---------------------------------------------
            # ADMIN CANCELLATION OVERRIDE
            # Available at every stage/status, including Live.
            # ---------------------------------------------
            if role == "admin":
                st.divider()
                st.markdown("#### 🛑 Admin Cancellation Override")

                st.warning(
                    "This action cancels the sale regardless of "
                    "its current stage or status. Other workflow "
                    "actions will no longer be available."
                )

                existing_cancel_date = parse_db_date(
                    sale.get("cancellation_date"),
                    default=date.today(),
                )

                existing_cancel_reason = (
                    sale.get("cancellation_reason")
                    or (
                        sale.get("rejection_reason")
                        if status == "Cancelled"
                        else ""
                    )
                    or ""
                )

                admin_cancel_reason = st.text_area(
                    "Cancellation Reason *",
                    value=existing_cancel_reason,
                    key=f"admin_cancel_reason_{sale_id}",
                    placeholder=(
                        "Enter the reason for cancelling this sale..."
                    ),
                )

                admin_cancel_date = st.date_input(
                    "Cancellation Date *",
                    value=existing_cancel_date,
                    key=f"admin_cancel_date_{sale_id}",
                )

                cancel_button_label = (
                    "Update Cancellation Record"
                    if status == "Cancelled"
                    else "Cancel Sale — Admin Override"
                )

                if st.button(
                    cancel_button_label,
                    key=f"admin_cancel_submit_{sale_id}",
                    use_container_width=True,
                    type="secondary",
                ):
                    if not admin_cancel_reason.strip():
                        st.warning(
                            "A cancellation reason is required."
                        )

                    else:
                        try:
                            require_active_admin()

                            supabase.rpc(
                                "admin_cancel_sale",
                                {
                                    "p_sale_id": sale_id,
                                    "p_reason": (
                                        admin_cancel_reason.strip()
                                    ),
                                    "p_cancellation_date": (
                                        admin_cancel_date.isoformat()
                                    ),
                                },
                            ).execute()

                            st.success(
                                "Sale cancelled. Its status has "
                                "been set to Cancelled, and the "
                                "reason and date have been recorded."
                            )
                            st.rerun()

                        except Exception as exc:
                            st.error(
                                "The Admin cancellation could not "
                                f"be saved. Details: {exc}"
                            )

            # ---------------------------------------------
            # QUALITY REVIEW
            # ---------------------------------------------
            if (
                not is_terminal
                and is_quality_review
                and (
                    role == "admin"
                    or (
                        role == "department_staff"
                        and user_department == "Quality"
                    )
                )
            ):
                st.divider()
                st.markdown("#### Quality Review")

                decision = st.radio(
                    "Decision",
                    ["Approve", "Reject"],
                    horizontal=True,
                    key=f"quality_decision_{sale_id}",
                )

                quality_remarks = st.text_area(
                    (
                        "Remarks"
                        if decision == "Approve"
                        else "Rejection Reason *"
                    ),
                    key=f"quality_remarks_{sale_id}",
                    placeholder=(
                        "Enter review remarks..."
                        if decision == "Approve"
                        else "Explain why this application is rejected..."
                    ),
                )

                if st.button(
                    "Submit Quality Decision",
                    key=f"quality_submit_{sale_id}",
                    use_container_width=True,
                ):
                    if (
                        decision == "Reject"
                        and not quality_remarks.strip()
                    ):
                        st.warning(
                            "A rejection reason is required."
                        )

                    else:
                        try:
                            supabase.rpc(
                                "review_sale_quality",
                                {
                                    "p_sale_id": sale_id,
                                    "p_decision": (
                                        "Approved"
                                        if decision == "Approve"
                                        else "Rejected"
                                    ),
                                    "p_remarks": (
                                        quality_remarks.strip()
                                        or None
                                    ),
                                },
                            ).execute()

                            st.success(
                                f"Quality decision submitted: {decision}."
                            )
                            st.rerun()

                        except Exception as exc:
                            st.error(
                                "The Quality decision could not "
                                "be saved. Details: "
                                f"{exc}"
                            )

            # ---------------------------------------------
            # WORKFLOW ACTIONS AND STAGE-SPECIFIC FIELDS
            # ---------------------------------------------
            if (
                not is_terminal
                and can_process_assigned_sale(profile, sale)
            ):
                stage_details = {}
                selected_call_outcome = None

                # DD SETUP DETAILS
                if (
                    stage == "DD Setup"
                    and status == "Pending"
                ):
                    st.divider()
                    st.markdown("#### DD Setup Details")

                    dd_reference_number = st.text_input(
                        "DD Reference Number *",
                        value=(
                            sale.get("dd_reference_number") or ""
                        ),
                        key=f"dd_reference_{sale_id}",
                    )

                    payment_date = st.date_input(
                        "Payment Date *",
                        value=parse_db_date(
                            sale.get("payment_date"),
                            default=date.today(),
                        ),
                        key=f"payment_date_{sale_id}",
                    )

                    stage_details.update({
                        "p_dd_reference_number": (
                            dd_reference_number.strip() or None
                        ),
                        "p_payment_date": payment_date,
                    })

                # CONFIRMATION / COMMITTED CALL DETAILS
                elif (
                    stage == "Confirmation Call"
                    and status == "Pending"
                ):
                    st.divider()
                    st.markdown("#### Committed Call Details")

                    existing_outcome = (
                        sale.get("committed_call") or ""
                    )

                    if existing_outcome in COMMITTED_CALL_OUTCOMES:
                        default_outcome = existing_outcome
                    else:
                        default_outcome = "Select outcome"

                    outcome_index = COMMITTED_CALL_OUTCOMES.index(
                        default_outcome
                    )

                    selected_call_outcome = st.selectbox(
                        "Committed Call *",
                        COMMITTED_CALL_OUTCOMES,
                        index=outcome_index,
                        key=f"committed_call_{sale_id}",
                    )

                    committed_call_comments = st.text_area(
                        "Committed Call Comments",
                        value=(
                            sale.get("committed_call_comments") or ""
                        ),
                        key=f"committed_call_comments_{sale_id}",
                        placeholder=(
                            "Record the call outcome, customer "
                            "response, and any relevant comments..."
                        ),
                    )

                    stage_details.update({
                        "p_committed_call": (
                            None
                            if selected_call_outcome == "Select outcome"
                            else selected_call_outcome
                        ),
                        "p_committed_call_comments": (
                            committed_call_comments.strip() or None
                        ),
                    })

                # PROVISIONING DETAILS
                elif (
                    stage == "SIM + Hardware Provisioning"
                    and status == "Approved"
                ):
                    st.divider()
                    st.markdown(
                        "#### SIM and Hardware Provisioning Details"
                    )

                    provisioning_date = st.date_input(
                        "Provisioning Date *",
                        value=parse_db_date(
                            sale.get("provisioning_date"),
                            default=date.today(),
                        ),
                        key=f"provisioning_date_{sale_id}",
                    )

                    sim_number = st.text_input(
                        "SIM Number *",
                        value=sale.get("sim_number") or "",
                        key=f"sim_number_{sale_id}",
                    )

                    stage_details.update({
                        "p_provisioning_date": provisioning_date,
                        "p_sim_number": sim_number.strip() or None,
                    })

                # SHOW WORKFLOW ACTIONS
                options = stage_action_options(
                    sale,
                    committed_call=selected_call_outcome,
                )

                if options:
                    st.divider()
                    st.markdown("#### Process Application")

                    if (
                        is_live_auth_user
                        and is_live_authorisation_record
                    ):
                        st.info(
                            "Final decision: authorise this sale "
                            "as Live or cancel it. These actions "
                            "are restricted to Live authorisation staff."
                        )

                    if (
                        stage == "Letter Sending"
                        and status == "Pending"
                    ):
                        st.caption(
                            "The Letter Sent Date will be recorded "
                            "automatically when you mark the letter as sent."
                        )

                    if (
                        stage == "Live"
                        and status == "Pending"
                        and is_live_auth_user
                    ):
                        st.caption(
                            "The Live Date will be recorded "
                            "automatically when you authorise the sale."
                        )

                    action_labels = [
                        label for _, label in options
                    ]

                    selected_label = st.selectbox(
                        "Action",
                        action_labels,
                        key=f"workflow_action_{sale_id}",
                    )

                    selected_action = next(
                        action
                        for action, label in options
                        if label == selected_label
                    )

                    workflow_remarks = st.text_area(
                        (
                            "Cancellation Reason *"
                            if selected_action == "Cancelled"
                            else "Additional Remarks (optional)"
                        ),
                        key=f"workflow_remarks_{sale_id}",
                        placeholder=(
                            "Explain why this application is being cancelled..."
                            if selected_action == "Cancelled"
                            else "Add any additional details..."
                        ),
                    )

                    if st.button(
                        "Submit Action",
                        key=f"workflow_submit_{sale_id}",
                        use_container_width=True,
                    ):
                        validation_error = None

                        if (
                            selected_action == "Cancelled"
                            and not workflow_remarks.strip()
                        ):
                            validation_error = (
                                "A cancellation reason is required."
                            )

                        elif (
                            stage == "DD Setup"
                            and selected_action == "Complete DD Setup"
                        ):
                            if not dd_reference_number.strip():
                                validation_error = (
                                    "DD Reference Number is required."
                                )

                        elif (
                            stage == "Confirmation Call"
                            and selected_action == "Record Call Details"
                        ):
                            if (
                                selected_call_outcome
                                in (None, "Select outcome")
                            ):
                                validation_error = (
                                    "Select a Committed Call outcome."
                                )

                        elif (
                            stage == "Confirmation Call"
                            and selected_action == "Approved"
                        ):
                            if selected_call_outcome != "Committed":
                                validation_error = (
                                    "The Committed Call outcome must be "
                                    "Committed before approval."
                                )

                        elif (
                            stage == "SIM + Hardware Provisioning"
                            and selected_action == "Complete Provisioning"
                        ):
                            if not sim_number.strip():
                                validation_error = (
                                    "SIM Number is required."
                                )

                        if validation_error:
                            st.warning(validation_error)

                        else:
                            # Add event-based dates only when the
                            # corresponding workflow action succeeds.
                            if selected_action == "Letter Sent":
                                stage_details["p_letter_sent_date"] = (
                                    date.today()
                                )

                            if selected_action == "Live":
                                stage_details["p_live_date"] = (
                                    date.today()
                                )

                            try:
                                call_workflow(
                                    sale_id=sale_id,
                                    action=selected_action,
                                    remarks=workflow_remarks,
                                    details=stage_details,
                                )

                                st.success(
                                    "Application updated successfully."
                                )
                                st.rerun()

                            except Exception as exc:
                                st.error(
                                    "The action could not be saved. "
                                    "Refresh and check the stage, "
                                    "status, required fields and permissions. "
                                    f"Details: {exc}"
                                )

                # ------------------------------------------
                # GENERAL COMMENTS
                # ------------------------------------------
                # Do not allow further comments through the
                # normal workflow once the sale is terminal.
                st.divider()
                st.markdown("#### Add Comment")

                comment = st.text_area(
                    "Comment",
                    key=f"comment_text_{sale_id}",
                    placeholder=(
                        "Enter a stage comment or update..."
                    ),
                )

                if st.button(
                    "Save Comment",
                    key=f"comment_submit_{sale_id}",
                    use_container_width=True,
                ):
                    if not comment.strip():
                        st.warning(
                            "Enter a comment before saving."
                        )

                    else:
                        try:
                            call_workflow(
                                sale_id=sale_id,
                                action="Add Comment",
                                remarks=comment,
                            )

                            st.success(
                                "Comment saved to application history."
                            )
                            st.rerun()

                        except Exception as exc:
                            st.error(
                                "The comment could not be saved. "
                                f"Details: {exc}"
                            )

            # ---------------------------------------------
            # APPLICATION HISTORY
            # ---------------------------------------------
            st.divider()
            st.markdown("#### Application History")

            try:
                history = load_sale_history(sale_id)

                if not history:
                    st.caption(
                        "No history entries are available yet."
                    )

                else:
                    for entry in history:
                        action = (
                            entry.get("action") or "Update"
                        )
                        created_at = (
                            entry.get("created_at") or "-"
                        )

                        st.markdown(
                            f"**{action}** · {created_at}"
                        )

                        st.caption(
                            "By: "
                            + display_author(
                                entry.get("changed_by"),
                                profile,
                                user_id,
                            )
                        )

                        previous_stage = entry.get(
                            "previous_stage"
                        )
                        new_stage = entry.get("new_stage")

                        if previous_stage != new_stage:
                            st.caption(
                                f"Stage: {previous_stage or '—'} "
                                f"→ {new_stage or '—'}"
                            )

                        if entry.get("remarks"):
                            st.write(entry["remarks"])

                        st.divider()

            except Exception as exc:
                st.warning(
                    "History could not be loaded. Check the "
                    "sale_history SELECT policies. "
                    f"Details: {exc}"
                )

except Exception as exc:
    st.error(
        "Unable to load sales records. Check the database "
        f"access policies and schema migration. Details: {exc}"
    )


# =========================================================
# CANCELLATION REGISTER — VISIBLE ACROSS ALL MODULES
# =========================================================
st.divider()
st.subheader("🛑 Cancellation Register")
st.caption(
    "Cancellations across departments. This register displays "
    "summary details only and does not permit further processing."
)

try:
    cancellation_result = (
        supabase.rpc("list_cancelled_sales", {})
        .execute()
    )

    cancelled_sales = cancellation_result.data or []

    if cancelled_sales:
        st.dataframe(
            [
                {
                    "Customer": (
                        row.get("customer_name") or "-"
                    ),
                    "Stage at Cancellation": (
                        row.get("current_stage") or "-"
                    ),
                    "Assigned Department": (
                        row.get("assigned_department") or "-"
                    ),
                    "Status": row.get("status") or "-",
                    "Cancellation Reason": (
                        row.get("cancellation_reason") or "-"
                    ),
                    "Cancellation Date": (
                        row.get("cancellation_date") or "-"
                    ),
                    "Created": row.get("created_at") or "-",
                    "Reference": row.get("id") or "-",
                }
                for row in cancelled_sales
            ],
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "There are no cancelled sales to display."
        )

except Exception as exc:
    st.warning(
        "The cancellation register could not be loaded. "
        "Confirm that the backend migration has been run. "
        f"Details: {exc}"
    )


# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption(
    "Sales CRM | Department Workflow, Stage Details "
    "and Application History"
)
