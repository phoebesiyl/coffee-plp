# app.py — Coffee Learning Portal v3.4 (Progress & Sources Fixed)
import streamlit as st
from langchain_rag import qa_chain
from agents import agent_run
import time
import re

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Master Art of Coffee - Learning Portal",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# MODERN BLUE THEME STYLING
# ============================================
st.markdown("""
    <style>
    /* Main container */
    .main {
        background-color: #ffffff;
    }
    
    /* Header styling */
    .big-title {
        font-size: 42px;
        font-weight: 700;
        color: #1e3a8a;
        text-align: center;
        margin-bottom: 5px;
    }
    
    .subtitle {
        font-size: 16px;
        color: #64748b;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Answer box */
    .answer-box {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    
    .answer-box h3 {
        color: #1e3a8a;
        margin-top: 0;
    }
    
    /* Loading animation */
    .loading-container {
        text-align: center;
        padding: 40px;
        background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
        border-radius: 12px;
        margin: 20px 0;
        border: 2px solid #cbd5e1;
    }
    
    .spinner {
        border: 4px solid #e0e7ff;
        border-top: 4px solid #3b82f6;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    
    /* Brew Answer button (primary) */
.stButton > button[kind="primary"] {
    background-color: #3b82f6 !important;     /* Blue tone */
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.6em 1.2em !important;
    box-shadow: 0 3px 8px rgba(59,130,246,0.3);
    transition: background 0.3s ease, transform 0.1s ease;
}

.stButton > button[kind="primary"]:hover {
    background-color: #2563eb !important;     /* Slightly darker blue */
    transform: scale(1.02);
}

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        color: #1e3a8a;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #3b82f6 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    
    /* Sidebar buttons - BLACK TEXT */
    [data-testid="stSidebar"] .stButton > button {
        background-color: rgba(255, 255, 255, 0.1);
        color: black !important;
        border: 1px solid rgba(255, 255, 255, 0.3);
        font-weight: 500;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.5);
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border: 2px solid #cbd5e1;
        border-radius: 8px;
        padding: 12px;
        font-size: 16px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Citation styling */
    .citation-ref {
        color: #3b82f6;
        font-weight: 600;
        background-color: #eff6ff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if "completed_modules" not in st.session_state:
    st.session_state.completed_modules = {
        "Pillar 1: Coffee Sensory Evaluation & Flavor Science": [],
        "Pillar 2: Espresso Mastery & Milk-Based Drinks": [],
        "Pillar 3: Hand-Brewed Coffee Methods": []
    }

if "questions_asked" not in st.session_state:
    st.session_state.questions_asked = 0

if "expanded_pillars" not in st.session_state:
    st.session_state.expanded_pillars = set()

if "last_answer" not in st.session_state:
    st.session_state.last_answer = None

if "current_question" not in st.session_state:
    st.session_state.current_question = ""

# ============================================
# MODULE CONTENT
# ============================================
MODULES = {
    "Pillar 1: Coffee Sensory Evaluation & Flavor Science": {
        "icon": "👅",
        "short_name": "Sensory & Flavor",
        "questions": [
            "How are coffee flavors categorized across aroma, taste, and aftertaste?",
            "What is the role of the World Coffee Research Sensory Lexicon, and how are its intensity scales applied in practice?",
            "How can I describe coffee flavors precisely during a cupping session?",
            "How can I design a simple comparative tasting to train my palate in recognizing sweetness and acidity?",
            "How do different processing methods—washed, natural, and honey—shape a coffee’s sensory profile?"
        ]
    },
    "Pillar 2: Espresso Mastery & Milk-Based Drinks": {
        "icon": "☕️",
        "short_name": "Espresso & Milk",
        "questions": [
            "How do grind size and dose affect espresso extraction?",
            "What is the ideal espresso brewing temperature and pressure?",
            "How does milk steaming temperature influence foam quality?",
            "What are the key steps to dial in espresso properly?",
            "What are the differences between latte, cappuccino, and flat white textures?"
        ]
    },
    "Pillar 3: Hand-Brewed Coffee Methods": {
        "icon": "🫖",
        "short_name": "Hand Brewing",
        "questions": [
            "What is the optimal coffee-to-water ratio for V60 brewing?",
            "How does water temperature affect extraction in pour-over methods?",
            "What's the difference between immersion and percolation brewing?",
            "How does pouring technique influence agitation and flavor?",
            "How do various brewing methods highlight different coffee origins?"
        ]
    }
}

# ============================================
# HELPER FUNCTIONS
# ============================================
def calculate_progress():
    """Calculate overall learning progress"""
    total_questions = sum(len(MODULES[m]["questions"]) for m in MODULES)
    completed = sum(len(st.session_state.completed_modules[m]) for m in st.session_state.completed_modules)
    return completed / total_questions if total_questions > 0 else 0

def is_module_complete(module_name):
    """Check if a module is complete"""
    return len(st.session_state.completed_modules[module_name]) >= len(MODULES[module_name]["questions"])

def mark_question_complete(question):
    """
    Mark a question as complete in the appropriate module.
    FIXED: Now updates session state correctly (forces Streamlit to re-render).
    """
    question_normalized = question.strip().lower()
    updated = False

    for module_name, module_data in MODULES.items():
        for module_question in module_data["questions"]:
            if module_question.strip().lower() == question_normalized:
                if module_question not in st.session_state.completed_modules[module_name]:
                    # Create a shallow copy so Streamlit detects a state change
                    completed = st.session_state.completed_modules.copy()
                    completed[module_name] = completed[module_name] + [module_question]
                    st.session_state.completed_modules = completed
                    updated = True
                    return module_name
    return None

def count_citations(text):
    """
    Count [1], [2], [3] style citations in text.
    FIX #1: For multi-agent answers.
    """
    if not text:
        return 0
    # Find all [number] patterns
    citations = re.findall(r'\[(\d+)\]', text)
    # Return count of unique citations
    return len(set(citations))

def highlight_citations(text):
    """Highlight [1], [2] style citations in the text"""
    if not text:
        return text
    pattern = r'\[(\d+)\]'
    highlighted = re.sub(pattern, r'<span class="citation-ref">[\1]</span>', text)
    return highlighted

# ============================================
# SIDEBAR (WITH FIXED PROGRESS)
# ============================================
with st.sidebar:
    st.markdown("### ☕️ Coffee Learning")
    st.caption("AI-Powered Barista Training")
    
    st.divider()
    
    # Progress overview (FIXED - recalculates each time)
    st.markdown("### 📊 Progress")
    overall_progress = calculate_progress()
    st.progress(overall_progress)
    st.caption(f"{int(overall_progress * 100)}% Complete")
    
    st.markdown("")
    
    # Stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Questions", st.session_state.questions_asked)
    with col2:
        modules_done = sum(1 for m in MODULES if is_module_complete(m))
        st.metric("Pillars", f"{modules_done}/3")
    
    col1, col2 = st.columns(2)
    total_completed = sum(len(st.session_state.completed_modules[m]) for m in st.session_state.completed_modules)
    total_questions = sum(len(MODULES[m]["questions"]) for m in MODULES)
    
    with col1:
        st.metric("Answered", total_completed)
    with col2:
        st.metric("Total", total_questions)
    
    st.divider()
    
    # Actions
    st.markdown("### ⚙️ Actions")
    
    if st.button("🔄 Reset Progress", use_container_width=True, key="sidebar_reset"):
        st.session_state.show_reset_confirm = True
    
    if st.session_state.get("show_reset_confirm", False):
        st.warning("⚠️ Are you sure?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes", use_container_width=True, key="confirm_yes"):
                st.session_state.completed_modules = {m: [] for m in MODULES}
                st.session_state.questions_asked = 0
                st.session_state.expanded_pillars = set()
                st.session_state.last_answer = None
                st.session_state.current_question = ""
                st.session_state.show_reset_confirm = False
                st.rerun()
        with col2:
            if st.button("No", use_container_width=True, key="confirm_no"):
                st.session_state.show_reset_confirm = False
                st.rerun()
    
    st.divider()
    
    # About
    with st.expander("ℹ️ About", expanded=False):
        st.markdown("""
        **Coffee Learning Portal**
        
        Built with:
        - 🤖 LangChain RAG
        - 🧠 Multi-Agent AI
        - 📚 15+ Sources
        
        v3.4 - Progress Fixed
        """)

# ============================================
# MAIN CONTENT
# ============================================

# Header
st.markdown('<div class="big-title">Coffee Learning</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Want to become coffee-smart and barista-ready? Ask a question or explore a pillar.</div>', unsafe_allow_html=True)

st.markdown("")

# ============================================
# QUESTION INPUT
# ============================================
question = st.text_input(
    "Ask your coffee question here:",
    value=st.session_state.current_question,
    placeholder="e.g., Why does espresso taste sour?",
    label_visibility="collapsed"
)

if question != st.session_state.current_question:
    st.session_state.current_question = question

# Options
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    use_multi_agent = st.checkbox(
        "🧠 Multi-Agent Deep Research",
        help="""
        **3-Stage AI Process:**
        1. Researcher searches knowledge base
        2. Synthesizer combines findings
        3. Critic reviews and improves
        
        ⏱️ Takes 20-40 seconds (vs 5-15 sec standard)
        """,
        key="use_multi_agent"
    )

with col2:
    if use_multi_agent:
        st.caption("⚡ Advanced: ~20-40 sec")
    else:
        st.caption("⚡ Standard: ~5-15 sec")

with col3:
    brew_button = st.button(
        "☕️ Brew Answer", 
        type="primary", 
        use_container_width=True, 
        disabled=(not question),
        key="brew_btn"
    )

st.markdown("")

# ============================================
# PROCESS QUESTION
# ============================================
if brew_button and question:
    st.session_state.questions_asked += 1
    
    loading_placeholder = st.empty()
    
    with loading_placeholder.container():
        if use_multi_agent:
            st.markdown("""
            <div class="loading-container">
                <div class="spinner"></div>
                <h3 style="color: #1e3a8a; margin: 20px 0 10px 0;">🧠 Multi-Agent System Working...</h3>
                <p style="color: #64748b; margin: 5px 0;">
                    <strong>Stage 1:</strong> Researcher searching knowledge base<br>
                    <strong>Stage 2:</strong> Synthesizer combining information<br>
                    <strong>Stage 3:</strong> Critic reviewing answer quality
                </p>
                <p style="color: #94a3b8; font-size: 12px; margin-top: 10px;">Estimated: 20-40 seconds</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="loading-container">
                <div class="spinner"></div>
                <h3 style="color: #1e3a8a; margin: 20px 0 10px 0;">☕ Brewing Your Answer...</h3>
                <p style="color: #64748b;">Searching knowledge base and generating response</p>
                <p style="color: #94a3b8; font-size: 12px; margin-top: 10px;">Estimated: 5-15 seconds</p>
            </div>
            """, unsafe_allow_html=True)
    
    start_time = time.time()
    
    try:
        if use_multi_agent:
            answer_text = agent_run(question)
            result = {
                "result": answer_text,
                "source_documents": []  # Multi-agent doesn't return docs
            }
            mode = "Multi-Agent AI"
        else:
            result = qa_chain(question)
            mode = "Standard RAG"
        
        elapsed = time.time() - start_time
        loading_placeholder.empty()
        
        st.session_state.last_answer = {
            "question": question,
            "result": result,
            "elapsed": elapsed,
            "mode": mode,
            "timestamp": time.strftime("%H:%M:%S")
        }
        
        # IMPORTANT: Force rerun to update progress bars
        st.rerun()
        
    except Exception as e:
        loading_placeholder.empty()
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Check if Ollama/OpenAI is running and API keys are set")

# ============================================
# DISPLAY ANSWER (WITH FIXED SOURCE COUNT)
# ============================================
if st.session_state.last_answer:
    answer_data = st.session_state.last_answer
    answer_text = answer_data['result']['result']
    highlighted_answer = highlight_citations(answer_text)
    
    st.markdown(f"""
    <div class="answer-box">
        <h3>☕ Your Answer</h3>
        <p style="color: #64748b; font-size: 14px; margin-bottom: 16px;">
            <strong>Question:</strong> {answer_data['question']}<br>
            <strong>Time:</strong> {answer_data['timestamp']} | <strong>Mode:</strong> {answer_data['mode']}
        </p>
        <div style="color: #1e3a8a; line-height: 1.8; font-size: 16px;">
            {highlighted_answer}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Metadata (FIXED SOURCE COUNT)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⏱️ Time", f"{answer_data['elapsed']:.1f}s")
    
    with col2:
        st.metric("🔧 Mode", answer_data['mode'])
    
    with col3:
        # FIX #1: Show correct source/citation count
        if answer_data['mode'] == "Multi-Agent AI":
            citation_count = count_citations(answer_text)
            if citation_count > 0:
                st.metric("📄 Citations", citation_count)
            else:
                st.metric("📄 Citations", "Multiple")
        else:
            source_count = len(answer_data['result'].get("source_documents", []))
            st.metric("📄 Sources", source_count)
    
    with col4:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_answer_btn"):
            st.session_state.last_answer = None
            st.session_state.current_question = ""
            st.rerun()
    
    # Show sources (Standard RAG only)
    if answer_data['mode'] == "Standard RAG" and answer_data['result'].get("source_documents"):
        with st.expander("📚 View Sources", expanded=False):
            for i, doc in enumerate(answer_data['result']["source_documents"], 1):
                st.markdown(f"""
                **[{i}] {doc.metadata.get('title', 'Unknown Source')}**
                
                *Excerpt:* {doc.page_content[:300]}...
                """)
                if i < len(answer_data['result']["source_documents"]):
                    st.divider()
    elif answer_data['mode'] == "Multi-Agent AI":
        citation_count = count_citations(answer_text)
        st.info(f"""
        **ℹ️ Multi-Agent Mode:** Sources are analyzed internally by 3 AI agents. 
        {f"Found **{citation_count} citations** in the answer text above." if citation_count > 0 else "Citations appear as [1], [2], [3] in the answer."}
        """)
    
    # Track progress (FIX #2: Better tracking)
    completed_module = mark_question_complete(answer_data['question'])
    if completed_module:
        st.success(f"✅ Progress saved in {MODULES[completed_module]['short_name']}")
        
        if is_module_complete(completed_module):
            st.balloons()
            st.success(f"🎉 You completed **{MODULES[completed_module]['short_name']}**!")

st.markdown("---")

if not st.session_state.last_answer:
    st.info("💡 **Tip:** Select a pillar below and click **Ask** on any question to get started.")

st.markdown("")

# ============================================
# LEARNING PILLARS
# ============================================
st.markdown("### Choose a Pillar:")

for pillar_idx, (module_name, module_data) in enumerate(MODULES.items()):
    is_complete = is_module_complete(module_name)
    is_expanded = module_name in st.session_state.expanded_pillars
    completed_count = len(st.session_state.completed_modules[module_name])
    total_count = len(module_data["questions"])
    progress = completed_count / total_count
    
    with st.container():
        col1, col2, col3 = st.columns([8, 1, 1])
        
        with col1:
            st.markdown(f"### {module_data['icon']} {module_name}")
        
        with col2:
            toggle_label = "▼" if is_expanded else "▶"
            if st.button(toggle_label, key=f"toggle_{pillar_idx}", use_container_width=True):
                if is_expanded:
                    st.session_state.expanded_pillars.discard(module_name)
                else:
                    st.session_state.expanded_pillars.add(module_name)
                st.rerun()
        
        
        st.progress(progress)
        status_emoji = "✅" if is_complete else "📖"
        st.caption(f"{status_emoji} {completed_count}/{total_count} questions • {int(progress * 100)}%")
        
        if is_expanded:
            st.markdown("")
            
            for q_idx, q in enumerate(module_data["questions"]):
                is_answered = q in st.session_state.completed_modules[module_name]
                status_icon = "✅" if is_answered else "⭕"
                
                q_col1, q_col2 = st.columns([5, 1])
                
                with q_col1:
                    bg_color = "#dbeafe" if is_answered else "#f8fafc"
                    border_color = "#10b981" if is_answered else "#3b82f6"
                    st.markdown(f"""
                    <div style="
                        background-color: {bg_color};
                        border-left: 4px solid {border_color};
                        padding: 14px 16px;
                        border-radius: 8px;
                        margin: 8px 0;
                    ">
                        {status_icon} <strong>Q{q_idx + 1}:</strong> {q}
                    </div>
                    """, unsafe_allow_html=True)
                
                with q_col2:
                    if st.button("Ask", key=f"ask_{pillar_idx}_{q_idx}", use_container_width=True):
                        st.session_state.current_question = q
                        st.rerun()
            
            st.markdown("")
    
    st.markdown("")

# ============================================
# PROGRESS SUMMARY
# ============================================
st.markdown("---")
st.markdown("### 🎯 Your Learning Progress")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Overall", f"{int(calculate_progress() * 100)}%")

with col2:
    modules_complete = sum(1 for m in MODULES if is_module_complete(m))
    st.metric("Pillars Done", f"{modules_complete}/3")

with col3:
    st.metric("Questions Done", f"{total_completed}/{total_questions}")

with col4:
    st.metric("Total Asked", st.session_state.questions_asked)