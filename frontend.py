import streamlit as st
import time
import uuid
from datetime import datetime, date

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

# ── Theme ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background: radial-gradient(ellipse 120% 80% at 50% -10%, #0f1b2e 0%, #080d14 55%);
}
* { scrollbar-width: thin; scrollbar-color: #23364f #0a0f1a; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-thumb { background: #23364f; border-radius: 10px; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 6rem; max-width: 900px; }

/* ── Login ── */
.login-wrapper { display: flex; justify-content: center; align-items: center; height: 78vh; }
.login-card {
    background: linear-gradient(180deg, #101b2c 0%, #0b1420 100%);
    border: 1px solid #1e2e44; border-radius: 20px;
    padding: 2.4rem 2.6rem; width: 400px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(58,123,213,0.06) inset;
}
.login-badge {
    background: rgba(58,123,213,0.16); border: 1px solid rgba(58,123,213,0.4);
    color: #7ab8f5; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; padding: 0.32rem 0.9rem; border-radius: 20px;
    display: inline-block; margin-bottom: 1.1rem;
}
.login-title { color: #f2f8ff; font-size: 1.7rem; font-weight: 800; margin-bottom: 0.3rem; }
.login-sub { color: #6b8bab; font-size: 0.85rem; margin-bottom: 1.6rem; }
.stTextInput input {
    background: #0d1520 !important; border: 1px solid #1e2e44 !important;
    color: #e8f4ff !important; border-radius: 10px !important;
}
.stTextInput input:focus { border-color: #3a7bd5 !important; box-shadow: 0 0 0 3px rgba(58,123,213,0.15) !important; }
.stButton button {
    border-radius: 10px !important; font-weight: 600 !important; transition: all 0.15s ease !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #090e18 !important; border-right: 1px solid #141f30 !important;
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }
.brand-row {
    display: flex; align-items: center; gap: 0.6rem; margin-bottom: 1.1rem; padding: 0 0.2rem;
}
.brand-icon {
    width: 34px; height: 34px; border-radius: 10px;
    background: linear-gradient(135deg, #3a7bd5, #0a3d75);
    display: flex; align-items: center; justify-content: center; font-size: 1.1rem;
    box-shadow: 0 4px 14px rgba(58,123,213,0.35);
}
.brand-name { color: #f2f8ff; font-weight: 800; font-size: 1.05rem; letter-spacing: -0.01em; }

div[data-testid="stSidebar"] button[kind="primary"] {
    background: linear-gradient(135deg, #2f7de0 0%, #0a3d75 100%) !important;
    color: #fff !important; border: none !important;
    box-shadow: 0 6px 16px rgba(47,125,224,0.3) !important;
}
div[data-testid="stSidebar"] button[kind="primary"]:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(47,125,224,0.42) !important; }

.sidebar-section-label {
    color: #4b6580; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase;
    margin: 1.1rem 0.2rem 0.4rem;
}

/* chat row buttons in sidebar (secondary look) */
section[data-testid="stSidebar"] button[kind="secondary"] {
    background: transparent !important; color: #a8c4de !important; border: 1px solid transparent !important;
    text-align: left !important; justify-content: flex-start !important; font-weight: 500 !important;
    font-size: 0.85rem !important; padding: 0.45rem 0.7rem !important;
}
section[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: #101c2c !important; border-color: #1e2e44 !important; color: #eaf3ff !important;
}
.chat-row-active button[kind="secondary"] {
    background: #14243a !important; border-left: 3px solid #3a7bd5 !important; color: #fff !important;
    font-weight: 600 !important;
}

.icon-btn button {
    background: transparent !important; border: 1px solid transparent !important; color: #4b6580 !important;
    padding: 0.3rem !important; font-size: 0.8rem !important; min-height: 0 !important;
}
.icon-btn button:hover { color: #e05a5a !important; background: rgba(224,90,90,0.1) !important; }

.user-pill {
    display: flex; align-items: center; gap: 0.6rem; padding: 0.55rem 0.6rem;
    background: #0d1522; border: 1px solid #182234; border-radius: 12px; margin-top: 0.5rem;
}
.user-avatar {
    width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
    background: linear-gradient(135deg, #5aa8f0, #2755a8);
    display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; font-size: 0.8rem;
}
.user-name { color: #dbe9f7; font-size: 0.85rem; font-weight: 600; }
.user-status { color: #4b8a5e; font-size: 0.7rem; }

/* ── Empty state ── */
.empty-hero { text-align: center; padding: 3.5rem 1rem 1.5rem; }
.empty-icon {
    width: 62px; height: 62px; border-radius: 18px; margin: 0 auto 1.1rem;
    background: linear-gradient(135deg, #3a7bd5, #163d70);
    display: flex; align-items: center; justify-content: center; font-size: 1.7rem;
    box-shadow: 0 10px 30px rgba(58,123,213,0.35);
}
.empty-title { color: #f2f8ff; font-size: 1.55rem; font-weight: 800; margin-bottom: 0.4rem; }
.empty-sub { color: #6b8bab; font-size: 0.9rem; margin-bottom: 1.8rem; }

div[data-testid="column"] .stButton button[kind="secondary"] {
    background: #0e1623 !important; border: 1px solid #1e2e44 !important; color: #b9d3ec !important;
    border-radius: 12px !important; padding: 0.7rem 0.5rem !important; font-size: 0.83rem !important;
    width: 100%; transition: all 0.15s ease;
}
div[data-testid="column"] .stButton button[kind="secondary"]:hover {
    border-color: #3a7bd5 !important; background: #101d30 !important; transform: translateY(-2px);
}

/* ── Chat bubbles ── */
.msg-row { display: flex; margin-bottom: 1.1rem; gap: 0.6rem; align-items: flex-end; }
.msg-row.user { justify-content: flex-end; }
.msg-row.assistant { justify-content: flex-start; }
.avatar-sm {
    width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700;
}
.avatar-sm.assistant { background: linear-gradient(135deg, #3a7bd5, #0a3d75); color: #fff; }
.avatar-sm.user { background: #1a3a5c; color: #cfe4fb; }
.bubble {
    max-width: 68%; padding: 0.75rem 1.05rem; border-radius: 16px; line-height: 1.6;
    font-size: 0.93rem; word-wrap: break-word;
}
.bubble.user {
    background: linear-gradient(135deg, #2f6fb8, #1a3a5c); color: #f2f8ff; border-bottom-right-radius: 5px;
}
.bubble.assistant {
    background: #0e1623; border: 1px solid #1e2e44; color: #d7e6f5; border-bottom-left-radius: 5px;
}
.msg-meta { font-size: 0.68rem; color: #4b6580; margin-top: 0.3rem; }
.msg-col { display: flex; flex-direction: column; }
.msg-col.user { align-items: flex-end; }

/* Typing indicator */
.typing-dots span {
    display: inline-block; width: 6px; height: 6px; margin-right: 3px;
    background: #7ab8f5; border-radius: 50%; animation: blink 1.2s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }

/* Chat input */
div[data-testid="stChatInput"] textarea {
    background: #0e1623 !important; border: 1px solid #1e2e44 !important; color: #e8f4ff !important;
}
div[data-testid="stChatInput"] { border-top: 1px solid #141f30 !important; }
</style>
""", unsafe_allow_html=True)

# ── Auth (demo credentials — replace with real auth before shipping) ─────────
VALID_USER = "anshu"
VALID_PASS = "anshu@123"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "chats" not in st.session_state:
    st.session_state.chats = {}          # {chat_id: {"title": str, "messages": [...], "created": ts, "pinned": bool}}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "renaming_id" not in st.session_state:
    st.session_state.renaming_id = None


def login_page():
    st.markdown("<div class='login-wrapper'>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<div class='login-badge'>✦ Secure Sign In</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>Welcome back</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-sub'>Sign in to continue your conversations</div>", unsafe_allow_html=True)

        user_id = st.text_input("User ID", placeholder="Enter your User ID")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        remember = st.checkbox("Remember me")

        if st.button("Sign In", use_container_width=True, type="primary"):
            if user_id == VALID_USER and password == VALID_PASS:
                st.session_state.authenticated = True
                st.session_state.user_id = user_id
                st.rerun()
            else:
                st.error("Invalid User ID or Password")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def new_chat():
    chat_id = str(uuid.uuid4())[:8]
    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "messages": [],
        "created": datetime.now(),
        "pinned": False,
    }
    st.session_state.active_chat_id = chat_id


def date_bucket(ts: datetime) -> str:
    d = ts.date()
    today = date.today()
    delta = (today - d).days
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Yesterday"
    if delta <= 7:
        return "Previous 7 days"
    return "Older"


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="brand-row">
            <div class="brand-icon">💬</div>
            <div class="brand-name">AI Chat</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("＋  New chat", use_container_width=True, type="primary"):
            new_chat()
            st.rerun()

        search = st.text_input("Search chats", label_visibility="collapsed",
                                placeholder="🔍  Search chats")

        all_chats = list(st.session_state.chats.items())
        if search:
            all_chats = [(cid, c) for cid, c in all_chats if search.lower() in c["title"].lower()]

        pinned = [(cid, c) for cid, c in all_chats if c.get("pinned")]
        unpinned = sorted(
            [(cid, c) for cid, c in all_chats if not c.get("pinned")],
            key=lambda kv: kv[1]["created"], reverse=True
        )

        def render_chat_row(cid, chat):
            is_active = cid == st.session_state.active_chat_id
            is_renaming = st.session_state.renaming_id == cid
            row_class = "chat-row-active" if is_active else ""
            st.markdown(f"<div class='{row_class}'>", unsafe_allow_html=True)

            if is_renaming:
                new_title = st.text_input("rename", value=chat["title"], key=f"rename_{cid}",
                                           label_visibility="collapsed")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Save", key=f"save_{cid}", use_container_width=True):
                        chat["title"] = new_title.strip() or chat["title"]
                        st.session_state.renaming_id = None
                        st.rerun()
                with c2:
                    if st.button("Cancel", key=f"cancel_{cid}", use_container_width=True):
                        st.session_state.renaming_id = None
                        st.rerun()
            else:
                col1, col2, col3, col4 = st.columns([7, 1, 1, 1])
                with col1:
                    label = f"📌 {chat['title']}" if chat.get("pinned") else chat["title"]
                    if st.button(label, key=f"select_{cid}", use_container_width=True):
                        st.session_state.active_chat_id = cid
                        st.rerun()
                with col2:
                    st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
                    if st.button("📌", key=f"pin_{cid}", help="Pin/unpin"):
                        chat["pinned"] = not chat.get("pinned", False)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with col3:
                    st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
                    if st.button("✏️", key=f"edit_{cid}", help="Rename"):
                        st.session_state.renaming_id = cid
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with col4:
                    st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{cid}", help="Delete"):
                        del st.session_state.chats[cid]
                        if st.session_state.active_chat_id == cid:
                            st.session_state.active_chat_id = None
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if pinned:
            st.markdown("<div class='sidebar-section-label'>📌 Pinned</div>", unsafe_allow_html=True)
            for cid, chat in pinned:
                render_chat_row(cid, chat)

        buckets = {}
        for cid, chat in unpinned:
            b = date_bucket(chat["created"])
            buckets.setdefault(b, []).append((cid, chat))

        for label in ["Today", "Yesterday", "Previous 7 days", "Older"]:
            if label in buckets:
                st.markdown(f"<div class='sidebar-section-label'>{label}</div>", unsafe_allow_html=True)
                for cid, chat in buckets[label]:
                    render_chat_row(cid, chat)

        if not all_chats:
            st.markdown("<div class='sidebar-section-label'>No chats yet</div>", unsafe_allow_html=True)

        st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
        uid = st.session_state.get('user_id', 'user')
        st.markdown(f"""
        <div class="user-pill">
            <div class="user-avatar">{uid[0].upper()}</div>
            <div>
                <div class="user-name">{uid}</div>
                <div class="user-status">● Online</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Log out", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()


def render_message(role, content, timestamp=None):
    align = "user" if role == "user" else "assistant"
    ts = timestamp or datetime.now().strftime("%H:%M")
    avatar = "🧑" if role == "user" else "✨"
    if align == "user":
        st.markdown(f"""
        <div class="msg-row user">
            <div class="msg-col user">
                <div class="bubble user">{content}</div>
                <div class="msg-meta">{ts}</div>
            </div>
            <div class="avatar-sm user">{avatar}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="msg-row assistant">
            <div class="avatar-sm assistant">{avatar}</div>
            <div class="msg-col">
                <div class="bubble assistant">{content}</div>
                <div class="msg-meta">{ts}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def stream_response(user_text: str):
    """
    Placeholder streaming response.
    Replace this generator with your actual LLM call
    (e.g. yielding tokens from `app.stream(...)`).
    """
    fake_response = f"You said: \"{user_text}\". Here's a streamed reply to demonstrate the chat UX."
    for word in fake_response.split(" "):
        yield word + " "
        time.sleep(0.05)


def render_chat_interface():
    render_sidebar()

    if st.session_state.active_chat_id is None:
        st.markdown("""
        <div class="empty-hero">
            <div class="empty-icon">✨</div>
            <div class="empty-title">How can I help you today?</div>
            <div class="empty-sub">Start a new conversation or pick a suggestion below</div>
        </div>
        """, unsafe_allow_html=True)
        suggestions = [("🧭", "Plan a trip"), ("📄", "Summarize a doc"),
                        ("💡", "Explain a concept"), ("👨‍💻", "Write code")]
        cols = st.columns(len(suggestions))
        for col, (icon, s) in zip(cols, suggestions):
            with col:
                if st.button(f"{icon}  {s}", use_container_width=True, key=f"sugg_{s}"):
                    new_chat()
                    st.session_state.pending_prompt = s
                    st.rerun()
        return

    chat = st.session_state.chats[st.session_state.active_chat_id]

    for msg in chat["messages"]:
        render_message(msg["role"], msg["content"], msg.get("timestamp"))

    pending = st.session_state.pop("pending_prompt", None)
    user_input = st.chat_input("Message the assistant...")
    prompt = pending or user_input

    if prompt:
        if chat["title"] == "New Chat":
            chat["title"] = prompt[:40]

        chat["messages"].append({
            "role": "user", "content": prompt,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        render_message("user", prompt)

        placeholder = st.empty()
        placeholder.markdown("""
        <div class="msg-row assistant">
            <div class="avatar-sm assistant">✨</div>
            <div class="msg-col">
                <div class="bubble assistant typing-dots"><span></span><span></span><span></span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        full_text = ""
        for chunk in stream_response(prompt):
            full_text += chunk
            placeholder.markdown(f"""
            <div class="msg-row assistant">
                <div class="avatar-sm assistant">✨</div>
                <div class="msg-col">
                    <div class="bubble assistant">{full_text}▌</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        placeholder.markdown(f"""
        <div class="msg-row assistant">
            <div class="avatar-sm assistant">✨</div>
            <div class="msg-col">
                <div class="bubble assistant">{full_text}</div>
                <div class="msg-meta">{datetime.now().strftime("%H:%M")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        chat["messages"].append({
            "role": "assistant", "content": full_text,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        st.rerun()


# ── Router ─────────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    login_page()
else:
    render_chat_interface()