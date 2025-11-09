## Financial Manager

FastAPI + Vue3 financial management system for small companies. Features:

- Email registration and login with JWT authentication
- Manage purchase list, sales list, and invoices
- SQLite storage (default) with SQLAlchemy ORM

### Backend

Install dependencies (using uv or pip):

```bash
uv sync
```

Run development server:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Tests

```bash
uv run pytest -q
```

### Frontend

Located in `frontend/` (Vite + Vue 3 + Pinia + Router + Axios).

Install & run:

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE` in a `.env` (defaults to http://127.0.0.1:8000):

```
VITE_API_BASE=http://127.0.0.1:8000
```

Production build:

```bash
npm run build
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| FM_SECRET_KEY | Override default JWT secret |
| FM_ACCESS_TOKEN_EXPIRE_MINUTES | Token expiration minutes |
| FM_JWT_ALGORITHM | JWT algorithm (default HS256) |

### Next Steps

- Form validation & better error handling
- Pagination & filtering
- Reporting endpoints (monthly totals, profit) & dashboard charts
- Role-based permissions & audit logging
- Invoice PDF export

### clean vscode server
```bash
# Kill server processes
kill -9 $(ps aux | grep vscode-server | grep $USER | grep -v grep | awk '{print $2}')
# Delete related files and folder
rm -rf $HOME/.vscode-server # Or ~/.vscode-server-insiders
```