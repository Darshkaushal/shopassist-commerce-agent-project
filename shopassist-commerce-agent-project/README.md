# ShopAssist Commerce Support Desk

A company-ready e-commerce support project with a public support workspace, a protected FastAPI backend, and a private admin operations panel.

The required company assignment function is preserved exactly:

```python
run_agent(question: str) -> str
```

The project answers online-store customer questions by selecting the correct tools, chaining calls when needed, handling missing data safely, and returning customer-friendly responses.

---

## What changed in this version

Earlier, the fulfillment status form was visible inside the main website. That is not realistic because any user could edit order status. In this version:

- The public Streamlit website is now **read-only** for orders.
- Status updates are moved to a separate **private admin backend panel**.
- The FastAPI status update endpoint is protected with an `X-Admin-Key` header.
- `Dispatched`, `Delivered`, `Processing`, `Shipped`, `Out for Delivery`, and `Cancelled` updates work from the admin panel.
- The support assistant immediately uses the latest backend status after an admin update.

---

## Key Features

- Required tools preserved exactly:
  - `get_order(order_id)`
  - `search_products(query)`
  - `get_product(product_id)`
- Required public function: `run_agent(question: str) -> str`
- FastAPI backend with Swagger documentation
- Protected admin status update endpoint
- Private Streamlit admin panel for fulfillment operations
- Public Streamlit support workspace with read-only order tracking
- Product detail lookup by product ID
- Catalogue search with category and budget filtering
- Cheaper alternative flow using order ID, product ID, or category
- Multi-item order handling
- Out-of-stock filtering for recommendations
- Safe handling of invalid orders, invalid products, and empty searches
- JSONL activity logging
- CLI mode for quick testing
- Unit tests for agent logic, backend API, protected admin flow, and status updates

---

## Project Structure

```text
shopassist-commerce-agent/
│
├── agent.py                         # Required assignment entry point wrapper
├── app.py                           # Public support website, read-only order view
├── admin_panel.py                   # Private backend operations panel
├── cli.py                           # Interactive CLI
├── requirements.txt
├── README.md
├── sample_outputs.txt
├── design_decisions.md
├── design_decisions.pdf
├── run_api.bat                      # Windows shortcut to start backend
├── run_ui.bat                       # Windows shortcut to start public UI
├── run_admin.bat                    # Windows shortcut to start admin panel
├── pytest.ini
│
├── backend/
│   ├── __init__.py
│   └── main.py                      # FastAPI backend
│
├── shopassist_agent/
│   ├── __init__.py
│   ├── agent.py                     # Core support assistant logic
│   ├── data.py                      # Mock order/product database
│   ├── logger.py                    # JSONL logging
│   ├── nlu.py                       # Request type + entity extraction
│   ├── schemas.py                   # Structured result models
│   └── tools.py                     # Required assignment tools + admin update helper
│
├── tests/
│   ├── test_agent.py
│   └── test_api.py
│
└── logs/
    └── .gitkeep
```

---

## Setup

### 1. Create virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run the project properly

### Terminal 1: Start FastAPI backend

```bash
uvicorn backend.main:app --reload
```

Backend URLs:

```text
API Home:  http://127.0.0.1:8000
Docs:      http://127.0.0.1:8000/docs
Health:    http://127.0.0.1:8000/health
```

### Terminal 2: Start public support website

Windows PowerShell:

```powershell
$env:SHOPASSIST_API_URL="http://127.0.0.1:8000"
streamlit run app.py
```

This website can answer customer questions and show orders, but it cannot update status.

### Terminal 3: Start private admin backend panel

Windows PowerShell:

```powershell
$env:SHOPASSIST_API_URL="http://127.0.0.1:8000"
$env:SHOPASSIST_ADMIN_KEY="shopassist-admin-2026"
streamlit run admin_panel.py
```

Open the admin panel and enter this demo key:

```text
shopassist-admin-2026
```

Then update any order to `Dispatched`, `Delivered`, or another supported status. After saving, open the public website and ask:

```text
Where is order ORD-1003?
```

The support assistant will answer using the updated backend status.

---

