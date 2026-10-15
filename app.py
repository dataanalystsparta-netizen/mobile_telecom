
import re
import secrets
import string

import streamlit as st
from supabase import create_client


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Sales CRM",
    page_icon="📋",
    layout="wide",
)


# --------------------------------------------------
# DATABASE CONNECTIONS
# --------------------------------------------------
def get_supabase():
    """Normal client for authenticated CRM operations."""
    if "supabase_client" not in st.session_state:
        st.session_state["supabase_client"] = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
        )

    return st.session_state["supabase_client"]


def get_admin_supabase():
    """
    Privileged backend client.
    Never use this client for ordinary sales operations.
    """
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


# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------
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


# --------------------------------------------------
# PROFILE LOOKUP
# --------------------------------------------------
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
    """
    Validate the actual Supabase Auth session rather than
    trusting a user ID stored in Streamlit session state.
    """
    try:
        response = supabase.auth.get_user()
        user = response.user

        if not user:
            return None

        if str(user.id) != str(st.session_state.get("user_id")):
            return None

        return user

    except Exception:
        return None


# --------------------------------------------------
# USERNAME-BASED LOGIN
# --------------------------------------------------
if "user_id" in st.session_state:
    authenticated_user = get_verified_session_user()

    if not authenticated_user:
        st.session_state.clear()
        st.rerun()


if "user_id" not in st.session_state:
    st.title("📋 Sales CRM")
    st.caption("Secure sales and operations management")
    st.subheader("Sign in")

    with st.form("login_form"):
        username = st.text_input(
            "Username",
            placeholder="Enter your username",
        )

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
            st.warning("Enter your username and password.")

        else:
            try:
                admin_client = get_admin_supabase()

                # Resolve the username to its Auth account.
                # This lookup stays on the server.
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

                if not login_profile or not login_profile["is_active"]:
                    st.error("Invalid username or password.")

                else:
                    # Obtain the existing Auth email for this user.
                    # Existing accounts retain their current email;
                    # newly created accounts use an internal identifier.
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
                        st.error("Unable to authenticate this account.")

                    else:
                        response = supabase.auth.sign_in_with_password({
                            "email": auth_email,
                            "password": password,
                        })

                        if not response.user:
                            st.error("Invalid username or password.")

                        else:
                            profile = load_profile(response.user.id)

                            if not profile or not profile["is_active"]:
                                supabase.auth.sign_out()
                                st.error(
                                    "This account is inactive or "
                                    "has no CRM profile."
                                )

                            else:
                                st.session_state["user_id"] = str(
                                    response.user.id
                                )
                                st.session_state["profile"] = profile
                                st.rerun()

            except Exception:
                st.error(
                    "Sign-in failed. Check your credentials and "
                    "try again. Contact the administrator if the "
                    "problem persists."
                )

    st.stop()


# --------------------------------------------------
# VERIFY CURRENT USER AND PROFILE
# --------------------------------------------------
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


# --------------------------------------------------
# SECURE ADMIN AUTHORISATION
# --------------------------------------------------
def require_active_admin():
    """
    Re-check identity and current database permissions before
    performing any privileged operation.
    """
    verified_user = get_verified_session_user()

    if not verified_user:
        raise PermissionError("Your session is not authenticated.")

    current_profile = load_profile(verified_user.id)

    if (
        not current_profile
        or not current_profile["is_active"]
        or current_profile["role"] != "admin"
    ):
        raise PermissionError(
            "Only an active Admin can perform this operation."
        )

    return current_profile


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.title("📋 Sales CRM")
    st.divider()

    st.write(f"**User:** {profile['full_name']}")
    st.write(f"**Username:** {profile.get('username') or '-'}")
    st.write(f"**Role:** {role.replace('_', ' ').title()}")
    st.write(f"**Department:** {profile['department'] or '-'}")

    st.divider()

    if st.button("Sign out", use_container_width=True):
        try:
            supabase.auth.sign_out()
        finally:
            st.session_state.clear()
            st.rerun()


