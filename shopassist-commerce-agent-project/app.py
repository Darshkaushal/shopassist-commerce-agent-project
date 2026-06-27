"""Polished Streamlit interface for ShopAssist Commerce.

The backend still keeps the required public function in
shopassist_agent.agent: run_agent(question: str) -> str.
"""

from __future__ import annotations

import json
import os
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any, Dict

import requests
import streamlit as st

from shopassist_agent.agent import run_agent_detailed
from shopassist_agent.data import ORDERS, PRODUCTS, ORDER_STATUSES, STATUS_PROGRESS as STORE_STATUS_PROGRESS
from shopassist_agent.logger import read_recent_logs
from shopassist_agent.schemas import AgentResult, ToolCall

st.set_page_config(
    page_title="ShopAssist Commerce | Support Desk",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


API_BASE_URL = os.getenv("SHOPASSIST_API_URL", "").strip().rstrip("/")
API_TIMEOUT = (4, 24)  # connect timeout, read timeout; Render cold starts can be slow.



def _result_from_api(data: Dict[str, Any]) -> AgentResult:
    """Convert FastAPI JSON into the same object shape used by the direct Python mode."""
    calls = [
        ToolCall(
            name=call.get("name", "unknown"),
            input=call.get("input", {}),
            status=call.get("status", "unknown"),
            output_summary=call.get("output_summary", ""),
            timestamp=call.get("timestamp", ""),
        )
        for call in data.get("tool_calls", [])
    ]
    return AgentResult(
        answer=data.get("answer", "No answer returned."),
        intent=data.get("intent", "unknown"),
        confidence=float(data.get("confidence", 0.0)),
        entities=data.get("entities", {}),
        tool_calls=calls,
        safety_notes=data.get("safety_notes"),
    )


def _set_backend_status(state: str, detail: str = "") -> None:
    """Store connection state without printing large warning boxes on mobile screens."""
    st.session_state.backend_state = state
    st.session_state.backend_detail = detail


def get_support_result(question: str) -> AgentResult:
    """Use the FastAPI backend when configured, with a clean local fallback."""
    if API_BASE_URL:
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/agent/ask",
                json={"question": question},
                timeout=API_TIMEOUT,
            )
            response.raise_for_status()
            _set_backend_status("connected", "Live backend response")
            return _result_from_api(response.json())
        except Exception as exc:  # noqa: BLE001 - UI fallback should never crash demo.
            _set_backend_status("fallback", f"Backend is waking or temporarily slow. Local mode used safely. {exc}")
    return run_agent_detailed(question)


@st.cache_data(ttl=25, show_spinner=False)
def _fetch_orders_from_api(api_url: str) -> list[dict]:
    response = requests.get(f"{api_url}/api/orders", timeout=API_TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_orders_data() -> list[dict]:
    """Read orders from FastAPI when available; fall back silently for a clean demo."""
    if API_BASE_URL:
        try:
            orders = _fetch_orders_from_api(API_BASE_URL)
            _set_backend_status("connected", "Orders synced from backend")
            return orders
        except Exception as exc:  # noqa: BLE001 - app remains usable even during Render cold starts.
            _set_backend_status("fallback", f"Showing safe local preview while backend wakes. {exc}")
    else:
        _set_backend_status("local", "No SHOPASSIST_API_URL configured")
    return list(ORDERS.values())


def backend_status_chip() -> str:
    state = st.session_state.get("backend_state", "local")
    detail = st.session_state.get("backend_detail", "")
    if state == "connected":
        return f"<span class='tool-badge'>● Live backend</span><span class='neutral-badge'>{safe(API_BASE_URL)}</span>"
    if state == "fallback":
        return "<span class='warning-badge'>● Local preview active</span><span class='neutral-badge'>Backend may be waking on Render</span>"
    return "<span class='neutral-badge'>● Local mode</span>"



CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@500;600;700;800&display=swap');

:root {
    --bg: #070812;
    --panel: rgba(14, 20, 37, 0.76);
    --panel-strong: rgba(15, 23, 42, 0.92);
    --line: rgba(255, 255, 255, 0.12);
    --line-strong: rgba(255, 255, 255, 0.20);
    --text: #f8fafc;
    --muted: #9ca3af;
    --soft: #cbd5e1;
    --brand: #7c3aed;
    --brand-2: #06b6d4;
    --success: #22c55e;
    --warning: #f59e0b;
    --danger: #ef4444;
}

html, body, [class*="css"] {
    font-family: 'Manrope', Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

h1, h2, h3, .brand-title, .hero-title, .metric-value, .section-heading {
    font-family: 'Sora', 'Manrope', sans-serif;
}

.stApp {
    color: var(--text);
    background:
        radial-gradient(circle at 10% 8%, rgba(124, 58, 237, 0.34), transparent 28%),
        radial-gradient(circle at 88% 4%, rgba(6, 182, 212, 0.26), transparent 25%),
        radial-gradient(circle at 45% 90%, rgba(245, 158, 11, 0.11), transparent 28%),
        linear-gradient(140deg, #050711 0%, #0c1020 45%, #0f172a 100%);
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px);
    background-size: 44px 44px;
    mask-image: linear-gradient(to bottom, rgba(0,0,0,0.85), rgba(0,0,0,0.20));
    z-index: 0;
}

[data-testid="stAppViewContainer"], [data-testid="stSidebar"], .main, .block-container {
    position: relative;
    z-index: 1;
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 1.15rem;
    padding-bottom: 2rem;
    max-width: 1420px;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(8, 13, 29, 0.98), rgba(15, 23, 42, 0.94)),
        radial-gradient(circle at top, rgba(124, 58, 237, 0.22), transparent 36%);
    border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.10);
    color: #f8fafc;
    text-align: left;
    justify-content: flex-start;
    min-height: 45px;
    box-shadow: none;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(124, 58, 237, 0.26);
    border-color: rgba(167, 139, 250, 0.45);
}

