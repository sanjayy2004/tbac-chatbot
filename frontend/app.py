import streamlit as st
import requests
import json
from datetime import datetime

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Company Internal Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── API Configuration ──────────────────────────────────────────
API_BASE_URL = "http://127.0.0.1:8080"

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white !important;
        text-align: center;
        margin-bottom: 20px;
    }
    .user-message {
        background: #1e3a5f !important;
        padding: 15px;
        border-radius: 15px 15px 0px 15px;
        margin: 10px 0;
        border-left: 4px solid #2196F3;
        color: #ffffff !important;
    }
    .bot-message {
        background: #2d1b4e !important;
        padding: 15px;
        border-radius: 15px 15px 15px 0px;
        margin: 10px 0;
        border-left: 4px solid #9c27b0;
        color: #ffffff !important;
    }
    .source-card {
        background: #3d2b0e !important;
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        border-left: 3px solid #ff9800;
        font-size: 12px;
        color: #ffffff !important;
    }
    .user-message * {
        color: #ffffff !important;
    }
    .bot-message * {
        color: #ffffff !important;
    }
    .source-card * {
        color: #ffffff !important;
    }
    .main-header * {
        color: #ffffff !important;
    }
    .stTextInput > div > div > input {
        border-radius: 25px;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state initialization ───────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "token" not in st.session_state:
    st.session_state.token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── API Helper functions ───────────────────────────────────────
def login(username, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/login",
            data={"username": username, "password": password},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def get_user_info(token):
    try:
        response = requests.get(
            f"{API_BASE_URL}/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def send_chat(query, token):
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"query": query},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Chat error: {e}")
        return None

# ── Role colors ────────────────────────────────────────────────
ROLE_COLORS = {
    "finance": "#2ecc71",
    "hr": "#3498db",
    "marketing": "#e74c3c",
    "engineering": "#9b59b6",
    "employee": "#f39c12",
    "c_level": "#1abc9c"
}

ROLE_ICONS = {
    "finance": "💰",
    "hr": "👥",
    "marketing": "📢",
    "engineering": "⚙️",
    "employee": "👤",
    "c_level": "👑"
}

# ── Login Page ─────────────────────────────────────────────────
def show_login_page():
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Company Internal Chatbot</h1>
        <p>Secure Role-Based Access Control System</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🔐 Login to your account")

        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Login →", use_container_width=True)

            if submit:
                if not username or not password:
                    st.error("Please enter username and password!")
                else:
                    with st.spinner("Logging in..."):
                        result = login(username, password)
                    if result:
                        st.session_state.logged_in = True
                        st.session_state.token = result["access_token"]
                        st.session_state.user_info = {
                            "username": result["username"],
                            "name": result["name"],
                            "role": result["role"]
                        }
                        st.success(f"Welcome {result['name']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password!")

        st.markdown("---")
        st.markdown("### 👥 Demo Accounts")
        demo_accounts = [
            ("alice", "finance123", "Finance", "💰"),
            ("bob", "hr123", "HR", "👥"),
            ("carol", "mkt123", "Marketing", "📢"),
            ("dave", "eng123", "Engineering", "⚙️"),
            ("eve", "emp123", "Employee", "👤"),
            ("frank", "ceo123", "C-Level", "👑"),
        ]
        for user, pwd, role, icon in demo_accounts:
            st.markdown(f"{icon} **{user}** / `{pwd}` — {role}")

# ── Chat Page ──────────────────────────────────────────────────
def show_chat_page():
    user = st.session_state.user_info
    role = user["role"]
    role_color = ROLE_COLORS.get(role, "#95a5a6")
    role_icon = ROLE_ICONS.get(role, "👤")

    # ── Sidebar ────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style='background: {role_color}; padding: 15px; border-radius: 10px; color: white; text-align: center;'>
            <h2>{role_icon}</h2>
            <h3>{user['name']}</h3>
            <p>@{user['username']}</p>
            <p><b>{role.replace('_', ' ').title()}</b></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📁 Your Document Access")

        access_map = {
            "finance": ["💰 Financial Reports", "📋 General Handbook"],
            "hr": ["👥 HR Data", "📋 General Handbook"],
            "marketing": ["📢 Marketing Reports", "📋 General Handbook"],
            "engineering": ["⚙️ Technical Docs", "📋 General Handbook"],
            "employee": ["📋 General Handbook"],
            "c_level": ["💰 Finance", "👥 HR", "📢 Marketing", "⚙️ Engineering", "📋 General"]
        }

        for doc in access_map.get(role, []):
            st.markdown(f"✅ {doc}")

        st.markdown("---")
        st.markdown("### 💡 Sample Questions")

        sample_questions = {
            "finance": ["What is the total revenue?", "What are the quarterly expenses?", "What is the profit margin?"],
            "hr": ["What are the leave policies?", "What are employee benefits?", "What is the attendance policy?"],
            "marketing": ["What were Q1 marketing results?", "What is the customer acquisition rate?", "What are the marketing campaigns?"],
            "engineering": ["What is the system architecture?", "What are the technical processes?", "What tools do we use?"],
            "employee": ["What are the company policies?", "What are my leave entitlements?", "What are the office timings?"],
            "c_level": ["What is the total revenue?", "What are the HR policies?", "What are the marketing results?"]
        }

        for q in sample_questions.get(role, []):
            if st.button(q, use_container_width=True, key=q):
                st.session_state.pending_question = q

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.token = None
            st.session_state.user_info = None
            st.session_state.chat_history = []
            st.rerun()

    # ── Main chat area ─────────────────────────────────────────
    st.markdown(f"""
    <div class="main-header">
        <h2>🤖 Company Internal Chatbot</h2>
        <p>{role_icon} Logged in as <b>{user['name']}</b> | Role: <b>{role.replace('_', ' ').title()}</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Display chat history
    if not st.session_state.chat_history:
        st.markdown(f"""
        <div style='text-align: center; padding: 40px; color: #888;'>
            <h3>👋 Welcome {user['name']}!</h3>
            <p>Ask me anything about your company documents.</p>
            <p>I can only show you information relevant to your <b>{role.replace('_', ' ').title()}</b> role.</p>
        </div>
        """, unsafe_allow_html=True)

    for chat in st.session_state.chat_history:
        # User message
        st.markdown(f"""
        <div class="user-message">
            <b>👤 You:</b><br>{chat['query']}
            <br><small style='color: #888;'>{chat['time']}</small>
        </div>
        """, unsafe_allow_html=True)

        # Bot message
        st.markdown(f"""
        <div class="bot-message">
            <b>🤖 Assistant:</b><br>{chat['answer']}
        </div>
        """, unsafe_allow_html=True)

        # Sources
        if chat.get("sources"):
            with st.expander(f"📚 Sources ({len(chat['sources'])} documents)"):
                for source in chat["sources"]:
                    st.markdown(f"""
                    <div class="source-card">
                        📄 <b>{source['source']}</b> | 
                        🏢 Department: {source['department'].title()}
                    </div>
                    """, unsafe_allow_html=True)

        # Confidence
        if chat.get("confidence"):
            confidence_pct = int(chat["confidence"] * 100)
            st.markdown(f"**Confidence:** {confidence_pct}%")
            st.progress(chat["confidence"])

        st.markdown("---")

    # ── Chat input ─────────────────────────────────────────────
    # Handle sidebar button questions
    pending = st.session_state.get("pending_question", None)

    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Ask a question...",
                value=pending if pending else "",
                placeholder=f"Ask anything about your {role} documents...",
                label_visibility="collapsed"
            )
        with col2:
            send = st.form_submit_button("Send 🚀", use_container_width=True)

        if send and user_input:
            st.session_state.pending_question = None
            with st.spinner("🤖 Thinking..."):
                response = send_chat(user_input, st.session_state.token)

            if response:
                st.session_state.chat_history.append({
                    "query": user_input,
                    "answer": response["answer"],
                    "sources": response.get("sources", []),
                    "confidence": response.get("confidence", 0),
                    "time": datetime.now().strftime("%H:%M")
                })
                st.rerun()
            else:
                st.error("Failed to get response.Please try again.")

# ── Main app ───────────────────────────────────────────────────
def main():
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_chat_page()

if __name__ == "__main__":
    main()