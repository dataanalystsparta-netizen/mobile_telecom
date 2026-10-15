
import re

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
    if "supabase_client" not in st.session_state:
        st.session_state["supabase_client"] = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
        )
    return st.session_state["supabase_client"]


def get_admin_supabase():
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
    try:
        response = supabase.auth.get_user()
        user = response.user

        if (
            not user
            or str(user.id) != str(st.session_state.get("user_id"))
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
        raise PermissionError("Active Admin access is required.")

    return profile


# --------------------------------------------------
# USERNAME LOGIN
# --------------------------------------------------
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
        password = st.text_input("Password", type="password")
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
                                    "Your account is inactive or "
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
                    "Sign-in failed. Check your credentials and try again."
                )

    st.stop()


# --------------------------------------------------
# VERIFY CURRENT USER
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

    with st.expander("➕ Create New User", expanded=False):
        with st.form("create_user_form", clear_on_submit=True):
            full_name = st.text_input("Employee Full Name *")
            new_username = st.text_input("Username *")
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
            department = st.selectbox("Department *", DEPARTMENTS)

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
                st.warning("Employee Full Name is required.")
            elif not valid_username:
                st.warning(
                    "Username must be 3–32 characters and contain "
                    "only letters, numbers, dots, underscores or hyphens."
                )
            elif len(new_password) < 8:
                st.warning("Password must be at least 8 characters.")
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
                        st.warning("That username already exists.")
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
                            st.error("Unable to create the Auth account.")
                        else:
                            created_user_id = str(
                                auth_response.user.id
                            )

                            (
                                admin_client.table("profiles")
                                .update({
                                    "full_name": full_name,
                                    "username": new_username,
                                    "role": ROLES[selected_role_label],
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
                                "Share the initial password securely "
                                "with the employee."
                            )
                            st.rerun()

                except PermissionError:
                    st.error("Only an active Admin can create users.")
                except Exception:
                    if created_user_id:
                        try:
                            require_active_admin()
                            get_admin_supabase().auth.admin.delete_user(
                                created_user_id
                            )
                        except Exception:
                            pass

                    st.error(
                        "Account creation failed. Check Supabase Auth, "
                        "the profile trigger, and database settings."
                    )

    st.markdown("#### Existing Employees")

    try:
        require_active_admin()
        admin_client = get_admin_supabase()

        users_result = (
            admin_client.table("profiles")
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
                        "Employee": u.get("full_name") or "-",
                        "Username": u.get("username") or "-",
                        "Role": (
                            u.get("role") or "-"
                        ).replace("_", " ").title(),
                        "Department": u.get("department") or "-",
                        "Active": (
                            "Yes" if u.get("is_active") else "No"
                        ),
                        "Created": u.get("created_at") or "-",
                    }
                    for u in users
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
                        "could not be saved."
                    )

                st.rerun()
            else:
                st.error("The sale could not be created.")

        except Exception:
            st.error(
                "Unable to create the sale. Check database permissions."
            )


# --------------------------------------------------
# SALES RECORDS AND QUALITY REVIEW
# --------------------------------------------------
st.divider()
st.subheader("📋 Sales Records")

try:
    query = (
        supabase.table("sales")
        .select(
            "id, customer_name, customer_phone, "
            "created_by, assigned_department, current_stage, "
            "status, rejection_reason, created_at"
        )
        .order("created_at", desc=True)
    )

    if role == "agent":
        query = query.eq("created_by", user_id)
    elif role == "department_staff":
        query = query.eq(
            "assigned_department",
            profile["department"],
        )

    result = query.limit(200).execute()
    sales = result.data or []

    if not sales:
        st.info("No sales records are available to display.")

    for sale in sales:
        sale_id = sale["id"]
        is_quality_review = (
            sale["current_stage"] == "Quality"
            and sale["assigned_department"] == "Quality"
            and sale["status"] == "Pending"
        )

        with st.expander(
            f"{sale['customer_name']} — "
            f"{sale['current_stage']} — {sale['status']}"
        ):
            st.write(f"**Reference:** {sale_id}")
            st.write(
                f"**Phone:** {sale.get('customer_phone') or '-'}"
            )
            st.write(
                f"**Department:** {sale['assigned_department']}"
            )
            st.write(f"**Stage:** {sale['current_stage']}")
            st.write(f"**Status:** {sale['status']}")
            st.write(
                f"**Created:** {sale.get('created_at') or '-'}"
            )

            if sale.get("rejection_reason"):
                st.error(
                    f"**Rejection reason:** "
                    f"{sale['rejection_reason']}"
                )

            # Review controls are displayed only for eligible users.
            if (
                role == "admin"
                or (
                    role == "department_staff"
                    and profile["department"] == "Quality"
                )
            ) and is_quality_review:
                st.divider()
                st.markdown("#### Quality Review")

                decision_key = f"quality_decision_{sale_id}"
                remarks_key = f"quality_remarks_{sale_id}"

                decision = st.radio(
                    "Decision",
                    ["Approve", "Reject"],
                    horizontal=True,
                    key=decision_key,
                )

                remarks = st.text_area(
                    "Remarks" if decision == "Approve"
                    else "Rejection Reason *",
                    key=remarks_key,
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
                    if decision == "Reject" and not remarks.strip():
                        st.warning(
                            "A rejection reason is required."
                        )
                    else:
                        try:
                            # The database function validates the
                            # user's permissions and current sale state.
                            response = supabase.rpc(
                                "review_sale_quality",
                                {
                                    "p_sale_id": sale_id,
                                    "p_decision": (
                                        "Approved"
                                        if decision == "Approve"
                                        else "Rejected"
                                    ),
                                    "p_remarks": remarks.strip() or None,
                                },
                            ).execute()

                            st.success(
                                f"Quality decision submitted: {decision}."
                            )
                            st.rerun()

                        except Exception:
                            st.error(
                                "The Quality decision could not be "
                                "saved. The sale may have already been "
                                "reviewed, or your permissions may "
                                "have changed. Refresh and try again."
                            )

except Exception:
    st.error(
        "Unable to load sales records. Check the database access policies."
    )


st.divider()
st.caption("Sales CRM | Quality Review workflow")
