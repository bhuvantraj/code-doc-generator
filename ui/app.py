"""
Streamlit UI for the Agentic Code Documentation Generator.

Displays: current state, state transition history, active agent,
agent messages, tool calls (I/O), metrics dashboard, run controls.
"""

import streamlit as st
import asyncio
import sys
import os

# Ensure project root is on the path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from main import run_pipeline  # noqa: E402
from agent_logging.logger import AgentLogger  # noqa: E402
from metrics.metrics import MetricsTracker  # noqa: E402

# ---- Page Config -----------------------------------------------------------

st.set_page_config(
    page_title="Code Doc Agent",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Custom CSS ------------------------------------------------------------

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .state-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
    }
    .state-START { background: #e2e8f0; color: #475569; }
    .state-READ_CODE { background: #dbeafe; color: #1d4ed8; }
    .state-PARSE_CODE { background: #fef3c7; color: #d97706; }
    .state-GENERATE_DOCUMENTATION { background: #ede9fe; color: #7c3aed; }
    .state-DISPLAY_RESULT { background: #d1fae5; color: #059669; }
    .state-END { background: #d1fae5; color: #047857; border: 2px solid #34d399; }
    .state-ERROR { /* no color */ }
    /* default badge style: white background, gray border */
    .state-badge { background: #ffffff; color: #000000; border: 1px solid #cbd5e1; }
    .state-active { background: #34d399 !important; color: #ffffff !important; }
        /* removed nav-bar and wrapper classes */
    .state-row { margin-top: 2rem; margin-bottom: 2.5rem; text-align: center; }
    /* panel styles */
    /* columns transparent with minimal horizontal padding */
    div[data-testid="stColumns"] > div {
        padding: 1rem 0;        /* removed side padding to close gap */
        background: transparent;
        border-radius: 0;
        box-shadow: none;
    }
    /* header typography */
    .main-header { font-size: 2.6rem; font-weight: 800; }
    .sub-header { font-size: 1.1rem; }
    /* button tweaks */
    .stButton > button { background: #667eea; color: #fff; border: none; }
    .stButton > button:hover { background: #5a67d8; }
    /* overall page container */
    .css-1d391kg { max-width: 250px; margin: auto; }
    body, .main { background: #f4f6f8; }
    .stTextArea textarea { font-family: monospace; background: #ffffff; border: 1px solid #a0aec0; color: #2d3748; }
    /* hide streamlit header (deploy/share button) */
    header {display: none !important;}


    .metric-card {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        color: #64748b;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.3rem;
    }

    .transition-arrow {
        color: #667eea;
        font-weight: 600;
    }

    .msg-box {
        background: #f0f9ff;
        border-left: 3px solid #38bdf8;
        border-radius: 0 8px 8px 0;
        padding: 0.5rem 1rem;
        margin-bottom: 0.3rem;
        font-size: 0.9rem;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ---- Session State Init ---------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []
if "tool_calls" not in st.session_state:
    st.session_state.tool_calls = []
if "state_transitions" not in st.session_state:
    st.session_state.state_transitions = []
if "current_state" not in st.session_state:
    st.session_state.current_state = "START"
if "result" not in st.session_state:
    st.session_state.result = None
if "running" not in st.session_state:
    st.session_state.running = False
if "metrics_tracker" not in st.session_state:
    st.session_state.metrics_tracker = MetricsTracker()
if "logger" not in st.session_state:
    st.session_state.logger = AgentLogger()

# ---- Callbacks for pipeline ------------------------------------------------


def on_state_change(prev, event, next_s):
    st.session_state.current_state = next_s
    st.session_state.state_transitions.append(
        {"from": prev, "event": event, "to": next_s}
    )


def on_tool_call(name, inp, out):
    st.session_state.tool_calls.append(
        {"tool": name, "input": inp, "output": out}
    )


def on_message(msg):
    st.session_state.messages.append(msg)


# ---- Header ---------------------------------------------------------------

# project title centered with margin
st.markdown('<div class="main-header" style="text-align:center; margin-bottom:2rem;">Code Documentation Agent</div>', unsafe_allow_html=True)

# second row: seed and language selectors
c1, c2 = st.columns([1,1])
with c1:
    seed = st.number_input("Seed", min_value=0, max_value=99999, value=42, step=1)
with c2:
    language = st.selectbox("Language", ["python", "javascript", "java"])

st.markdown("<div style='margin-bottom:25px;'></div>", unsafe_allow_html=True)





# state graph below header rows
current = st.session_state.current_state
states_list = [
    "START",
    "READ_CODE",
    "PARSE_CODE",
    "GENERATE_DOCUMENTATION",
    "DISPLAY_RESULT",
    "END",
]

sm_html = ""
for i, s in enumerate(states_list):
    active_cls = " state-active" if s == current else ""
    sm_html += f'<span class="state-badge state-{s}{active_cls}">{s}</span>'
    if i < len(states_list) - 1:
        sm_html += '<span class="transition-arrow">&nbsp;→&nbsp;</span>'
st.markdown(f'<div class="state-row">{sm_html}</div>', unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:35px;'></div>", unsafe_allow_html=True)

# ---- Main Area -------------------------------------------------------------

# two regions: left for code+buttons, right for results
# give code column a bit more space
code_col, results_col = st.columns([1,1])

with code_col:
    st.markdown("### Source Code Input")
    default_code = '''def add(a, b):
    """Adds two numbers together."""
    return a + b

class Calculator:
    """A simple calculator class."""

    def multiply(self, x, y):
        """Multiply two numbers."""
        return x * y

    def divide(self, x, y):
        """Divide x by y."""
        if y == 0:
            raise ValueError("Cannot divide by zero")
        return x / y
'''
    source_code = st.text_area("Paste your code here:", value=default_code, height=500, width=500)

    # start/reset buttons below code area
    btn1, btn2 = st.columns(2)
    with btn1:
        start_btn = st.button("Start", type="primary")
    with btn2:
        reset_btn = st.button("Reset")

# results will appear in results_col


# ---- Reset handler ---------------------------------------------------------

if reset_btn:
    st.session_state.messages = []
    st.session_state.tool_calls = []
    st.session_state.state_transitions = []
    st.session_state.current_state = "START"
    st.session_state.result = None
    st.session_state.running = False
    st.rerun()

# ---- Start handler ---------------------------------------------------------

if start_btn and not st.session_state.running:
    st.session_state.running = True
    st.session_state.messages = []
    st.session_state.tool_calls = []
    st.session_state.state_transitions = []
    st.session_state.current_state = "START"
    st.session_state.result = None

    with st.spinner("Running documentation pipeline..."):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                run_pipeline(
                    source_code=source_code,
                    language=language,
                    seed=seed,
                    logger=st.session_state.logger,
                    metrics=st.session_state.metrics_tracker,
                    on_state_change=on_state_change,
                    on_tool_call=on_tool_call,
                    on_message=on_message,
                )
            )
            loop.close()
            st.session_state.result = result
            st.session_state.current_state = (
                "END" if result["success"] else "ERROR"
            )
        except Exception as e:
            st.session_state.result = {
                "success": False,
                "error": str(e),
                "documentation": "",
            }
            st.session_state.current_state = "ERROR"
            st.session_state.messages.append(f"Pipeline error: {e}")
        finally:
            st.session_state.running = False

    st.rerun()

# ---- Results Display -------------------------------------------------------

with results_col:
    if st.session_state.result or st.session_state.messages:
        # Tabs for organized display
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "Documentation",
                "State Transitions",
                "Tool Calls",
                "Agent Messages",
                "Metrics",
            ]
        )

        # -- Tab 1: Documentation -------------------------------------------
        with tab1:
            if st.session_state.result and st.session_state.result.get("documentation"):
                st.markdown(st.session_state.result["documentation"])
            else:
                st.info("Run the pipeline to generate documentation.")

        # -- Tab 2: State Transitions ---------------------------------------
        with tab2:
            st.markdown("#### State Transition History")
            if st.session_state.state_transitions:
                for i, t in enumerate(st.session_state.state_transitions):
                    c1, c2, c3 = st.columns([2, 1, 2])
                    with c1:
                        st.markdown(
                            f'<span class="state-badge state-{t["from"]}">'
                            f'{t["from"]}</span>',
                            unsafe_allow_html=True,
                        )
                    with c2:
                        st.markdown(
                            f'<span class="transition-arrow">'
                            f'-- {t["event"]} --></span>',
                            unsafe_allow_html=True,
                        )
                    with c3:
                        st.markdown(
                            f'<span class="state-badge state-{t["to"]}">'
                            f'{t["to"]}</span>',
                            unsafe_allow_html=True,
                        )
                st.markdown("---")
                st.markdown(
                    f"**Total transitions:** {len(st.session_state.state_transitions)}"
                )
            else:
                st.info("No transitions yet. Start the pipeline.")

        # -- Tab 3: Tool Calls ----------------------------------------------
        with tab3:
            st.markdown("#### Tool Call Log")
            if st.session_state.tool_calls:
                for i, tc in enumerate(st.session_state.tool_calls):
                    with st.expander(f"Tool: {tc['tool']}", expanded=(i == 0)):
                        st.markdown("**Input:**")
                        st.json(tc["input"])
                        st.markdown("**Output:**")
                        st.json(tc["output"])
            else:
                st.info("No tool calls yet. Start the pipeline.")

        # -- Tab 4: Agent Messages ----------------------------------------------
        with tab4:
            st.markdown("#### Agent Activity Log")
            if st.session_state.messages:
                for msg in st.session_state.messages:
                    st.markdown(
                        f'<div class="msg-box">{msg}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No messages yet.")

        # -- Tab 5: Metrics Dashboard -------------------------------------------
        with tab5:
            st.markdown("#### Metrics Dashboard")

            summary = st.session_state.metrics_tracker.get_summary()

            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="metric-value">{summary["avg_generation_time"]:.2f}s</div>'
                    f'<div class="metric-label">Avg Generation Time</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with m2:
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="metric-value">{summary["total_tool_calls"]}</div>'
                    f'<div class="metric-label">Total Tool Calls</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with m3:
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="metric-value">{summary["success_rate"]:.0f}%</div>'
                    f'<div class="metric-label">Success Rate</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("")

            # Run history table
            run_history = st.session_state.metrics_tracker.get_run_history()
            if run_history:
                st.markdown("#### Run History")
                st.dataframe(
                    run_history,
                    column_config={
                        "run_id": "Run ID",
                        "generation_time": st.column_config.NumberColumn(
                            "Gen Time (s)", format="%.4f"
                        ),
                        "tool_call_count": "Tool Calls",
                        "success": st.column_config.CheckboxColumn("Success"),
                    },
                    use_container_width=True,
                )
    st.markdown('</div>', unsafe_allow_html=True)

# ---- Footer ----------------------------------------------------------------

st.markdown("---")
st.caption("Built with Pydantic AI | Groq LLM | Tree-sitter | Streamlit")
