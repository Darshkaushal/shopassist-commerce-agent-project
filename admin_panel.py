"""Private Streamlit backend operations panel for ShopAssist Commerce.

Run after starting FastAPI:
    set SHOPASSIST_API_URL=http://127.0.0.1:8000
    set SHOPASSIST_ADMIN_KEY=shopassist-admin-2026
    streamlit run admin_panel.py

This panel is intentionally separate from app.py so status updates are not available in
the public/support website view.
"""

from __future__ import annotations

import os
from html import escape
from typing import Any, Dict, List

import requests
import streamlit as st

from shopassist_agent.data import ORDER_STATUSES, ORDERS, PRODUCTS, STATUS_DESCRIPTIONS, STATUS_PROGRESS
from shopassist_agent.tools import update_order_status as local_update_order_status

st.set_page_config(
    page_title="ShopAssist Commerce | Admin Backend",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv("SHOPASSIST_API_URL", "http://127.0.0.1:8000").strip().rstrip("/")
ADMIN_KEY = os.getenv("SHOPASSIST_ADMIN_KEY", "shopassist-admin-2026")
API_TIMEOUT = (4, 24)



def safe(value: object) -> str:
    return escape(str(value))


def rupee(value: int | float) -> str:
    return f"₹{int(value):,}"


CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
h1, h2, h3, .brand, .page-title, .metric-value { font-family: 'Sora', sans-serif; }
.stApp {
    background:
        radial-gradient(circle at 5% 5%, rgba(59,130,246,.28), transparent 30%),
        radial-gradient(circle at 80% 0%, rgba(16,185,129,.18), transparent 28%),
        linear-gradient(135deg, #050816 0%, #0b1020 55%, #111827 100%);
    color: #f8fafc;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1420px; padding-top: 1.2rem; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(3,7,18,.98), rgba(15,23,42,.96));
    border-right: 1px solid rgba(255,255,255,.12);
}
.hero, .panel, .metric, .order-card {
    border: 1px solid rgba(255,255,255,.14);
    background: rgba(15,23,42,.74);
    box-shadow: 0 24px 80px rgba(0,0,0,.30);
    border-radius: 28px;
    backdrop-filter: blur(18px);
}
.hero { padding: 32px 34px; margin-bottom: 20px; }
.page-title { font-size: 48px; line-height: 1; letter-spacing: -0.055em; margin: 0; }
.hero-copy { color: #cbd5e1; max-width: 760px; font-size: 16px; margin-top: 12px; }
.badge {
    display:inline-flex; align-items:center; gap:8px; padding:8px 12px; border-radius:999px;
    border:1px solid rgba(255,255,255,.15); color:#dbeafe; background:rgba(59,130,246,.12);
    font-size:12px; font-weight:800; letter-spacing:.04em; text-transform:uppercase;
}
.success-badge { background:rgba(34,197,94,.14); color:#bbf7d0; border-color:rgba(34,197,94,.30); }
.warn-badge { background:rgba(245,158,11,.14); color:#fde68a; border-color:rgba(245,158,11,.30); }
.danger-badge { background:rgba(239,68,68,.14); color:#fecaca; border-color:rgba(239,68,68,.32); }
.panel { padding: 24px; margin: 14px 0; }
.panel-title { font-size: 20px; font-weight: 800; margin-bottom: 6px; }
.muted { color:#94a3b8; font-size:14px; }
.metric { padding:20px; min-height:132px; }
.metric-label { color:#94a3b8; font-size:12px; text-transform:uppercase; letter-spacing:.08em; font-weight:800; }
.metric-value { font-size:34px; font-weight:800; margin-top:4px; }
.metric-foot { color:#9ca3af; font-size:13px; margin-top:4px; }
.order-card { padding: 20px; margin-bottom: 16px; }
.order-head { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
.order-id { font-size:22px; font-weight:800; letter-spacing:-.02em; }
.grid-four { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:12px; margin-top:18px; }
.info-box { border:1px solid rgba(255,255,255,.10); background:rgba(2,6,23,.38); border-radius:18px; padding:14px; }
.info-label { color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:.08em; font-weight:800; }
.info-value { font-size:15px; font-weight:800; color:#f8fafc; margin-top:6px; }
.progress-track { height:10px; background:rgba(255,255,255,.10); border-radius:999px; overflow:hidden; margin:14px 0; }
.progress-fill { height:100%; background:linear-gradient(90deg,#3b82f6,#22c55e); border-radius:999px; }
.stButton > button, .stFormSubmitButton > button {
    border-radius:14px; min-height:44px; font-weight:800; border:0;
    background:linear-gradient(135deg,#2563eb,#10b981); color:white;
}
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div {
    border-radius:14px !important; background:rgba(2,6,23,.55) !important; color:#f8fafc !important;
}


* { box-sizing: border-box; }
html, body { overflow-x: hidden; }
.element-container { overflow-wrap: anywhere; }
.status-mini-card {
    padding:12px 14px; border-radius:18px; background:rgba(15,23,42,.72);
    border:1px solid rgba(255,255,255,.12); color:#cbd5e1; font-size:12px; line-height:1.45;
    margin-bottom:12px;
}
.mobile-unlock { display:none; }
@media (max-width: 980px) {
    [data-testid="stSidebar"] { display:none !important; }
    [data-testid="collapsedControl"] { display:none !important; }
    [data-testid="stHeader"] { display:none !important; }
    .block-container { padding:0.75rem 0.85rem 1.5rem !important; max-width:100% !important; }
    .hero { padding:20px 18px !important; border-radius:24px !important; margin-bottom:14px !important; }
    .page-title { font-size:clamp(30px, 12vw, 42px) !important; line-height:1.06 !important; letter-spacing:-.05em !important; }
    .hero-copy { font-size:14px !important; line-height:1.6 !important; }
    .panel, .metric, .order-card { border-radius:20px !important; padding:15px !important; box-shadow:0 14px 38px rgba(0,0,0,.25) !important; }
    .grid-four { grid-template-columns:1fr 1fr !important; gap:8px !important; }
    .order-head { flex-direction:column !important; }
    .order-id { font-size:19px !important; }
    .metric-value { font-size:25px !important; }
    .badge { font-size:10.5px !important; padding:6px 8px !important; }
    .mobile-unlock { display:block !important; }
    .stButton > button, .stFormSubmitButton > button { min-height:44px !important; border-radius:14px !important; }
    .stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div { min-height:46px !important; }
}
@media (max-width: 520px) { .grid-four { grid-template-columns:1fr !important; } }

</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

VISIBILITY_FIX_CSS = """
<style>
/* High-contrast production visibility fix */
:root {
    --bg: #050712;
    --panel: rgba(17, 24, 39, 0.90);
    --panel-strong: rgba(15, 23, 42, 0.98);
    --line: rgba(226, 232, 240, 0.20);
    --line-strong: rgba(226, 232, 240, 0.36);
    --text: #ffffff;
    --muted: #d1d5db;
    --soft: #e5e7eb;
    --brand: #8b5cf6;
    --brand-2: #22d3ee;
}

html, body, .stApp, [data-testid="stAppViewContainer"], .block-container,
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li, p, li, span, label, div {
    color: #f8fafc;
    text-rendering: geometricPrecision;
}

.stApp {
    background:
        radial-gradient(circle at 16% 6%, rgba(139, 92, 246, 0.36), transparent 30%),
        radial-gradient(circle at 88% 0%, rgba(34, 211, 238, 0.28), transparent 28%),
        linear-gradient(140deg, #050712 0%, #0b1020 48%, #081827 100%) !important;
}

/* sidebar text was looking dull on laptop/mobile */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(5, 7, 18, 0.99), rgba(11, 18, 32, 0.98)) !important;
    border-right: 1px solid rgba(226, 232, 240, 0.18) !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] .stCaptionContainer {
    color: #f8fafc !important;
    opacity: 1 !important;
}
[data-testid="stSidebar"] .stCaptionContainer, .brand-subtitle, .muted, .section-subtitle,
.workflow-copy, .product-meta, .desc, .hero-copy, .metric-foot, .ops-copy {
    color: #dbe4f0 !important;
    opacity: 1 !important;
}

.sidebar-brand, .hero, .metric-card, .glass-card, .trace-card, .product-card, .order-card, .workflow-card,
.prompt-card, .chat-shell, .ops-panel, .status-mini-card {
    background: linear-gradient(145deg, rgba(17,24,39,0.94), rgba(15,23,42,0.86)) !important;
    border: 1px solid rgba(226,232,240,0.18) !important;
    box-shadow: 0 20px 70px rgba(0,0,0,0.42) !important;
}

.hero {
    background:
        linear-gradient(135deg, rgba(124, 58, 237, 0.32), rgba(6, 182, 212, 0.22)),
        rgba(15, 23, 42, 0.92) !important;
}

.brand-title, .hero-title, .section-heading, .workflow-title, .product-name,
.order-title, .trace-title, .metric-value, .price, .fulfillment-value, .logo-mark {
    color: #ffffff !important;
    opacity: 1 !important;
    text-shadow: 0 1px 1px rgba(0,0,0,0.22);
}
.hero-title span {
    background: linear-gradient(135deg, #ffffff 0%, #ddd6fe 42%, #67e8f9 88%) !important;
    -webkit-background-clip: text !important;
    background-clip: text !important;
    color: transparent !important;
}

.eyebrow, .pill, .tool-badge, .warning-badge, .danger-badge, .neutral-badge,
.status-step, .rating, .metric-label, .fulfillment-label {
    opacity: 1 !important;
    filter: none !important;
}
.pill {
    background: rgba(255,255,255,0.14) !important;
    border-color: rgba(255,255,255,0.22) !important;
    color: #ffffff !important;
}
.metric-label, .fulfillment-label {
    color: #c7d2fe !important;
}
.workflow-copy, .product-meta, .desc, .muted, .section-subtitle {
    color: #dbe4f0 !important;
}

/* Streamlit widgets */
.stButton > button, .stFormSubmitButton > button {
    color: #ffffff !important;
    background: linear-gradient(135deg, #7c3aed 0%, #0ea5e9 100%) !important;
    border: 1px solid rgba(255,255,255,0.28) !important;
    box-shadow: 0 16px 36px rgba(14,165,233,0.22) !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: linear-gradient(135deg, #8b5cf6 0%, #22d3ee 100%) !important;
    border-color: rgba(255,255,255,0.42) !important;
}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    background: rgba(15, 23, 42, 0.94) !important;
    color: #ffffff !important;
    caret-color: #22d3ee !important;
    border: 1px solid rgba(226,232,240,0.32) !important;
    font-weight: 700 !important;
}
[data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder {
    color: #cbd5e1 !important;
    opacity: 1 !important;
}
[data-baseweb="select"] > div, [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: rgba(15, 23, 42, 0.94) !important;
    color: #ffffff !important;
    border: 1px solid rgba(226,232,240,0.32) !important;
}

/* tabs look like a real product nav */
.stTabs [data-baseweb="tab"] {
    color: #f8fafc !important;
    background: rgba(255,255,255,0.10) !important;
    border-color: rgba(255,255,255,0.18) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #7c3aed 0%, #0284c7 100%) !important;
    color: #ffffff !important;
}

code, pre { color: #dbeafe !important; background: rgba(2, 6, 23, 0.70) !important; }
.stAlert { color: #0f172a !important; }
.stAlert * { color: inherit !important; }

/* Better laptop spacing */
.block-container { padding-left: 2.2rem !important; padding-right: 2.2rem !important; }

@media (max-width: 980px) {
    .block-container { padding: 0.8rem 0.8rem 1.5rem 0.8rem !important; }
    html, body, .stApp, [data-testid="stMarkdownContainer"] p, p, li, span, label, div {
        font-size-adjust: none;
    }
    .hero, .metric-card, .workflow-card, .glass-card, .trace-card, .product-card, .order-card, .chat-shell, .ops-panel, .prompt-card {
        background: rgba(15, 23, 42, 0.94) !important;
        border-color: rgba(226, 232, 240, 0.18) !important;
    }
    .hero-title { color: #ffffff !important; }
    .hero-copy, .section-subtitle, .workflow-copy, .desc, .muted { color: #e5e7eb !important; }
}
</style>
"""

st.markdown(VISIBILITY_FIX_CSS, unsafe_allow_html=True)



def auth_headers(admin_key: str) -> Dict[str, str]:
    return {"X-Admin-Key": admin_key}


def backend_online() -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=API_TIMEOUT)
        return response.status_code == 200
    except Exception:
        return False


def get_admin_orders(admin_key: str) -> List[Dict[str, Any]]:
    try:
        response = requests.get(f"{API_BASE_URL}/api/admin/orders", headers=auth_headers(admin_key), timeout=API_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        st.session_state.admin_backend_note = f"Backend is waking or temporarily slow. Local preview loaded safely. {exc}"
        return list(ORDERS.values())


def update_admin_order(order_id: str, admin_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = requests.patch(
            f"{API_BASE_URL}/api/admin/orders/{order_id}/status",
            json=payload,
            headers=auth_headers(admin_key),
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        raise RuntimeError(f"Backend rejected the update: {detail}") from exc
    except Exception as exc:
        if backend_online():
            raise RuntimeError(str(exc)) from exc
        updated = local_update_order_status(order_id, payload["status"], **{k: v for k, v in payload.items() if k != "status"})
        if not updated:
            raise RuntimeError(f"Order {order_id} was not found")
        return updated


def status_badge(status: str) -> str:
    if status == "Delivered":
        cls = "success-badge"
    elif status == "Cancelled":
        cls = "danger-badge"
    elif status in {"Processing", "Dispatched"}:
        cls = "warn-badge"
    else:
        cls = "badge"
    return f"<span class='badge {cls}'>{safe(status)}</span>"


def order_card(order: Dict[str, Any]) -> str:
    progress = STATUS_PROGRESS.get(order.get("status"), 25)
    items = []
    for item in order.get("items", []):
        product = PRODUCTS.get(item.get("product_id"), {"name": item.get("product_id")})
        items.append(f"{product['name']} × {item.get('quantity', 1)}")
    return f"""
    <div class="order-card">
        <div class="order-head">
            <div>
                <div class="order-id">{safe(order.get('order_id'))}</div>
                <div class="muted">{safe(order.get('customer_name'))} • Placed {safe(order.get('placed_on'))}</div>
            </div>
            {status_badge(order.get('status', 'Unknown'))}
        </div>
        <div class="progress-track"><div class="progress-fill" style="width:{progress}%"></div></div>
        <div class="grid-four">
            <div class="info-box"><div class="info-label">Total</div><div class="info-value">{rupee(order.get('order_total', 0))}</div></div>
            <div class="info-box"><div class="info-label">Tracking ID</div><div class="info-value">{safe(order.get('tracking_id') or 'Pending')}</div></div>
            <div class="info-box"><div class="info-label">Carrier</div><div class="info-value">{safe(order.get('carrier') or 'Not assigned')}</div></div>
            <div class="info-box"><div class="info-label">ETA</div><div class="info-value">{safe(order.get('eta'))}</div></div>
        </div>
        <p class="muted" style="margin-top:14px;"><strong>Items:</strong> {safe(', '.join(items))}</p>
        <p class="muted"><strong>Latest update:</strong> {safe(order.get('last_update'))}</p>
    </div>
    """


with st.sidebar:
    st.markdown("<div class='panel'><div class='brand'>🔐 Admin Backend</div><div class='muted'>Private operations console</div></div>", unsafe_allow_html=True)
    st.markdown("#### Backend connection")
    st.code(API_BASE_URL)
    if backend_online():
        st.success("FastAPI backend is online")
    else:
        st.info("Backend is waking or not reachable. Local preview remains available.")
    st.markdown("---")
    entered_key = st.text_input("Admin API key", type="password", placeholder="Enter backend admin key")
    unlock = st.button("Unlock admin panel")
    if unlock:
        st.session_state.admin_unlocked = entered_key == ADMIN_KEY
        st.session_state.admin_key = entered_key
    if st.session_state.get("admin_unlocked"):
        st.success("Admin access granted")
    else:
        st.info("Status updates stay locked until admin key is verified.")
    st.markdown("---")
    st.caption("Default local demo key is shown in README. Change SHOPASSIST_ADMIN_KEY before sharing publicly.")

st.markdown(
    """
    <div class="hero">
        <span class="badge success-badge">Protected backend panel</span>
        <h1 class="page-title">Fulfillment operations console</h1>
        <p class="hero-copy">
            Update order status, tracking number, courier partner, delivery ETA, and customer-facing shipment notes from a private backend screen. The public support website is read-only and cannot edit fulfillment data.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("admin_backend_note"):
    st.markdown(f"<div class='status-mini-card'>{safe(st.session_state.admin_backend_note)}</div>", unsafe_allow_html=True)

# Mobile users cannot reliably access Streamlit sidebar, so provide unlock in the main screen too.
if not st.session_state.get("admin_unlocked"):
    st.markdown("<div class='mobile-unlock'>", unsafe_allow_html=True)
    with st.form("mobile_admin_unlock", clear_on_submit=False):
        mobile_key = st.text_input("Admin API key", type="password", placeholder="Enter backend admin key", key="mobile_admin_key")
        mobile_unlock = st.form_submit_button("Unlock admin panel")
        if mobile_unlock:
            st.session_state.admin_unlocked = mobile_key == ADMIN_KEY
            st.session_state.admin_key = mobile_key
    st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.get("admin_unlocked"):
    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Admin access required</div>
            <div class="muted">Enter the admin API key from the sidebar to unlock status updates. This keeps Delivered, Dispatched, and Cancelled controls away from the public website.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

admin_key = st.session_state.get("admin_key", ADMIN_KEY)
orders = get_admin_orders(admin_key)

status_counts: Dict[str, int] = {}
for order in orders:
    status_counts[order["status"]] = status_counts.get(order["status"], 0) + 1

metric_cols = st.columns(4)
with metric_cols[0]:
    st.markdown(f"<div class='metric'><div class='metric-label'>Orders</div><div class='metric-value'>{len(orders)}</div><div class='metric-foot'>Backend records</div></div>", unsafe_allow_html=True)
with metric_cols[1]:
    st.markdown(f"<div class='metric'><div class='metric-label'>In transit</div><div class='metric-value'>{status_counts.get('Dispatched',0)+status_counts.get('Shipped',0)+status_counts.get('Out for Delivery',0)}</div><div class='metric-foot'>Active shipments</div></div>", unsafe_allow_html=True)
with metric_cols[2]:
    st.markdown(f"<div class='metric'><div class='metric-label'>Delivered</div><div class='metric-value'>{status_counts.get('Delivered',0)}</div><div class='metric-foot'>Completed orders</div></div>", unsafe_allow_html=True)
with metric_cols[3]:
    st.markdown(f"<div class='metric'><div class='metric-label'>Admin API</div><div class='metric-value'>Secure</div><div class='metric-foot'>X-Admin-Key protected</div></div>", unsafe_allow_html=True)

st.write("")
left, right = st.columns([0.42, 0.58], gap="large")

with left:
    st.markdown("<div class='panel'><div class='panel-title'>Update fulfillment status</div><div class='muted'>Changes are sent to the protected FastAPI admin endpoint and used by the support assistant immediately.</div></div>", unsafe_allow_html=True)
    selected_order_id = st.selectbox(
        "Order",
        [order["order_id"] for order in orders],
        format_func=lambda value: f"{value} - {next((order['customer_name'] for order in orders if order['order_id'] == value), '')}",
    )
    current_order = next(order for order in orders if order["order_id"] == selected_order_id)
    status_index = ORDER_STATUSES.index(current_order["status"]) if current_order["status"] in ORDER_STATUSES else 0

    with st.form("admin_status_form", clear_on_submit=False):
        new_status = st.selectbox("New status", ORDER_STATUSES, index=status_index)
        tracking_id = st.text_input("Tracking ID", value=current_order.get("tracking_id") or "", placeholder="Example: TRK-1003DSP")
        carrier = st.text_input("Courier partner", value=current_order.get("carrier") or "", placeholder="Example: Delhivery")
        eta = st.text_input("Delivery ETA", value=current_order.get("eta") or "", placeholder="Example: Expected by tomorrow")
        last_update = st.text_area(
            "Customer-facing update note",
            value=current_order.get("last_update") or STATUS_DESCRIPTIONS.get(new_status, ""),
            height=110,
        )
        submitted = st.form_submit_button("Save status to backend")

    if submitted:
        payload = {
            "status": new_status,
            "tracking_id": tracking_id or None,
            "carrier": carrier or None,
            "eta": eta or None,
            "last_update": last_update or None,
        }
        try:
            updated = update_admin_order(selected_order_id, admin_key, payload)
            st.success(f"{updated['order_id']} updated to {updated['status']}. Open the public Support Desk and ask about this order to verify the new status.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not update status: {exc}")

with right:
    st.markdown("<div class='panel'><div class='panel-title'>Selected order record</div><div class='muted'>Current backend state before update.</div></div>", unsafe_allow_html=True)
    st.markdown(order_card(current_order), unsafe_allow_html=True)
    with st.expander("Raw backend order JSON"):
        st.json(current_order)

st.markdown("<div class='panel'><div class='panel-title'>All backend orders</div><div class='muted'>Read-only overview of orders available to the admin console.</div></div>", unsafe_allow_html=True)
filter_status = st.selectbox("Filter admin orders", ["All"] + ORDER_STATUSES, key="admin_filter")
visible_orders = orders if filter_status == "All" else [order for order in orders if order.get("status") == filter_status]
cols = st.columns(2)
for index, order in enumerate(visible_orders):
    with cols[index % 2]:
        st.markdown(order_card(order), unsafe_allow_html=True)
