# GPT-Powered Supervisor Dashboard

This project is a secure, web-based performance reporting tool built with Streamlit. It connects to Tableau to retrieve support agent metrics, formats those stats, and generates summaries using OpenAI's GPT-4 model. The dashboard includes both supervisor-facing and admin-facing features with granular access control.

---

## 🔧 Features

### 👤 Supervisor View
- Secure login using company email (`@fetchrewards.com`)
- Personalized dashboard showing only agents mapped to the logged-in supervisor
- Sidebar filters:
  - **Supervisor** selector (multi-select)
  - **Agent** selector (dynamic based on selected supervisors)
- GPT-generated agent summaries and team-wide summaries (when all agents selected)

### 🛠️ Admin Dashboard
- Accessible only to authorized admin emails
- Paginated error log viewer (20 rows per page)
- Filters by error code, agent, supervisor, and user email
- Enhanced logging with error codes and timestamps

### 🧠 GPT Summarization
- Connects to OpenAI's GPT-4 to summarize performance metrics into plain English
- Provides both individual summaries and aggregate team insights

### 🔐 Authentication
- New users can self-register (restricted to `@fetchrewards.com` addresses)
- Passwords are securely hashed and stored in `users.json`
- Session-based authentication with logout capability

---

## 📂 Project Structure

```
supervisor_dashboard/
├── main.py                  # Main Streamlit application
├── .env                     # Stores sensitive tokens (excluded from Git)
├── users.json               # Stores hashed user credentials
├── EMAIL_TO_AGENTS.json     # Agent → Supervisor email mapping
├── error_agent_data.log     # Error log with timestamps and error codes
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 🔑 Environment Variables (`.env`)

```
OPENAI_API_KEY=your_openai_key
TABLEAU_PAT_NAME=your_tableau_pat_name
TABLEAU_PAT_SECRET=your_tableau_pat_secret
```

---

## 🚀 Getting Started

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Run the app**

```bash
streamlit run main.py
```

3. **Log in or create an account**

- Email must match domain: `@fetchrewards.com`
- Must be mapped in `EMAIL_TO_AGENTS.json` to view any data

---

## 📊 Tableau Integration

- The app connects to a Tableau view named `"Team Metrics"`
- You must have a valid PAT (Personal Access Token) and permissions to query the Tableau Server
- Make sure your `site_id`, PAT name, and secret are correctly loaded via `.env`

---

## 🧪 Testing Locally

You can create test mappings like:

```json
{
  "fake@fetchrewards.com": ["John Doe", "John Doee", "John Doeee"]
}
```

Then login as that user to view filtered agent summaries.

---

## 📥 Deployment Notes

For deployment:
- Use **Streamlit Cloud** or internal server
- Ensure `.env`, `users.json`, and `EMAIL_TO_AGENTS.json` are properly configured
- Consider Git-ignoring sensitive files

---

## ✅ Future Enhancements

- Add MFA via email magic link or SMS
- CSV export of summaries
- Audit log of GPT responses and usage

---

## 🧑‍💻 Maintainer

Zach Thomson – [z.thomson@fetchrewards.com](mailto:z.thomson@fetchrewards.com)

For support or enhancements, open a PR or contact via Fetch Slack.