## Backend API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API landing response |
| GET | `/health` | Health check |
| POST | `/api/agent/ask` | Full support response with trace |
| POST | `/api/agent/simple` | Assignment-style answer only |
| GET | `/api/orders` | Public read-only order list |
| GET | `/api/orders/{order_id}` | Public read-only order details |
| GET | `/api/order-statuses` | Supported fulfillment statuses |
| GET | `/api/admin/orders` | Protected admin order list |
| PATCH | `/api/admin/orders/{order_id}/status` | Protected admin status update |
| GET | `/api/products` | List products |
| GET | `/api/products/{product_id}` | Product details |
| GET | `/api/products/search` | Search catalogue |
| GET | `/api/metrics` | Dashboard metrics |
| GET | `/api/logs` | Recent activity logs |

---

## Protected Admin API Example

Update an order to Dispatched:

```bash
curl -X PATCH "http://127.0.0.1:8000/api/admin/orders/ORD-1003/status" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: shopassist-admin-2026" \
  -d "{\"status\": \"Dispatched\", \"carrier\": \"Delhivery\", \"tracking_id\": \"TRK-1003DSP\", \"eta\": \"Expected by tomorrow\", \"last_update\": \"Package has been dispatched from the warehouse.\"}"
```

Update an order to Delivered:

```bash
curl -X PATCH "http://127.0.0.1:8000/api/admin/orders/ORD-1003/status" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: shopassist-admin-2026" \
  -d "{\"status\": \"Delivered\"}"
```

Without the admin key, the backend returns `401 Admin API key required`.

---

## Sample Customer Messages

```text
Where is order ORD-1002?
Is there a cheaper alternative to the shoes I ordered in ORD-1002?
Show me shoes under 2000
Tell me about product P-4001
Is order ORD-1003 dispatched?
Where is order ORD-9999?
Find cheaper alternative to P-1002
```

---

## Testing

```bash
pytest -q
```

Verified result:

```text
34 passed
```

---

## How to Explain This in Interview

I built a commerce support system with four layers:

1. A reusable Python assistant that exposes the required `run_agent(question: str) -> str` function.
2. A FastAPI backend that exposes assistant, order, product, metrics, logs, and protected admin endpoints.
3. A public Streamlit support workspace that customers/support users can use safely without editing orders.
4. A private admin backend panel where only authorized operations users can update fulfillment status.

For each customer question, the system detects the request type, extracts IDs or budget/category details, checks only available store data, calls the correct tools in sequence, and returns a clear customer-ready answer. It handles missing data safely and does not fabricate information.

---

## Notes

This project uses mock in-memory data because the assignment focuses on tool selection, tool chaining, error handling, and response quality. The same backend structure can later be connected to a real database, authentication provider, courier API, CRM, or order-management platform.

---

## Mobile/Desktop UI hardening update

This build has been polished for both phone screens and laptop/desktop screens.

### UI improvements

- Responsive hero section with smaller mobile typography.
- Sidebar is hidden on small screens to avoid overlap with the main content.
- Quick customer-message buttons are available inside the Support Desk on mobile.
- Product, order, metric, and timeline cards resize cleanly on narrow screens.
- Tabs, buttons, input fields, badges, and long backend URLs are wrapped safely.
- The public site no longer shows large yellow backend timeout warnings on mobile.

### Backend reliability improvement

Render free deployments can sleep when inactive. Earlier, this could show a large timeout warning on the public website. The app now handles this more professionally:

- If the backend is live, the UI uses the live FastAPI data.
- If Render is waking up or temporarily slow, the UI safely switches to local preview data.
- The customer support assistant still works and does not crash.
- A compact connection chip shows whether the app is using the live backend or local preview.

### Final live links

```text
GitHub Repository: https://github.com/Darshkaushal/shopassist-commerce-agent-project
Public Frontend:   https://shopassist-commerce.streamlit.app
Admin Panel:       https://shopassist-commerce-adm.streamlit.app
Backend API:       https://shopassist-commerce-backend.onrender.com
Backend Docs:      https://shopassist-commerce-backend.onrender.com/docs
```
