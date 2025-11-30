import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
from database import (
    add_user, validate_user, create_session, save_message,
    get_user_sessions, get_chat_messages, rename_session, delete_session
)

# -------------------------------
# CONFIG
# -------------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

FREE_LIMIT = 2  # Free guest questions

# -------------------------------
# Gemini Vision Function
# -------------------------------
def get_gemini_vision_response(image, prompt):
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        st.error(f"⚠️ Gemini API Error: {e}")
        return None

# -------------------------------
# LOGIN PAGE
# -------------------------------
def login_page():
    # Header: Logo + Text
    col1, col2 = st.columns([1, 3])
    with col1:
        logo = Image.open("static/saanra_logo.jpeg")  # local image
        st.image(logo, width=60)
    with col2:
        st.markdown("<h1 style='margin:0; color:#4c9dff;'>Saanra AI</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin:0; color:white;'>Login to your account</h3>", unsafe_allow_html=True)

    st.write("")  # spacing

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            user_id = validate_user(username, password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.session_state.page = "chat"
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    with col2:
        if st.button("Sign Up"):
            st.session_state.page = "signup"
            st.rerun()




# -------------------------------
# SIGNUP PAGE
# -------------------------------
def signup_page():
    # Header: Logo + Text
    col1, col2 = st.columns([1, 3])
    with col1:
        logo = Image.open("static/saanra_logo.jpeg")  # local image
        st.image(logo, width=60)
    with col2:
        st.markdown("<h1 style='margin:0; color:#4c9dff;'>Saanra AI</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin:0; color:white;'>Create an Account</h3>", unsafe_allow_html=True)

    st.write("")  # spacing

    username = st.text_input("Choose Username")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if username.strip() == "" or password.strip() == "":
            st.error("⚠️ Fill all fields")
        elif password != confirm:
            st.error("⚠️ Passwords do not match")
        else:
            if add_user(username, password):
                st.success("✅ Account created! Please login.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error("⚠️ Username already exists")


# -------------------------------
# CHAT PAGE
# -------------------------------
def chat_page():
    st.write(f"Welcome, **{st.session_state.username}** 👋")

    user_id = st.session_state.user_id

    # Initialize session states
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = []
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "guest_messages" not in st.session_state:
        st.session_state.guest_messages = 0

    # -------------------------------
    # Sidebar - Chat Sessions
    # -------------------------------
    st.sidebar.title("💾 Chat Sessions")
    sessions = get_user_sessions(user_id)
    session_dict = {s[1]: s[0] for s in sessions}  # name -> id

    for name in reversed(session_dict.keys()):
        session_id = session_dict[name]
        with st.sidebar.expander(f"🗨️ {name}", expanded=False):
            if st.button("Open Chat", key=f"open_{session_id}"):
                st.session_state.session_id = session_id
                messages = get_chat_messages(session_id)
                st.session_state.current_chat = [
                    {"question": m[1], "answer": ""} if m[0] == "user" else {"question": "", "answer": m[1]}
                    for m in messages
                ]
                st.session_state.uploaded_image = None
                st.rerun()
            # Rename
            new_name_key = f"rename_input_{session_id}"
            rename_btn_key = f"rename_btn_{session_id}"
            st.text_input("Rename chat:", key=new_name_key, value=name)
            if st.button("Rename", key=rename_btn_key):
                new_name = st.session_state.get(new_name_key, "").strip()
                if new_name:
                    rename_session(session_id, new_name)
                    st.success("Chat renamed!")
                    st.rerun()
                else:
                    st.error("Enter a valid name")
            # Delete
            if st.button("Delete Chat", key=f"delete_btn_{session_id}"):
                delete_session(session_id)
                st.success("Chat deleted!")
                st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("➕ New Chat")
    new_name = st.sidebar.text_input("Enter chat name", key="new_chat_name")
    if st.sidebar.button("Create Chat"):
        if new_name.strip():
            session_id = create_session(user_id, new_name.strip())
            st.session_state.session_id = session_id
            st.session_state.current_chat = []
            st.session_state.uploaded_image = None
            st.rerun()
        else:
            st.sidebar.warning("Enter a valid name")

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        for key in ["logged_in", "username", "user_id", "session_id", "current_chat", "uploaded_image", "guest_messages"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.page = "login"
        st.success("Logged out successfully!")
        st.rerun()

    # -------------------------------
    # Image Upload
    # -------------------------------
    uploaded_file = st.file_uploader("📷 Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.session_state.uploaded_image = image
        image.thumbnail((600, 600))
        st.image(image, caption="Uploaded Image", width=300)
    elif st.session_state.uploaded_image:
        st.image(st.session_state.uploaded_image, caption="Uploaded Image", width=300)
    else:
        st.info("👆 Upload an image to start chat")

    # -------------------------------
    # Prompt Input
    # -------------------------------
    prompt = st.text_input("💬 Ask a question about this image:", key="prompt")

    if st.button("Send"):
        # Check guest limit
        if not st.session_state.logged_in and st.session_state.guest_messages >= FREE_LIMIT:
            st.warning(f"⚠️ Free trial ended ({FREE_LIMIT} messages). Please login to continue.")
        elif st.session_state.uploaded_image is None:
            st.warning("Upload an image first!")
        elif not prompt.strip():
            st.warning("Enter a question!")
        else:
            response = get_gemini_vision_response(st.session_state.uploaded_image, prompt)
            if response:
                st.session_state.current_chat.append({"question": prompt, "answer": response})
                if st.session_state.session_id:
                    save_message(st.session_state.session_id, "user", prompt)
                    save_message(st.session_state.session_id, "bot", response)
                if not st.session_state.logged_in:
                    st.session_state.guest_messages += 1

    # -------------------------------
    # Display Chat History
    # -------------------------------
    if st.session_state.current_chat:
        st.subheader("🧠 Chat History")
        for chat in reversed(st.session_state.current_chat):
            if chat["question"]:
                st.markdown(f"**🧍‍♀️ You:** {chat['question']}")
            if chat["answer"]:
                st.markdown(f"**🤖 Saanra:** {chat['answer']}")
            st.markdown("---")


# -------------------------------
# SESSION STATE INIT
# -------------------------------
if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------------------
# PAGE ROUTING
# -------------------------------
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "signup":
    signup_page()
else:
    chat_page()