# --------------------------------------------------
# DASHBOARD HEADER
# --------------------------------------------------
if role == "admin":
    st.title("🛡️ Admin Dashboard")
    st.caption("Organisation-wide sales management")

elif role == "manager":
    st.title("📊 Manager Dashboard")
    st.caption("Sales oversight and Live authorisation")

elif role == "department_staff":
    st.title("📂 Department Dashboard")
    st.caption("Department operations")

elif role == "agent":
    st.title("💼 My Sales Dashboard")
    st.caption("Your sales and application progress")

else:
    st.error("Unrecognised account role.")
    st.stop()


# --------------------------------------------------
# ADMIN USER MANAGEMENT
# --------------------------------------------------
if role == "admin":
    st.divider()
    st.subheader("👥 User Management")

    st.caption(
        "Create employee accounts and assign their CRM permissions. "
        "Employees sign in using a username and password."
    )

    with st.expander("➕ Create New User", expanded=False):
        with st.form("create_user_form", clear_on_submit=True):
            full_name = st.text_input(
                "Employee Full Name *",
                placeholder="Enter employee name",
            )

            new_username = st.text_input(
                "Username *",
                placeholder="e.g. john.smith",
                help=(
                    "Use 3–32 characters: letters, numbers, "
                    "full stops, underscores or hyphens."
                ),
            )

            new_password = st.text_input(
                "Initial Password *",
                type="password",
                help="Use at least 8 characters.",
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

            username_valid = bool(
                re.fullmatch(
                    r"[a-z0-9][a-z0-9._-]{2,31}",
                    new_username,
                )
            )

            if not full_name:
                st.warning("Employee Full Name is required.")

            elif not username_valid:
                st.warning(
                    "Username must contain 3–32 characters, start "
                    "with a letter or number, and use only letters, "
                    "numbers, full stops, underscores or hyphens."
                )

            elif len(new_password) < 8:
                st.warning(
                    "The initial password must be at least 8 characters."
                )

            elif new_password != confirm_password:
                st.warning("The passwords do not match.")

            else:
                created_user_id = None

                try:
                    # Verify the caller immediately before privileged work.
                    require_active_admin()
                    admin_client = get_admin_supabase()

                    # Check for a duplicate username.
                    duplicate = (
                        admin_client.table("profiles")
                        .select("id")
                        .eq("username", new_username)
                        .limit(1)
                        .execute()
                    )

                    if duplicate.data:
                        st.warning(
                            "That username already exists. "
                            "Choose another username."
                        )
                        st.stop()

                    # Supabase Auth requires an email identifier for
                    # password authentication. This internal identifier
                    # is never displayed as the employee's login.
                    # Email confirmation is set explicitly, so no
                    # invitation or confirmation email is needed.
                    internal_email = (
                        f"{new_username}@crm-login.invalid"
                    )

                    auth_response = admin_client.auth.admin.create_user({
                        "email": internal_email,
                        "password": new_password,
                        "email_confirm": True,
                        "user_metadata": {
                            "full_name": full_name,
                            "username": new_username,
                        },
                    })

                    if not auth_response.user:
                        st.error("Supabase could not create the account.")
                        st.stop()

                    created_user_id = str(auth_response.user.id)

                    # The existing database trigger creates a default
                    # profile. Update it with the Admin's assignments.
                    admin_client.table("profiles").update({
                        "full_name": full_name,
                        "username": new_username,
                        "role": ROLES[selected_role_label],
                        "department": department,
                        "is_active": True,
                    }).eq("id", created_user_id).execute()

                    st.success(
                        f"Account created for {full_name}. "
                        f"Username: {new_username}"
                    )

                    st.info(
                        "Share the username and initial password "
                        "with the employee securely. The password "
                        "is not stored in the CRM profile."
                    )

                    st.rerun()

                except PermissionError:
                    st.error(
                        "Permission denied. Only an active Admin "
                        "can create accounts."
                    )

                except Exception:
                    # Roll back the Auth account if profile setup fails.
                    # This avoids leaving a user who cannot sign in
                    # using the CRM username.
                    if created_user_id:
                        try:
                            require_active_admin()
                            get_admin_supabase().auth.admin.delete_user(
                                created_user_id
                            )
                        except Exception:
                            pass

                    st.error(
                        "Account creation failed. Check the username, "
                        "database trigger, and Supabase Auth settings. "
                        "If the problem persists, inspect the server "
                        "logs without sharing passwords or secret keys."
                    )

    # --------------------------------------------------
    # EXISTING USERS
    # --------------------------------------------------
    st.markdown("#### Existing Employees")

    if st.button("Refresh User List"):
        st.rerun()

    try:
        require_active_admin()
        admin_client = get_admin_supabase()

        users_result = (
            admin_client.table("profiles")
            .select(
                "full_name, username, role, department, is_active, created_at"
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
                        "Employee": item.get("full_name") or "-",
                        "Username": item.get("username") or "-",
                        "Role": (
                            item.get("role") or "-"
                        ).replace("_", " ").title(),
                        "Department": item.get("department") or "-",
                        "Active": (
                            "Yes" if item.get("is_active") else "No"
                        ),
                        "Created": item.get("created_at") or "-",
                    }
                    for item in users
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No employee profiles were found.")

    except Exception:
        st.error("Unable to load the employee list.")


# --------------------------------------------------
# CREATE SALE
# --------------------------------------------------
st.divider()
st.subheader("➕ Create New Sale")

with st.form("new_sale_form", clear_on_submit=True):
    customer_name = st.text_input("Customer Name *")
    customer_phone = st.text_input("Customer Phone Number")

    create_sale = st.form_submit_button(
        "Create Sale",
        use_container_width=True,
    )

if create_sale:
    if not customer_name.strip():
        st.warning("Customer Name is required.")

    else:
        try:
            # Sales operations always use the authenticated client.
            sale_result = (
                supabase.table("sales")
                .insert({
                    "customer_name": customer_name.strip(),
                    "customer_phone": customer_phone.strip() or None,
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
                    supabase.table("sale_history").insert({
                        "sale_id": sale["id"],
                        "changed_by": user_id,
                        "previous_stage": None,
                        "new_stage": "Quality",
                        "action": "Sale Created",
                        "remarks": "Application created.",
                    }).execute()

                    st.success(
                        f"Sale created successfully. "
                        f"Reference: {sale['id']}"
                    )

                except Exception:
                    st.warning(
                        "The sale was created, but its history entry "
                        "could not be saved. Please contact the administrator."
                    )

                st.rerun()

            else:
                st.error("The sale could not be created.")

        except Exception:
            st.error(
                "Unable to create the sale. Check your database "
                "permissions or contact the administrator."
            )


# --------------------------------------------------
# SALES LIST
# --------------------------------------------------
st.divider()
st.subheader("📋 Sales Records")

try:
    query = (
        supabase.table("sales")
        .select(
            "id, customer_name, customer_phone, "
            "assigned_department, current_stage, status, created_at"
        )
        .order("created_at", desc=True)
    )

    # Preserve the existing initial visibility rules.
    # Database RLS must also enforce access.
    if role in ("agent", "department_staff"):
        query = query.eq("created_by", user_id)

    result = query.limit(200).execute()
    sales = result.data or []

    if sales:
        for sale in sales:
            with st.expander(
                f"{sale['customer_name']} — {sale['current_stage']}"
            ):
                st.write(f"**Reference:** {sale['id']}")
                st.write(
                    f"**Phone:** {sale.get('customer_phone') or '-'}"
                )
                st.write(
                    f"**Department:** {sale['assigned_department']}"
                )
                st.write(f"**Stage:** {sale['current_stage']}")
                st.write(f"**Status:** {sale['status']}")
                st.write(f"**Created:** {sale['created_at']}")

    else:
        st.info("No sales records are available to display.")

except Exception:
    st.error(
        "Unable to load sales records. Please check the database "
        "access policies."
    )


st.divider()
st.caption("Sales CRM | Username authentication and sales entry")
