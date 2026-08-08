# 🤖 Universal Database AI Agent (MySQL & PostgreSQL)

An intelligent, full-stack AI Database Assistant supporting **MySQL** and **PostgreSQL** engines. Powered by **LangChain**, **LangGraph**, **FastAPI**, and **React**.

---

## 🌟 Key Features

- **Multi-Engine Support (MySQL & PostgreSQL)**: Connect to MySQL (`3306`) or PostgreSQL (`5432`) databases via standard credentials or 1-Click Connection URIs (`postgres://...` / `mysql://...`).
- **Full 4 SQL Sub-Languages Support**: Translates natural language into DDL (`CREATE`, `ALTER`, `DROP`), DML (`SELECT`, `INSERT`, `UPDATE`, `DELETE`), DCL (`GRANT`, `REVOKE`), and TCL (`COMMIT`, `ROLLBACK`).
- **Confirmation Gate for Destructive Actions**: Requires explicit confirmation (`✅ Confirm Action` / `Cancel Action`) before executing irreversible queries (`DROP`, `DELETE`, `TRUNCATE`, `ALTER`).
- **Actionable Error Formatting**: Provides plain-language explanations and closest schema suggestions for syntax or table/column errors.
- **Interactive Visual Data Grid**: View query results in a searchable grid with CSV export.
- **Dynamic Theme Accent Switcher**: Switch theme visual accents on the fly (Cyber Blue, Emerald Mint, Royal Purple, Sunset Rose).
- **1-Click Deployment Ready**: Configured for Vercel cloud deployment (`vercel.json`) and 1-click Windows desktop execution (`start_agent.bat`).

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/AKSHAY18-prog123/Database-agent.git
cd Database-agent

# Install Python requirements
pip install -r requirements.txt

# Install React frontend requirements
cd frontend && npm install && cd ..
```

### 2. Environment Variables
Copy `.env.example` to `.env` and add your OpenAI / OpenRouter API Key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
OPENAI_API_KEY=your_openrouter_or_openai_api_key_here
```

### 3. Run Application
- **Windows 1-Click**: Double-click `start_agent.bat`
- **Manual Launch**:
  ```bash
  # Terminal 1: Backend
  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

  # Terminal 2: Frontend
  cd frontend && npm run dev
  ```
- Open browser at `http://localhost:5173`.

---

## 🌐 Deploying to Vercel
1. Connect this GitHub repository to **[Vercel.com](https://vercel.com)**.
2. Set Environment Variable `OPENAI_API_KEY` in Vercel project settings.
3. Click **Deploy**! Vercel automatically deploys the FastAPI serverless backend and React frontend.
