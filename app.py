
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Sales CRM",
    page_icon="📋",
    layout="wide",
)

# --------------------------------------------------
# DATABASE CONNECTION — ISOLATED PER BROWSER SESSION
# --------------------------------------------------
def get_supabase():
    if "supabase_client" not in st.session_state:
        st.session_state["supabase_client"] = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
        )
    return st.session_state["supabase_client"]


try:
    supabase = get_supabase()
except Exception:
    st.error(
        "Unable to connect to the database. "
        "Please contact your administrator."
    )
    st.stop()


# --------------------------------------------------
# LOGIN
# --------------------------------------------------
def load_profile(user_id):
    result = (
        supabase.table("profiles")
        .select("id, full_name, role, department, is_active")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


if "user_id" not in st.session_state:
    st.title("📋 Sales CRM")
    st.caption("Secure sales and operations management")
    st.subheader("Sign in")

    with st.form("login_form"):
        email = st.text_input("Work email")
        password = st.text_input(
            "Password",
            type="password",
        )
        submitted = st.form_submit_button(
            "Sign in",
            use_container_width=True,
        )

    if submitted:
        if not email.strip() or not password:
            st.warning("Enter your work email and password.")
        else:
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password,
                })

                if not response.user:
                    st.error("Unable to sign in.")
                    st.stop()

                profile = load_profile(response.user.id)

                if not profile or not profile["is_active"]:
                    supabase.auth.sign_out()
                    st.error(
                        "Your CRM profile is missing or inactive. "
                        "Please contact the administrator."
                    )
                    st.stop()

                st.session_state["user_id"] = response.user.id
                st.session_state["user_email"] = response.user.email
                st.session_state["profile"] = profile

                st.rerun()

            except Exception:
                st.error(
                    "Sign-in or profile verification failed. "
                    "Check your credentials or contact the administrator."
                )

    st.stop()


# --------------------------------------------------
# VERIFY ACTIVE PROFILE ON EACH APP RERUN
# --------------------------------------------------
try:
    profile = load_profile(st.session_state["user_id"])

    if not profile or not profile["is_active"]:
        st.session_state.clear()
        st.error("Your account is inactive or unavailable. Please sign in again.")
        st.stop()

    st.session_state["profile"] = profile

except Exception:
    st.error(
        "Unable to verify your CRM profile. "
        "Please refresh the app or sign in again."
    )
    st.stop()


# --------------------------------------------------
# HEADER
# --------------------------------------------------
profile = st.session_state["profile"]
role = profile["role"]

with st.sidebar:
    st.title("📋 Sales CRM")
    st.divider()
    st.write(f"**User:** {profile['full_name']}")
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
# ROLE-BASED DASHBOARD LANDING PAGE
# --------------------------------------------------
if role == "admin":
    st.title("🛡️ Admin Dashboard")
    st.caption("Administration and organisation-wide oversight")

    st.info(
        "Admin access verified. The CRM management screens "
        "will be added in the next steps."
    )

elif role == "manager":
    st.title("📊 Manager Dashboard")
    st.caption("Sales oversight and Live authorisation")

    st.info(
        "Manager access verified. Sales monitoring and approval "
        "screens will be added next."
    )

elif role == "department_staff":
    st.title("📂 Department Dashboard")
    st.caption("Department operations and assigned applications")

    st.info(
        "Department access verified. Department queues "
        "will be added next."
    )

elif role == "agent":
    st.title("💼 My Sales Dashboard")
    st.caption("Your sales and application progress")

    st.info(
        "Agent access verified. Your personal sales list "
        "will be added next."
    )

else:
    st.error("Your account has an unrecognised role.")
    st.stop()

st.divider()
st.caption("Sales CRM | Initial dashboard")
