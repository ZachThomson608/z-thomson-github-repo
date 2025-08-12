# main.py — Secure Streamlit GPT Dashboard with AWS Fallback Secrets, Guide, and Admin Support

import streamlit as st
import pandas as pd
import os
import json
import io
import hashlib
import logging
from openai import OpenAI
from dotenv import load_dotenv

# --- Secure Secrets: AWS fallback support ---
try:
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError

    def get_secret(secret_name):
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])

    secrets = get_secret("streamlit/gpt_dashboard/secrets")
except Exception:
    load_dotenv()
    secrets = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "TABLEAU_PAT_NAME": os.getenv("TABLEAU_PAT_NAME"),
        "TABLEAU_PAT_SECRET": os.getenv("TABLEAU_PAT_SECRET")
    }

from tableau_api_lib import TableauServerConnection
from tableau_api_lib.utils.querying import get_views_dataframe

# --- CONFIG ---
st.set_page_config(page_title="Supervisor Dashboard", layout="wide")

OPENAI_API_KEY = secrets.get("OPENAI_API_KEY")
TABLEAU_TOKEN_NAME = secrets.get("TABLEAU_PAT_NAME")
TABLEAU_TOKEN_SECRET = secrets.get("TABLEAU_PAT_SECRET")
TABLEAU_SERVER = "https://tableau.fetchrewards.com"
TABLEAU_SITE_ID = ""
client = OpenAI(api_key=OPENAI_API_KEY)

LOG_FILE = "error_agent_data.log"
CREDENTIALS_FILE = "users.json"
EMAIL_TO_AGENTS_FILE = "EMAIL_TO_AGENTS.json"
ADMIN_EMAILS = ["z.thomson@fetchrewards.com", "b.johnson@fetchrewards.com"]

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def log_error(code, msg):
    logging.error(f"[{code}] {msg}")

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

# --- Load users ---
if not os.path.exists(CREDENTIALS_FILE):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump({}, f)
with open(CREDENTIALS_FILE) as f:
    try:
        users = json.load(f)
    except json.JSONDecodeError:
        users = {}

# --- Load agent mappings ---
if not os.path.exists(EMAIL_TO_AGENTS_FILE):
    st.error("EMAIL_TO_AGENTS.json missing. [E9001]")
    log_error("E9001", "Missing EMAIL_TO_AGENTS.json")
    st.stop()
with open(EMAIL_TO_AGENTS_FILE) as f:
    EMAIL_TO_AGENTS = json.load(f)

ALL_SUPERVISORS = sorted(EMAIL_TO_AGENTS.keys())
ALL_AGENTS = sorted({agent for agents in EMAIL_TO_AGENTS.values() for agent in agents})
AGENT_TO_SUPERVISOR_EMAIL = {
    agent: sup_email
    for sup_email, agents in EMAIL_TO_AGENTS.items()
    for agent in agents
}

# --- Login + Signup ---
tab1, tab2 = st.sidebar.tabs(["🔐 Login", "🆕 Sign Up"])
with tab1:
    st.subheader("Login")
    email = st.text_input("Email")
    pw = st.text_input("Password", type="password")
    if st.button("Log In"):
        if email in users and hash_pw(pw) == users[email]["hash"]:
            st.session_state["logged_in"] = True
            st.session_state["email"] = email
        else:
            st.error("❌ Invalid credentials. [E1001]")
            log_error("E1001", f"Login failed: {email}")
with tab2:
    st.subheader("Create Account")
    email = st.text_input("Your Fetch Email")
    pw1 = st.text_input("Create Password", type="password")
    pw2 = st.text_input("Confirm Password", type="password")
    if st.button("Create Account"):
        if not email.endswith("@fetchrewards.com"):
            st.error("Must use a @fetchrewards.com email. [E1002]")
        elif pw1 != pw2:
            st.error("Passwords do not match. [E1003]")
        elif email in users:
            st.error("User already exists. [E1004]")
        elif email not in EMAIL_TO_AGENTS and email not in ADMIN_EMAILS:
            st.error("You are not mapped to any agents. Contact admin. [E2001]")
        else:
            users[email] = {"hash": hash_pw(pw1)}
            with open(CREDENTIALS_FILE, "w") as f:
                json.dump(users, f)
            st.session_state["just_signed_up"] = True
            st.success("✅ Account created. Please log in.")