.sidebar-brand {
    padding: 16px 14px 10px 14px;
    border-radius: 24px;
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.20), rgba(6, 182, 212, 0.12));
    border: 1px solid var(--line);
    margin-bottom: 12px;
}

.logo-row { display: flex; align-items: center; gap: 12px; }
.logo-mark {
    width: 44px; height: 44px; border-radius: 16px;
    display: grid; place-items: center;
    background: linear-gradient(135deg, #8b5cf6, #06b6d4);
    box-shadow: 0 16px 34px rgba(124, 58, 237, 0.28);
    font-size: 22px;
}
.brand-title { font-size: 18px; font-weight: 800; letter-spacing: -0.02em; }
.brand-subtitle { color: var(--muted); font-size: 12px; margin-top: 2px; }

.hero {
    position: relative;
    overflow: hidden;
    padding: 34px 36px;
    border-radius: 34px;
    background:
        linear-gradient(135deg, rgba(124, 58, 237, 0.24), rgba(6, 182, 212, 0.14)),
        rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(255,255,255,0.16);
    box-shadow: 0 30px 90px rgba(0,0,0,0.36);
    backdrop-filter: blur(22px);
    margin-bottom: 22px;
}

.hero::after {
    content: "";
    position: absolute;
    width: 300px; height: 300px;
    right: -110px; top: -115px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255,255,255,0.18), rgba(124,58,237,0.08), transparent 68%);
}

.hero-grid { display: grid; grid-template-columns: 1.45fr 0.55fr; gap: 26px; align-items: center; }
.eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(34, 197, 94, 0.11);
    border: 1px solid rgba(34, 197, 94, 0.28);
    color: #bbf7d0;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 16px;
}

.hero-title {
    margin: 0;
    font-size: clamp(36px, 5vw, 64px);
    letter-spacing: -0.065em;
    line-height: 0.98;
    color: #ffffff;
}

.hero-title span {
    background: linear-gradient(135deg, #ffffff 10%, #c4b5fd 48%, #67e8f9 85%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.hero-copy {
    color: var(--soft);
    font-size: 16px;
    max-width: 900px;
    margin: 16px 0 0 0;
    line-height: 1.75;
}

.demo-card {
    position: relative;
    padding: 18px;
    border-radius: 26px;
    border: 1px solid rgba(255,255,255,0.14);
    background: rgba(3, 7, 18, 0.35);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
}
.demo-card-top { display: flex; justify-content: space-between; align-items: center; color: var(--muted); font-size: 12px; }
.pulse-dot { width: 9px; height: 9px; border-radius: 999px; background: #22c55e; box-shadow: 0 0 0 6px rgba(34,197,94,0.12); }
.mini-chat { margin-top: 16px; display: grid; gap: 12px; }
.mini-bubble {
    padding: 12px 14px;
    border-radius: 18px;
    color: #e5e7eb;
    font-size: 13px;
    line-height: 1.45;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.10);
}
.mini-bubble.agent { background: linear-gradient(135deg, rgba(124, 58, 237, 0.28), rgba(6, 182, 212, 0.16)); }

.pill-row { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
.pill {
    padding: 9px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.12);
    color: #e2e8f0;
    font-size: 12px;
    font-weight: 800;
}

.metric-card, .glass-card, .trace-card, .product-card, .order-card, .workflow-card, .prompt-card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 26px;
    box-shadow: 0 22px 70px rgba(0,0,0,0.26);
    backdrop-filter: blur(18px);
}

