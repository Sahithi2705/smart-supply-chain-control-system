# NEXUS TOWER — Supply Chain Intelligence Platform Frontend

NEXUS TOWER is a modern, enterprise-grade supply chain intelligence control tower frontend built from scratch with **React 18**, **TypeScript**, **Vite**, **Tailwind CSS**, **Recharts**, and **Amazon Cognito** authentication.

---

## 1. Architectural Highlights

- **Zero-Synthetic Data Compliance:** Designed explicitly to connect with the FastAPI backend (`http://127.0.0.1:8000`). When backend files or SQLite tables are uninitialized, the UI displays informative provenance banners and empty states rather than fabricating synthetic business data.
- **Amazon Cognito Integration:** Configured for AWS Region `ap-south-1` using a public User Pool client (no client secrets exposed in frontend bundles) with full session persistence and protected route boundaries.
- **Enterprise UI/UX Design:** Dark navy/charcoal interface with teal/blue accents, collapsible left sidebar navigation, top navigation with live API health heartbeat, metric KPI cards, interactive line/donut/bar charts, and searchable, filterable data tables.

---

## 2. Navigation & Feature Modules

1. **Overview (`/`)**: Executive control tower dashboard with total shipments, delayed event counts, critical risk incidents, inventory risk distribution, and module execution matrix.
2. **Shipment Tracking (`/shipments`)**: Real-time Kafka/SQLite event stream and grouped shipment tracking with delay status classification, ETA variance in hours, stockout risk, and interactive lifecycle timeline modal.
3. **Demand Forecasting (`/forecasts`)**: Module 3 ML inference comparisons (XGBoost, Seasonal Naive, 7-day Moving Average) against M5 historical sales test data. *Explicitly labeled as historical test predictions, not live future forecasts.*
4. **Inventory Management (`/inventory`)**: Module 4 safety stock, reorder point (ROP), simulated current inventory (14-day stock assumption), days of supply, and recommended order quantities. *Clearly designated as simulated inventory.*
5. **Risk Intelligence (`/risk`)**: Module 5 composite risk scoring engine (0–100 scale), severity distribution (CRITICAL, HIGH, MEDIUM, LOW), incident stream, and actionable mitigation recommendations.
6. **Analytics (`/analytics`)**: Cross-module analytics and pipeline status across all 5 supply chain modules.
7. **Settings (`/settings`)**: Amazon Cognito session credentials, public client settings, API ping latency diagnostics, and FastAPI OpenAPI documentation links.

---

## 3. Technology Stack

- **Framework:** React 18
- **Build Tool:** Vite 6
- **Language:** TypeScript 5.7
- **Styling:** Tailwind CSS 3.4 (with customized dark navy palette)
- **Charts:** Recharts 2.15
- **Icons:** Lucide React
- **Routing:** React Router DOM 6
- **HTTP Client:** Axios
- **Authentication:** Amazon Cognito Identity JS (`amazon-cognito-identity-js`)

---

## 4. Setup & Execution

### Prerequisites

- Node.js (v18+ recommended, verified on Node.js v26)
- Python 3.10+ (with FastAPI, Uvicorn, Pandas, PyArrow installed)

### 1. Environment Configuration

Copy the example configuration file:

```bash
cp .env.example .env.local
```

Verify your `.env.local` contains:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_COGNITO_REGION=ap-south-1
VITE_COGNITO_USER_POOL_ID=ap-south-1_gqD253QfU
VITE_COGNITO_CLIENT_ID=1h5fsjuph932ie83vdbgol7b3p
```

> **Security Note:** `.env.local` is excluded by `.gitignore` and must never be committed to source control.

### 2. Install Frontend Dependencies

```bash
cd nexus-tower-frontend
npm install
```

### 3. Start the Backend API

In the root of the project:

```bash
uvicorn services.main:app --reload --host 127.0.0.1 --port 8000
```

Backend base URL: `http://127.0.0.1:8000`  
Interactive OpenAPI Swagger docs: `http://127.0.0.1:8000/docs`

### 4. Start the Frontend Application

In `nexus-tower-frontend`:

```bash
npm run dev
```

Open your browser to:

```
http://localhost:5173
```

### 5. Authentication

- **Cognito Sign-in:** Enter your Cognito User Pool credentials.
- **Evaluation / Operator Mode:** For rapid evaluation without live AWS credentials, click **"Enter as Control Tower Operator (Evaluation Mode)"** on the login screen to access the telemetry dashboard immediately.

### 6. Production Build

```bash
npm run build
npm run preview
```