if "logged_in" not in st.session_state:
    st.stop()

# --- Logout ---
if st.sidebar.button("🚪 Log Out"):
    st.session_state.clear()
    st.markdown("<meta http-equiv='refresh' content='0'>", unsafe_allow_html=True)
    st.stop()

email = st.session_state["email"]
IS_ADMIN = email in ADMIN_EMAILS
agent_list = EMAIL_TO_AGENTS.get(email, [])
if IS_ADMIN and not agent_list:
    agent_list = ALL_AGENTS
if not agent_list:
    st.error("No agents mapped to your account. [E2001]")
    log_error("E2001", f"No agents mapped for {email}")
    st.stop()

# --- Welcome + Guide ---
first_name = email.split("@")[0].split(".")[0].capitalize()
st.title("📊 GPT-Powered Supervisor Insights Dashboard")
st.markdown(f"👋 Welcome, **{first_name}**! Use this tool to generate reports and insights for your team.")

if st.session_state.get("just_signed_up"):
    st.success(f"👋 Welcome, {first_name}! Your account has been created.")
    st.markdown("""
    ### 🚀 How to Use This Dashboard

    1. **Filter your team** using the sidebar — select supervisors and agents.
    2. **Click 'Run Report'** to fetch and summarize data from Tableau.
    3. **Read GPT summaries** for each agent and the full team.
    4. **Admins** can review error logs using the Admin Dashboard.
    """)
    st.session_state["just_signed_up"] = False

# --- Filters ---
st.sidebar.markdown("### 🧭 Filters")
selected_supervisors = st.sidebar.multiselect("Supervisors", ALL_SUPERVISORS, default=ALL_SUPERVISORS)
filtered_agents = sorted({
    agent for sup, agents in EMAIL_TO_AGENTS.items() if sup in selected_supervisors for agent in agents
})
selected_agents = st.sidebar.multiselect("Agents", filtered_agents, default=filtered_agents)
if not selected_agents:
    st.warning("Select at least one agent. [E2002]")
    st.stop()

# --- GPT REPORTING ---
st.subheader("📥 Run Report")
if st.button("Run Report"):
    try:
        config = {
            'default': {
                'server': TABLEAU_SERVER,
                'api_version': '3.23',
                'personal_access_token_name': TABLEAU_TOKEN_NAME,
                'personal_access_token_secret': TABLEAU_TOKEN_SECRET,
                'site_id': TABLEAU_SITE_ID,
                'site_name': 'default',
                'site_url': ''
            }
        }
        conn = TableauServerConnection(config, env='default')
        conn.sign_in()
        view_id = get_views_dataframe(conn)[
            lambda df: df['name'].str.contains("Team Metrics", case=False)
        ].iloc[0]['id']
        csv = conn.query_view_data(view_id=view_id)
        conn.sign_out()
        raw = pd.read_csv(io.StringIO(csv.text))
        df = raw[raw["FETCH_NAME"].isin(selected_agents)]
        if df.empty:
            st.error("No data found for selected agents.")
            st.stop()
        pivot = df.pivot_table(index="FETCH_NAME", columns="Measure Names", values="Measure Values", aggfunc="first").reset_index().fillna(0)

        def format_stats(row):
            return "\n".join([
                f"- {col}: {round(val, 2)}{'%' if 'Rate' in col or 'Utilization' in col else ''}"
                for col, val in row.items() if col != "FETCH_NAME"
            ])
        pivot["Stat Block"] = pivot.apply(format_stats, axis=1)

        if set(selected_agents) == set(filtered_agents):
            st.subheader("🧠 Team Summary")
            sample_stats = pivot["Stat Block"].head(3).to_string()
            team_summary = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Summarize this:\n{sample_stats}"}]
            )
            st.markdown(team_summary.choices[0].message.content.strip())

        for _, row in pivot.iterrows():
            st.subheader(f"📌 {row['FETCH_NAME']}")
            st.code(row["Stat Block"])
            summary = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Summarize:\n{row['Stat Block']}"}]
            )
            st.markdown(summary.choices[0].message.content.strip())
    except Exception as e:
        st.error("Failed to generate report. [E9999]")
        log_error("E9999", f"Report error: {e}")