.metric-card {
    padding: 18px;
    min-height: 118px;
    position: relative;
    overflow: hidden;
}
.metric-card::after {
    content: "";
    position: absolute;
    right: -40px; bottom: -52px;
    width: 130px; height: 130px;
    border-radius: 999px;
    background: rgba(124, 58, 237, 0.10);
}
.metric-icon { font-size: 22px; margin-bottom: 10px; }
.metric-label {
    color: var(--muted);
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.10em;
}
.metric-value { color: white; font-size: 31px; font-weight: 800; margin-top: 5px; letter-spacing: -0.04em; }
.metric-foot { color: #a5b4fc; font-size: 12px; margin-top: 4px; font-weight: 700; }

.section-heading { font-size: 24px; font-weight: 800; letter-spacing: -0.04em; margin: 12px 0 8px 0; }
.section-subtitle { color: var(--muted); margin-top: -4px; margin-bottom: 16px; }

.workflow-card { padding: 18px; min-height: 150px; }
.workflow-step {
    width: 36px; height: 36px; border-radius: 14px;
    display: grid; place-items: center;
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.90), rgba(6, 182, 212, 0.82));
    color: white; font-weight: 900;
    margin-bottom: 14px;
}
.workflow-title { font-weight: 900; color: white; font-size: 15px; margin-bottom: 8px; }
.workflow-copy { color: var(--muted); font-size: 13px; line-height: 1.55; }

.chat-shell {
    border: 1px solid var(--line);
    background: rgba(15, 23, 42, 0.64);
    border-radius: 30px;
    padding: 20px;
    box-shadow: 0 24px 80px rgba(0,0,0,0.28);
}

.user-bubble, .chat-answer {
    border-radius: 22px;
    padding: 16px 18px;
    line-height: 1.7;
    white-space: pre-wrap;
}
.user-bubble {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    color: #e5e7eb;
    margin-bottom: 12px;
}
.chat-answer {
    background: linear-gradient(135deg, rgba(88, 28, 135, 0.45), rgba(14, 116, 144, 0.30));
    border: 1px solid rgba(191,219,254,0.22);
    color: #f8fafc;
    box-shadow: 0 18px 60px rgba(6, 182, 212, 0.08);
}

.prompt-card {
    padding: 14px 15px;
    color: #e2e8f0;
    font-size: 13px;
    min-height: 83px;
}

.tool-badge, .warning-badge, .danger-badge, .neutral-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 10px;
    margin: 4px 6px 4px 0;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 900;
}
.tool-badge { background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.30); color: #bbf7d0; }
.warning-badge { background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.30); color: #fde68a; }
.danger-badge { background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.30); color: #fecaca; }
.neutral-badge { background: rgba(148,163,184,0.12); border: 1px solid rgba(148,163,184,0.25); color: #cbd5e1; }

.product-card, .order-card, .trace-card, .glass-card { padding: 18px; }
.product-card { min-height: 270px; transition: 180ms ease; position: relative; overflow: hidden; }
.product-card:hover, .order-card:hover, .trace-card:hover { transform: translateY(-2px); border-color: var(--line-strong); }
.product-hero { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.product-icon {
    width: 48px; height: 48px; border-radius: 18px;
    display: grid; place-items: center;
    background: linear-gradient(135deg, rgba(124,58,237,0.44), rgba(6,182,212,0.28));
    border: 1px solid rgba(255,255,255,0.12);
    font-size: 24px;
}
.product-name, .order-title, .trace-title {
    color: #ffffff;
    font-weight: 900;
    font-size: 16px;
    line-height: 1.35;
}
.product-meta, .muted { color: var(--muted); font-size: 13px; }
.price-row { display: flex; align-items: end; justify-content: space-between; margin: 13px 0; }
.price { font-family: 'Sora'; font-size: 27px; font-weight: 900; letter-spacing: -0.04em; color: white; }
.rating { color: #fde68a; font-weight: 900; font-size: 13px; }
.desc { color: #cbd5e1; font-size: 13px; line-height: 1.55; margin-top: 12px; }

.progress-track {
    height: 8px; border-radius: 999px;
    background: rgba(255,255,255,0.08);
    overflow: hidden;
    margin: 13px 0 10px 0;
}
.progress-fill {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #7c3aed, #06b6d4, #22c55e);
}

.trace-card { margin-bottom: 14px; }
.trace-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.trace-number {
    width: 34px; height: 34px; border-radius: 13px;
    display: grid; place-items: center;
    background: rgba(124, 58, 237, 0.28);
    color: #ddd6fe; font-weight: 900;
}
.trace-code {
    margin-top: 12px;
    padding: 12px;
    border-radius: 16px;
    background: rgba(2, 6, 23, 0.48);
    border: 1px solid rgba(255,255,255,0.08);
    color: #cbd5e1;
    font-size: 12px;
    overflow-wrap: anywhere;
}

.stTabs [data-baseweb="tab-list"] { gap: 10px; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.07);
    border-radius: 999px;
    padding: 11px 18px;
    border: 1px solid rgba(255,255,255,0.09);
    color: #e2e8f0;
    font-weight: 800;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.56), rgba(6, 182, 212, 0.34)) !important;
    color: white !important;
    border-color: rgba(255,255,255,0.22) !important;
}

.stButton > button, .stFormSubmitButton > button {
    width: 100%;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.16);
    background: linear-gradient(135deg, #7c3aed, #0891b2);
    color: white;
    font-weight: 900;
    padding: 0.72rem 1rem;
    box-shadow: 0 16px 36px rgba(124, 58, 237, 0.25);
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: rgba(255,255,255,0.32);
    transform: translateY(-1px);
    box-shadow: 0 20px 42px rgba(6, 182, 212, 0.18);
}

[data-testid="stTextInput"] input {
    border-radius: 18px;
    border: 1px solid rgba(148,163,184,0.22);
    background: rgba(2, 6, 23, 0.62);
    color: white;
    min-height: 54px;
    font-size: 15px;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: rgba(2, 6, 23, 0.62);
    border-radius: 16px;
    border-color: rgba(148,163,184,0.22);
}
[data-testid="stDataFrame"] { border-radius: 18px; overflow: hidden; }
code { color: #bfdbfe !important; }
hr { border-color: rgba(148,163,184,0.18) !important; }


.status-timeline {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 10px;
    margin: 16px 0 12px 0;
}
.status-step {
    padding: 10px 8px;
    border-radius: 16px;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.10);
    color: #94a3b8;
    font-size: 11px;
    font-weight: 900;
    text-align: center;
}
.status-step.active {
    color: #ffffff;
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.54), rgba(6, 182, 212, 0.30));
    border-color: rgba(255,255,255,0.22);
    box-shadow: 0 12px 32px rgba(6, 182, 212, 0.12);
}
.ops-panel {
    padding: 20px;
    border-radius: 28px;
    background: linear-gradient(135deg, rgba(15,23,42,0.84), rgba(30,41,59,0.62));
    border: 1px solid rgba(255,255,255,0.14);
    box-shadow: 0 24px 80px rgba(0,0,0,0.24);
    margin-bottom: 18px;
}
.ops-title { color: white; font-family: 'Sora'; font-weight: 900; font-size: 20px; letter-spacing: -0.04em; }
.ops-copy { color: var(--muted); font-size: 13px; line-height: 1.6; margin: 6px 0 14px 0; }
.fulfillment-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 12px; }
.fulfillment-item {
    padding: 14px;
    border-radius: 18px;
    background: rgba(2,6,23,0.36);
    border: 1px solid rgba(255,255,255,0.08);
}
.fulfillment-label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 900; }
.fulfillment-value { color: white; font-weight: 900; margin-top: 4px; }


