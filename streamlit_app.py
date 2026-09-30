import streamlit as st
from chatbot import FAQChatbot

# Page Configuration
st.set_page_config(
    page_title="TechNest Support Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS matching the dark theme dashboard
st.markdown("""
<style>
    .main {
        background-color: #0a0e1a;
        color: #f8fafc;
    }
    .stApp {
        background-color: #0a0e1a;
    }
    .metric-card {
        background: rgba(22, 29, 49, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34d399;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .popular-btn {
        background: rgba(22, 29, 49, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px;
        color: #f8fafc;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

# Initialize chatbot in session state
if "chatbot" not in st.session_state:
    st.session_state.chatbot = FAQChatbot()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Navigation & Stats
with st.sidebar:
    st.markdown("### 🤖 TechNest")
    st.caption("Support Chatbot")
    
    st.markdown("---")
    threshold = st.slider(
        "Similarity Cutoff",
        min_value=0.10,
        max_value=0.80,
        value=0.32,
        step=0.02,
        help="Adjust cosine similarity sensitivity."
    )
    st.session_state.chatbot.matcher.similarity_threshold = threshold

    st.markdown("---")
    st.markdown("#### 📊 Knowledge Base Stats")
    faqs = st.session_state.chatbot.matcher.faqs
    categories = list(set(f.get("category", "General") for f in faqs))
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total FAQs", len(faqs), "↑ +12%")
    with col2:
        st.metric("Categories", len(categories), "Active")

    st.markdown("---")
    with st.expander("Explore FAQs by Topic"):
        selected_cat = st.selectbox("Category", ["All"] + sorted(categories))
        display_list = faqs if selected_cat == "All" else [f for f in faqs if f.get("category") == selected_cat]
        for f in display_list:
            st.markdown(f"**Q:** {f['question']}")
            st.caption(f"**A:** {f['answer']}")
            st.divider()

# Main Hero
st.markdown('<div class="hero-badge">🤖 Powered by NLP (Tokenization • Lemmatization • Cosine Similarity)</div>', unsafe_allow_html=True)
st.markdown("# Hi there! 👋\n### I'm your **TechNest** Support Chatbot")
st.markdown("Get instant answers to your questions about orders, returns, refunds, shipping, payments, warranties and more. Type your question below or try one of the examples.")

st.markdown("---")
st.markdown("#### 💡 Popular Questions")
p_col1, p_col2, p_col3, p_col4 = st.columns(4)

with p_col1:
    if st.button("🛒 How can I track my order?", use_container_width=True):
        st.session_state.active_query = "How can I track my order?"
with p_col2:
    if st.button("🔄 What is your return policy?", use_container_width=True):
        st.session_state.active_query = "What is your return policy?"
with p_col3:
    if st.button("💳 Do you accept PayPal or Apple Pay?", use_container_width=True):
        st.session_state.active_query = "What payment methods do you accept?"
with p_col4:
    if st.button("🛡️ How do I file a warranty claim?", use_container_width=True):
        st.session_state.active_query = "How do I file a warranty claim for a defective item?"

# Render Chat Stream
if st.session_state.messages:
    st.markdown("---")
    st.markdown("#### 💬 Conversation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("suggestions"):
                st.caption("💡 Related questions you can ask:")
                for s in msg["suggestions"][:3]:
                    st.markdown(f"- *{s}*")

# Handle User Input
prompt = st.chat_input("Ask a question about your order, return, shipping, etc...")
if "active_query" in st.session_state and st.session_state.active_query:
    prompt = st.session_state.active_query
    st.session_state.active_query = None

if prompt:
    # Append user question
    st.session_state.messages.append({"role": "user", "content": prompt, "suggestions": []})
    
    # Get clean bot response (NO vector analysis or debug code shown!)
    res = st.session_state.chatbot.get_response(prompt)
    answer = res["answer"]
    suggestions = res.get("suggestions", [])
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "suggestions": suggestions
    })
    
    st.rerun()
