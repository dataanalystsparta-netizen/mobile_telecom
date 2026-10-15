
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Sales CRM",
    page_icon="📋",
    layout="wide",
)

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

try:
    supabase = get_supabase()
except Exception:
    st.error("Unable to connect to the CRM database. Please contact the administrator.")
    st.stop()

st.title("Sales CRM")
st.caption("Secure sales and operations management")

st.subheader("Sign in")

with st.form("login_form"):
    email = st.text_input("Work email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if not email.strip() or not password:
            st.warning("Please enter your email and password.")
        else:
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password,
                })

                if response.user:
                    st.session_state["user_id"] = response.user.id
                    st.session_state["user_email"] = response.user.email
                    st.success("Sign-in successful!")
                    st.rerun()

            except Exception:
                st.error("Sign-in failed. Check your credentials and try again.")

if st.session_state.get("user_id"):
    st.success(f"Signed in as {st.session_state.get('user_email', '')}")
    if st.button("Sign out"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()