/* Production polish + mobile safety */
* { box-sizing: border-box; }
html, body { overflow-x: hidden; }
img, svg, video, canvas { max-width: 100%; height: auto; }
.element-container { overflow-wrap: anywhere; }
[data-testid="stVerticalBlock"] { gap: 0.75rem; }
[data-testid="stSidebar"] * { overflow-wrap: anywhere; }
[data-testid="stForm"] { border: 0; background: transparent; }
.stAlert { border-radius: 18px; }

.mobile-quick-actions { display: none; }
.mobile-status-card { display: none; }
.status-mini-card {
    padding: 12px 14px;
    border-radius: 18px;
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(255,255,255,0.12);
    color: #cbd5e1;
    font-size: 12px;
    line-height: 1.45;
}

@media (max-width: 980px) {
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; }
    .block-container {
        padding: 0.75rem 0.85rem 1.5rem 0.85rem !important;
        max-width: 100% !important;
    }
    .stApp {
        background:
            radial-gradient(circle at 35% 0%, rgba(124,58,237,0.24), transparent 34%),
            radial-gradient(circle at 100% 30%, rgba(6,182,212,0.18), transparent 36%),
            linear-gradient(150deg, #060816 0%, #0b1120 60%, #08111f 100%) !important;
    }
    .stApp::before { background-size: 32px 32px; opacity: .65; }
    .hero {
        padding: 20px 18px !important;
        border-radius: 24px !important;
        margin: 0.35rem 0 1rem 0 !important;
        box-shadow: 0 18px 48px rgba(0,0,0,0.32) !important;
    }
    .hero::after { width: 190px; height: 190px; right: -90px; top: -85px; }
    .hero-grid { grid-template-columns: 1fr !important; gap: 12px !important; }
    .hero-title {
        font-size: clamp(30px, 12vw, 42px) !important;
        line-height: 1.06 !important;
        letter-spacing: -0.052em !important;
    }
    .hero-copy { font-size: 14px !important; line-height: 1.62 !important; margin-top: 13px !important; }
    .eyebrow { font-size: 10px !important; padding: 7px 10px !important; margin-bottom: 12px !important; }
    .demo-card { display: none !important; }
    .pill-row { display: grid !important; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px !important; margin-top: 16px !important; }
    .pill { font-size: 11px !important; text-align: center; padding: 9px 8px !important; }
    .mobile-quick-actions { display: block !important; margin: 0 0 1rem 0; }
    .mobile-status-card { display: block !important; margin: 0 0 1rem 0; }
    .metric-card, .workflow-card, .glass-card, .trace-card, .product-card, .order-card, .chat-shell, .ops-panel, .prompt-card {
        border-radius: 20px !important;
        padding: 15px !important;
        min-height: auto !important;
        box-shadow: 0 14px 38px rgba(0,0,0,0.24) !important;
    }
    .metric-value { font-size: 24px !important; }
    .metric-label { font-size: 10px !important; }
    .section-heading { font-size: 21px !important; margin-top: 0.4rem !important; }
    .section-subtitle { font-size: 13px !important; line-height: 1.55 !important; }
    .workflow-step { width: 32px !important; height: 32px !important; border-radius: 12px !important; }
    .chat-shell { padding: 14px !important; }
    .user-bubble, .chat-answer { border-radius: 18px !important; padding: 14px !important; font-size: 14px !important; line-height: 1.65 !important; }
    .product-hero, .trace-head { gap: 10px !important; }
    .product-name, .order-title, .trace-title { font-size: 15px !important; }
    .price { font-size: 23px !important; }
    .price-row { align-items: flex-start !important; gap: 8px !important; flex-direction: column !important; }
    .status-timeline { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 7px !important; }
    .status-step { font-size: 10px !important; padding: 8px 6px !important; border-radius: 13px !important; }
    .tool-badge, .warning-badge, .danger-badge, .neutral-badge { font-size: 10.5px !important; padding: 6px 8px !important; margin: 3px 4px 3px 0 !important; }
    .trace-code { font-size: 11px !important; max-width: 100% !important; overflow-x: auto; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px !important; overflow-x: auto !important; flex-wrap: nowrap !important; }
    .stTabs [data-baseweb="tab"] { padding: 9px 11px !important; font-size: 12px !important; white-space: nowrap !important; }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-baseweb="select"] > div {
        min-height: 48px !important;
        font-size: 14px !important;
    }
    .stButton > button, .stFormSubmitButton > button { min-height: 44px !important; border-radius: 14px !important; font-size: 13px !important; }
    .mobile-hide { display: none !important; }
}

