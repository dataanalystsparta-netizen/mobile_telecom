
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Sales CRM", page_icon="📋")

st.title("Sales CRM")
st.write("Testing the database connection...")

try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

    result = supabase.table("sales").select("id").limit(1).execute()

    st.success("Connected to Supabase successfully!")
    st.write("Your CRM database is reachable.")

except Exception as e:
    st.error("Database connection test failed.")
    st.code(str(e))
