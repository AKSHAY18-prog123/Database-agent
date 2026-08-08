import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.config import settings
from backend.db_manager import DBManager
from backend.agent.sql_agent import run_agent_query
from backend.seed_db import seed_database

app = FastAPI(
    title="SQL AI Agent API",
    description="Natural language SQL assistant for MySQL database management",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global DB Manager instance
db_manager = DBManager()

# Helper to create DBManager from request headers or body credentials
from fastapi import Header

def get_request_db_manager(
    x_mysql_host: Optional[str] = Header(None),
    x_mysql_port: Optional[int] = Header(None),
    x_mysql_user: Optional[str] = Header(None),
    x_mysql_password: Optional[str] = Header(None),
    x_mysql_database: Optional[str] = Header(None)
) -> DBManager:
    if x_mysql_user:
        return DBManager(
            host=x_mysql_host or settings.MYSQL_HOST,
            port=x_mysql_port or settings.MYSQL_PORT,
            user=x_mysql_user,
            password=x_mysql_password or "",
            database=x_mysql_database or settings.MYSQL_DB
        )
    return db_manager

# Request Models
class ChatRequest(BaseModel):
    query: str
    openai_api_key: Optional[str] = None
    db_config: Optional[Dict[str, Any]] = None
    confirmed: Optional[bool] = False
    pending_sql: Optional[str] = None

class RawQueryRequest(BaseModel):
    sql: str
    db_config: Optional[Dict[str, Any]] = None

class SettingsRequest(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    db_type: Optional[str] = "mysql"
    connection_uri: Optional[str] = None
    openai_api_key: Optional[str] = None

class CreateTableRequest(BaseModel):
    table_name: str
    columns: List[Dict[str, str]]

class InsertDataRequest(BaseModel):
    table_name: str
    data: Dict[str, Any]

@app.get("/api/health")
def health_check():
    db_status = db_manager.test_connection()
    return {
        "status": "online",
        "database": db_status,
        "openai_configured": bool(settings.OPENAI_API_KEY)
    }

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    current_db_mgr = db_manager
    if req.db_config:
        current_db_mgr = DBManager(
            host=req.db_config.get('host') or db_manager.host,
            port=req.db_config.get('port') or db_manager.port,
            user=req.db_config.get('user') or db_manager.user,
            password=req.db_config.get('password') if req.db_config.get('password') is not None else db_manager.password,
            database=req.db_config.get('database') or db_manager.database,
            db_type=req.db_config.get('db_type') or db_manager.db_type,
            connection_uri=req.db_config.get('connection_uri') or db_manager.connection_uri
        )
    
    # Test connection first
    conn_test = current_db_mgr.test_connection()
    if conn_test.get("status") == "error":
        return {
            "query": req.query,
            "is_relevant": True,
            "sql": None,
            "response": f"🔑 **Database Connection Error**: Unable to connect to your database (`{conn_test.get('message')}`). Please verify your credentials or ensure the database service is running.",
            "error": conn_test.get('message'),
            "auth_required": True
        }

    api_key = req.openai_api_key or settings.OPENAI_API_KEY
    result = run_agent_query(
        user_query=req.query,
        db_manager=current_db_mgr,
        openai_api_key=api_key,
        confirmed=req.confirmed or False,
        pending_sql=req.pending_sql
    )
    return result

@app.get("/api/database/databases")
def get_databases():
    dbs = db_manager.get_all_databases()
    return {"databases": dbs}

@app.get("/api/database/schema")
def get_schema(db_name: Optional[str] = None):
    return db_manager.get_database_tree(db_name=db_name)

@app.get("/api/database/table/{table_name}")
def get_table_data(table_name: str, limit: int = 50, offset: int = 0):
    return db_manager.get_table_data(table_name=table_name, limit=limit, offset=offset)

@app.post("/api/database/raw_query")
def execute_raw_query(req: RawQueryRequest):
    if not req.sql.strip():
        raise HTTPException(status_code=400, detail="SQL query cannot be empty")
    return db_manager.execute_query(req.sql)

@app.post("/api/database/seed")
def seed_database_endpoint():
    try:
        seed_database()
        return {"status": "success", "message": "Database successfully re-seeded with 35+ records."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/database/create_table_visual")
def create_table_visual(req: CreateTableRequest):
    table_name = req.table_name.strip()
    if not table_name:
        raise HTTPException(status_code=400, detail="Table name is required")
    
    col_defs = []
    has_pk = False
    for col in req.columns:
        c_name = col.get("name", "").strip()
        c_type = col.get("type", "VARCHAR(100)").strip()
        if not c_name:
            continue
        is_pk = col.get("primary", False)
        is_null = col.get("nullable", True)
        
        parts = [f"`{c_name}` {c_type}"]
        if not is_null:
            parts.append("NOT NULL")
        if is_pk:
            parts.append("PRIMARY KEY AUTO_INCREMENT")
            has_pk = True
        col_defs.append(" ".join(parts))
        
    if not col_defs:
        raise HTTPException(status_code=400, detail="At least one valid column definition is required")
        
    sql = f"CREATE TABLE `{table_name}` (\n  " + ",\n  ".join(col_defs) + "\n);"
    res = db_manager.execute_query(sql)
    res['sql'] = sql
    return res

@app.post("/api/database/insert_data_visual")
def insert_data_visual(req: InsertDataRequest):
    table_name = req.table_name.strip()
    data = req.data
    if not table_name or not data:
        raise HTTPException(status_code=400, detail="Table name and row data are required")
        
    cols = [f"`{k}`" for k in data.keys()]
    vals = []
    for v in data.values():
        if isinstance(v, str):
            escaped = v.replace("'", "''")
            vals.append(f"'{escaped}'")
        elif v is None:
            vals.append("NULL")
        else:
            vals.append(str(v))
            
    sql = f"INSERT INTO `{table_name}` ({', '.join(cols)}) VALUES ({', '.join(vals)});"
    res = db_manager.execute_query(sql)
    res['sql'] = sql
    return res

@app.post("/api/settings")
def update_settings(req: SettingsRequest):
    if req.connection_uri and req.connection_uri.strip():
        parsed = DBManager.parse_connection_uri(req.connection_uri.strip())
        db_manager.db_type = parsed.get("db_type", db_manager.db_type)
        db_manager.host = parsed.get("host", db_manager.host)
        db_manager.port = parsed.get("port", db_manager.port)
        db_manager.user = parsed.get("user", db_manager.user)
        db_manager.password = parsed.get("password", db_manager.password)
        db_manager.database = parsed.get("database", db_manager.database)
        db_manager.connection_uri = req.connection_uri.strip()
    else:
        if req.db_type:
            db_manager.db_type = req.db_type.lower()
        if req.host:
            db_manager.host = req.host
            settings.MYSQL_HOST = req.host
        if req.port:
            db_manager.port = req.port
            settings.MYSQL_PORT = req.port
        if req.user:
            db_manager.user = req.user
            settings.MYSQL_USER = req.user
        if req.password is not None:
            db_manager.password = req.password
            settings.MYSQL_PASSWORD = req.password
        if req.database:
            db_manager.database = req.database
            settings.MYSQL_DB = req.database

    if req.openai_api_key is not None:
        settings.OPENAI_API_KEY = req.openai_api_key

    test_res = db_manager.test_connection()
    return {
        "status": "updated",
        "connection_test": test_res,
        "openai_configured": bool(settings.OPENAI_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