@media (max-width: 520px) {
    .pill-row { grid-template-columns: 1fr 1fr !important; }
    .hero-title { font-size: clamp(30px, 13vw, 38px) !important; }
    .hero-copy { font-size: 13.5px !important; }
    .product-icon { width: 40px !important; height: 40px !important; border-radius: 15px !important; font-size: 20px !important; }
    .status-timeline { grid-template-columns: 1fr 1fr !important; }
}

@media (max-width: 900px) {
    .hero-grid { grid-template-columns: 1fr; }
    .hero { padding: 26px 22px; }
    .hero-title { font-size: 38px; }
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

SAMPLE_PROMPTS = [
    "Where is order ORD-1002?",
    "Is there a cheaper alternative to the shoes I ordered in ORD-1002?",
    "Show me shoes under 2000",
    "Tell me about product P-4001",
    "Is order ORD-1003 dispatched?",
    "Where is order ORD-9999?",
]

CATEGORY_ICONS = {
    "shoes": "👟",
    "hoodie": "🧥",
    "bag": "🎒",
    "headphones": "🎧",
    "earbuds": "🎵",
    "watch": "⌚",
}

STATUS_PROGRESS = STORE_STATUS_PROGRESS


def safe(value: object) -> str:
    """Escape text before placing it inside custom HTML."""
    return escape(str(value))


def rupee(value: int | float) -> str:
    return f"₹{int(value):,}"


def stock_badge(product: dict) -> str:
    if product["stock"] <= 0:
        return "<span class='warning-badge'>Out of stock</span>"
    if product["stock"] <= 8:
        return f"<span class='warning-badge'>Only {product['stock']} left</span>"
    return f"<span class='tool-badge'>In stock: {product['stock']}</span>"


def category_icon(category: str) -> str:
    return CATEGORY_ICONS.get(category, "🛍️")


def product_card(product: dict) -> str:
    is_value_pick = product["price"] <= 2000 and product["stock"] > 0
    value_badge = "<span class='tool-badge'>Best value</span>" if is_value_pick else "<span class='neutral-badge'>Catalogue item</span>"
    return f"""
    <div class="product-card">
        <div class="product-hero">
            <div>
                <div class="product-name">{safe(product['name'])}</div>
                <div class="product-meta">{safe(product['product_id'])} • {safe(product['brand'])} • {safe(product['category']).title()}</div>
            </div>
            <div class="product-icon">{category_icon(product['category'])}</div>
        </div>
        <div class="price-row">
            <div class="price">{rupee(product['price'])}</div>
            <div class="rating">⭐ {safe(product['rating'])}/5</div>
        </div>
        {stock_badge(product)} {value_badge}
        <div class="desc">{safe(product['description'])}</div>
    </div>
    """


def order_card(order: dict) -> str:
    progress = STATUS_PROGRESS.get(order["status"], 25)
    status_class = "danger-badge" if order["status"] == "Cancelled" else ("warning-badge" if order["status"] in {"Processing", "Dispatched"} else "tool-badge")
    items = []
    for item in order["items"]:
        product = PRODUCTS.get(item["product_id"], {"name": item["product_id"]})
        items.append(f"{product['name']} × {item['quantity']}")
    tracking = order.get("tracking_id") or "Not generated yet"
    carrier = order.get("carrier") or "Warehouse"
    active_index = ORDER_STATUSES.index(order["status"]) if order["status"] in ORDER_STATUSES else 0
    timeline = "".join(
        f"<div class='status-step {'active' if idx <= active_index and order['status'] != 'Cancelled' else ''}'>{safe(status)}</div>"
        for idx, status in enumerate(ORDER_STATUSES[:-1])
    )
    if order["status"] == "Cancelled":
        timeline = "<div class='status-step active' style='grid-column: 1 / -1;'>Cancelled</div>"
    return f"""
    <div class="order-card">
        <div class="product-hero">
            <div>
                <div class="order-title">{safe(order['order_id'])}</div>
                <div class="product-meta">{safe(order['customer_name'])} • Placed {safe(order['placed_on'])}</div>
            </div>
            <span class="{status_class}">{safe(order['status'])}</span>
        </div>
        <div class="progress-track"><div class="progress-fill" style="width:{progress}%"></div></div>
        <div class="status-timeline">{timeline}</div>
        <div class="price-row">
            <div class="price" style="font-size:24px;">{rupee(order['order_total'])}</div>
            <div class="rating">{safe(order['eta'])}</div>
        </div>
        <div class="muted"><strong>Items:</strong> {safe(', '.join(items))}</div>
        <div class="muted" style="margin-top:8px;"><strong>Tracking:</strong> {safe(tracking)} • {safe(carrier)}</div>
        <div class="desc">{safe(order['last_update'])}</div>
    </div>
    """


def metric_card(icon: str, label: str, value: str, foot: str) -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-label">{safe(label)}</div>
        <div class="metric-value">{safe(value)}</div>
        <div class="metric-foot">{safe(foot)}</div>
    </div>
    """


def workflow_card(step: int, title: str, copy: str) -> str:
    return f"""
    <div class="workflow-card">
        <div class="workflow-step">{step}</div>
        <div class="workflow-title">{safe(title)}</div>
        <div class="workflow-copy">{safe(copy)}</div>
    </div>
    """


def trace_card(index: int, call) -> str:
    status_class = "tool-badge" if call.status == "success" else "warning-badge"
    input_json = json.dumps(call.input, ensure_ascii=False)
    return f"""
    <div class="trace-card">
        <div class="trace-head">
            <div style="display:flex; gap:12px; align-items:flex-start;">
                <div class="trace-number">{index}</div>
                <div>
                    <div class="trace-title">{safe(call.name)}</div>
                    <div class="muted">Executed at {safe(call.timestamp)}</div>
                </div>
            </div>
            <span class="{status_class}">{safe(call.status)}</span>
        </div>
        <div class="trace-code"><strong>Input</strong>: <code>{safe(input_json)}</code><br><strong>Output</strong>: {safe(call.output_summary)}</div>
    </div>
    """


if "selected_prompt" not in st.session_state:
    st.session_state.selected_prompt = SAMPLE_PROMPTS[0]
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_question" not in st.session_state:
    st.session_state.last_question = SAMPLE_PROMPTS[0]
products = list(PRODUCTS.values())
orders = get_orders_data()
in_stock = sum(1 for product in products if product["stock"] > 0)
avg_rating = mean(product["rating"] for product in products)
inventory_units = sum(product["stock"] for product in products)
budget_count = sum(1 for product in products if product["price"] <= 2000 and product["stock"] > 0)

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="logo-row">
                <div class="logo-mark">S</div>
                <div>
                    <div class="brand-title">ShopAssist Commerce</div>
                    <div class="brand-subtitle">Smart order support</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Modern commerce support workspace")
    st.markdown("---")
    st.markdown("#### Try customer messages")
    for prompt in SAMPLE_PROMPTS:
        if st.button(prompt, key=f"sample_{prompt}"):
            st.session_state.selected_prompt = prompt
            st.session_state.last_question = prompt
    st.markdown("---")
    st.markdown("#### Service highlights")
    st.markdown("<span class='tool-badge'>Order tracking</span>", unsafe_allow_html=True)
    st.markdown("<span class='tool-badge'>Product discovery</span>", unsafe_allow_html=True)
    st.markdown("<span class='tool-badge'>Budget alternatives</span>", unsafe_allow_html=True)
    st.markdown("<span class='tool-badge'>Audit history</span>", unsafe_allow_html=True)
    st.markdown("<span class='tool-badge'>Read-only order view</span>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### Backend")
    if API_BASE_URL:
        st.success(f"API mode: {API_BASE_URL}")
    else:
        st.info("Local mode. Set SHOPASSIST_API_URL to use FastAPI.")
    st.markdown("---")
    st.caption("Designed for fast, polished customer conversations.")

# Compact connection chip for phones. This replaces large yellow warning boxes.
st.markdown(f"<div class='mobile-status-card status-mini-card'>{backend_status_chip()}</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
        <div class="hero-grid">
            <div>
                <div class="eyebrow"><span class="pulse-dot"></span> Commerce support workspace</div>
                <h1 class="hero-title">Resolve orders and product questions <span>in seconds.</span></h1>
                <p class="hero-copy">
                    Track orders, answer product questions, compare similar items, and guide shoppers to available options with clear support replies.
                </p>
                <div class="pill-row">
                    <span class="pill">Order tracking</span>
                    <span class="pill">Product discovery</span>
                    <span class="pill">Budget alternatives</span>
                    <span class="pill">Inventory aware</span>
                    <span class="pill">Clear replies</span>
                </div>
            </div>
            <div class="demo-card">
                <div class="demo-card-top"><span>Customer Desk</span><span class="pulse-dot"></span></div>
                <div class="mini-chat">
                    <div class="mini-bubble">Customer: Where is order ORD-1002?</div>
                    <div class="mini-bubble agent">Support: Your order has shipped and is expected by the listed delivery date.</div>
                    <div class="mini-bubble agent">Next step: Offer a helpful in-stock alternative when the customer asks for a lower price.</div>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(f"<div class='status-mini-card mobile-hide'>{backend_status_chip()}</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(metric_card("🛍️", "Product SKUs", str(len(products)), f"{in_stock} currently sellable"), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card("📦", "Orders", str(len(orders)), "Tracking + status data"), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card("🧭", "Backend APIs", "12+", "Agent • Orders • Admin • Logs"), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card("⭐", "Avg Rating", f"{avg_rating:.1f}", f"{inventory_units} inventory units"), unsafe_allow_html=True)

st.write("")
workflow_cols = st.columns(4)
workflow = [
    (1, "Listen", "Reads the customer message and identifies what help is needed."),
    (2, "Verify", "Checks available order, product, price, stock, and delivery data."),
    (3, "Compare", "Looks across the catalogue for relevant and budget-friendly choices."),
    (4, "Respond", "Creates a clear customer-ready reply without guessing unavailable details."),
]
for column, item in zip(workflow_cols, workflow):
    with column:
        st.markdown(workflow_card(*item), unsafe_allow_html=True)

st.write("")
chat_tab, trace_tab, catalog_tab, orders_tab, logs_tab, about_tab = st.tabs(
    ["💬 Support Desk", "🧭 Resolution Timeline", "🛒 Catalogue", "📦 Orders", "📜 Activity", "🏢 System Notes"]
)

with chat_tab:
    st.markdown("<div class='section-heading'>Support Desk</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-subtitle'>Enter a customer message and see the final reply, request type, confidence, and data checks.</div>", unsafe_allow_html=True)
    st.markdown("<div class='mobile-quick-actions'><div class='section-subtitle'>Quick customer messages</div></div>", unsafe_allow_html=True)
    mobile_prompt_cols = st.columns(2)
    for index, prompt in enumerate(SAMPLE_PROMPTS[:4]):
        with mobile_prompt_cols[index % 2]:
            if st.button(prompt, key=f"mobile_sample_{index}"):
                st.session_state.selected_prompt = prompt
                st.session_state.last_question = prompt
    with st.container():
        st.markdown("<div class='chat-shell'>", unsafe_allow_html=True)
        with st.form("agent_form", clear_on_submit=False):
            question = st.text_input(
                "Question",
                value=st.session_state.selected_prompt,
                placeholder="Example: Is there a cheaper alternative to the shoes I ordered in ORD-1002?",
                label_visibility="collapsed",
            )
            col_a, col_b = st.columns([0.72, 0.28])
            with col_a:
                submitted = st.form_submit_button("Generate Reply")
            with col_b:
                clear_history = st.form_submit_button("Clear History")

        if clear_history:
            st.session_state.history = []
            st.session_state.last_result = None

        if submitted:
            result = get_support_result(question)
            st.session_state.last_result = result
            st.session_state.last_question = question
            st.session_state.history.insert(0, {"question": question, "result": result})

        if st.session_state.last_result:
            result = st.session_state.last_result
            st.markdown(f"<div class='user-bubble'><strong>Customer</strong><br>{safe(st.session_state.last_question)}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='chat-answer'><strong>ShopAssist Commerce</strong><br>{safe(result.answer)}</div>", unsafe_allow_html=True)
            st.write("")
            insight_cols = st.columns(3)
            with insight_cols[0]:
                st.markdown(metric_card("🎯", "Request Type", result.intent, "Message routing"), unsafe_allow_html=True)
            with insight_cols[1]:
                st.markdown(metric_card("📈", "Confidence", f"{int(result.confidence * 100)}%", "Routing score"), unsafe_allow_html=True)
            with insight_cols[2]:
                st.markdown(metric_card("🔎", "Data Checks", str(len(result.tool_calls)), "Verified steps"), unsafe_allow_html=True)
        else:
            st.markdown(
                """
                <div class="prompt-card">
                    <strong>Try it:</strong> Start with an order tracking message or ask for a budget-friendly product alternative.
                    The workspace will show a clean customer reply and the internal data checks used to prepare it.
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.history:
        st.markdown("<div class='section-heading'>Recent Conversations</div>", unsafe_allow_html=True)
        for item in st.session_state.history[:5]:
            st.markdown(
                f"<div class='user-bubble'><strong>Q:</strong> {safe(item['question'])}<br><strong>A:</strong> {safe(item['result'].answer)}</div>",
                unsafe_allow_html=True,
            )

with trace_tab:
    st.markdown("<div class='section-heading'>Resolution Timeline</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-subtitle'>Internal view of the steps used to prepare the customer reply.</div>", unsafe_allow_html=True)
    result = st.session_state.last_result
    if not result:
        st.info("Run a customer message in the Support Desk tab to view the timeline.")
    else:
        st.markdown(
            f"<span class='tool-badge'>Request: {safe(result.intent)}</span> <span class='tool-badge'>Confidence: {int(result.confidence*100)}%</span> <span class='neutral-badge'>Verified store data</span>",
            unsafe_allow_html=True,
        )
        if result.entities:
            st.markdown("#### Extracted entities")
            st.json(result.entities)
        if not result.tool_calls:
            st.markdown("<span class='warning-badge'>No backend lookup needed for this message</span>", unsafe_allow_html=True)
        for index, call in enumerate(result.tool_calls, start=1):
            st.markdown(trace_card(index, call), unsafe_allow_html=True)
        with st.expander("Structured support result"):
            st.json(result.to_dict())

with catalog_tab:
    st.markdown("<div class='section-heading'>Store Catalogue</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-subtitle'>{len(products)} products • {in_stock} in stock • {budget_count} value picks under ₹2,000.</div>", unsafe_allow_html=True)
    categories = ["All"] + sorted({product["category"] for product in products})
    selected_category = st.selectbox("Filter catalogue", categories)
    visible_products = products if selected_category == "All" else [product for product in products if product["category"] == selected_category]
    cols = st.columns(3)
    for index, product in enumerate(visible_products):
        with cols[index % 3]:
            st.markdown(product_card(product), unsafe_allow_html=True)

with orders_tab:
    st.markdown("<div class='section-heading'>Order Tracking Overview</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-subtitle'>Read-only fulfillment view for support teams. Status changes are handled only inside the private backend admin panel.</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="ops-panel">
            <div class="ops-title">Customer-safe order view</div>
            <div class="ops-copy">
                This page shows order status, tracking, ETA, and latest updates for support visibility.
                Editing is not available here, so public/support users cannot change fulfillment records accidentally.
                Use the separate backend admin panel for Dispatch, Delivered, and other status updates.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not orders:
        st.info("No orders available.")
    else:
        status_filter = st.selectbox("Filter by status", ["All"] + ORDER_STATUSES)
        visible_orders = orders if status_filter == "All" else [order for order in orders if order.get("status") == status_filter]
        if not visible_orders:
            st.info("No orders match this status.")
        else:
            order_cols = st.columns(2)
            for index, order in enumerate(visible_orders):
                with order_cols[index % 2]:
                    st.markdown(order_card(order), unsafe_allow_html=True)

with logs_tab:
    st.markdown("<div class='section-heading'>Activity Logs</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-subtitle'>Recent support actions for audit, debugging, and quality review.</div>", unsafe_allow_html=True)
    logs = read_recent_logs(limit=80)
    if not logs:
        st.info("No activity yet. Run a support message first.")
    else:
        st.dataframe(logs, use_container_width=True, hide_index=True)
    log_path = Path("logs/tool_calls.jsonl")
    st.caption(f"Logs are stored at: {log_path}")

with about_tab:
    st.markdown("<div class='section-heading'>System Notes</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="glass-card">
            <p><strong>Why this workspace looks professional:</strong></p>
            <p class="muted">
                The workspace presents customer support as a polished commerce product with clean cards, fast replies, and transparent data checks.
                It stays practical for company review while looking like a real support dashboard.
            </p>
            <span class="tool-badge">Order tracking</span>
            <span class="tool-badge">Resolution timeline</span>
            <span class="tool-badge">Product matching</span>
            <span class="tool-badge">Safe fallbacks</span>
            <span class="tool-badge">Customer-ready replies</span>
            <span class="tool-badge">Professional UI</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown("<div class='section-heading'>Backend API</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="glass-card">
            <p class="muted">The project includes a FastAPI backend with Swagger documentation, health check, agent endpoint, orders endpoint, protected admin fulfillment endpoint, product search endpoint, metrics endpoint, and log viewer endpoint.</p>
            <span class="tool-badge">POST /api/agent/ask</span>
            <span class="tool-badge">GET /api/orders/{order_id}</span>
            <span class="tool-badge">PATCH /api/admin/orders/{order_id}/status</span>
            <span class="tool-badge">GET /api/products/search</span>
            <span class="tool-badge">GET /api/metrics</span>
            <span class="tool-badge">GET /docs</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown(
            """
            <div class="workflow-card">
                <div class="workflow-title">How to explain it to the company</div>
                <div class="workflow-copy">
                    I built a commerce support assistant for an online store. It reads customer messages, checks order and product records,
                    compares relevant catalogue options, handles invalid data safely, and returns a natural support-style answer.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_right:
        st.markdown(
            """
            <div class="workflow-card">
                <div class="workflow-title">Data safety</div>
                <div class="workflow-copy">
                    The assistant only uses available store data. If an order, product, or search result is missing,
                    it says that clearly and never invents customer information.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
