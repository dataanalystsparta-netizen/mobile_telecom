
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Sales CRM",
    page_icon="📋",
    layout="wide",
)


# --------------------------------------------------
# DATABASE CONNECTION
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
    st.error("Unable to connect to the CRM database.")
    st.stop()


# --------------------------------------------------
# PROFILE LOOKUP
# --------------------------------------------------
def load_profile(user_id):
    result = (
        supabase.table("profiles")
        .select("id, full_name, role, department, is_active")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# --------------------------------------------------
# LOGIN
# --------------------------------------------------
if "user_id" not in st.session_state:
    st.title("📋 Sales CRM")
    st.caption("Secure sales and operations management")
    st.subheader("Sign in")

    with st.form("login_form"):
        email = st.text_input("Work email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Sign in",
            use_container_width=True,
        )

    if submitted:
        if not email.strip() or not password:
            st.warning("Enter your email and password.")
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
                        "Your account is inactive or has no CRM profile."
                    )
                    st.stop()

                st.session_state["user_id"] = response.user.id
                st.session_state["user_email"] = response.user.email
                st.session_state["profile"] = profile
                st.rerun()

            except Exception:
                st.error(
                    "Sign-in failed. Check your credentials and try again."
                )

    st.stop()


# --------------------------------------------------
# VERIFY PROFILE
# --------------------------------------------------
try:
    profile = load_profile(st.session_state["user_id"])

    if not profile or not profile["is_active"]:
        st.session_state.clear()
        st.error("Your CRM account is inactive or unavailable.")
        st.stop()

    st.session_state["profile"] = profile

except Exception:
    st.error("Unable to verify your CRM profile.")
    st.stop()


profile = st.session_state["profile"]
role = profile["role"]
user_id = st.session_state["user_id"]


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
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

    # Agents and department staff initially see their own records.
    # RLS remains responsible for enforcing database access.
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
st.caption("Sales CRM | Initial sales-entry module")
