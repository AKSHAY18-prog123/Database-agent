import re
import urllib.parse
from typing import Dict, List, Any, Optional
import mysql.connector
from mysql.connector import Error as MySQLError

try:
    import psycopg2
    from psycopg2 import sql as pg_sql
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

class DBManager:
    """
    Universal Database Manager supporting MySQL and PostgreSQL engines.
    Provides schema inspection, query execution, and plain-language connection error reporting.
    """
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: Optional[str] = None,
        db_type: str = "mysql",
        connection_uri: Optional[str] = None
    ):
        self.connection_uri = connection_uri
        self.db_type = (db_type or "mysql").lower()
        
        # Parse URI if provided
        if connection_uri and connection_uri.strip():
            parsed = self.parse_connection_uri(connection_uri.strip())
            self.db_type = parsed.get("db_type", self.db_type)
            self.host = parsed.get("host", host)
            self.port = parsed.get("port", port)
            self.user = parsed.get("user", user)
            self.password = parsed.get("password", password)
            self.database = parsed.get("database", database)
        else:
            self.host = host or "127.0.0.1"
            self.port = int(port) if port else (5432 if self.db_type == "postgres" else 3306)
            self.user = user or ("postgres" if self.db_type == "postgres" else "root")
            self.password = password or ""
            self.database = database

    @staticmethod
    def parse_connection_uri(uri: str) -> Dict[str, Any]:
        """Parses a MySQL or PostgreSQL connection string into components."""
        # e.g., postgres://user:pass@host:5432/dbname or mysql://user:pass@host:3306/dbname
        result = {"db_type": "mysql", "host": "127.0.0.1", "port": 3306, "user": "root", "password": "", "database": None}
        try:
            if uri.startswith("postgres://") or uri.startswith("postgresql://"):
                result["db_type"] = "postgres"
                result["port"] = 5432
                result["user"] = "postgres"
            elif uri.startswith("mysql://"):
                result["db_type"] = "mysql"
                result["port"] = 3306
                result["user"] = "root"

            parsed = urllib.parse.urlparse(uri)
            if parsed.hostname:
                result["host"] = parsed.hostname
            if parsed.port:
                result["port"] = parsed.port
            if parsed.username:
                result["user"] = urllib.parse.unquote(parsed.username)
            if parsed.password:
                result["password"] = urllib.parse.unquote(parsed.password)
            if parsed.path and len(parsed.path) > 1:
                result["database"] = parsed.path.lstrip("/")
        except Exception as e:
            print("URI Parsing warning:", e)
        return result

    def get_connection(self, db_name_override: Optional[str] = None):
        """Creates a database connection for MySQL or PostgreSQL."""
        target_db = db_name_override if db_name_override is not None else self.database

        if self.db_type == "postgres":
            if not HAS_POSTGRES:
                raise Exception("psycopg2 package is not installed. Please run `pip install psycopg2-binary`.")
            
            # Default to 'postgres' database if no database specified for meta queries
            pg_db = target_db or "postgres"
            try:
                conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    dbname=pg_db,
                    connect_timeout=5
                )
                conn.autocommit = True
                return conn
            except Exception as err:
                err_str = str(err).lower()
                if "could not connect to server" in err_str or "connection refused" in err_str or "is the server running" in err_str:
                    raise Exception(
                        f"❌ PostgreSQL engine is not running or reachable at {self.host}:{self.port}. "
                        f"Please ensure PostgreSQL service is started on your computer."
                    )
                elif "password authentication failed" in err_str or "role" in err_str:
                    raise Exception(
                        f"❌ PostgreSQL Password Authentication Failed for user '{self.user}'. "
                        f"Please verify your PostgreSQL password in Settings."
                    )
                elif "database" in err_str and "does not exist" in err_str:
                    raise Exception(f"❌ PostgreSQL database '{pg_db}' does not exist on your server.")
                else:
                    raise Exception(f"❌ PostgreSQL Connection Error: {str(err)}")
        else:
            # MySQL Connection
            try:
                kwargs = {
                    "host": self.host,
                    "port": self.port,
                    "user": self.user,
                    "password": self.password,
                    "connect_timeout": 5
                }
                if target_db:
                    kwargs["database"] = target_db

                conn = mysql.connector.connect(**kwargs)
                return conn
            except MySQLError as err:
                err_str = str(err).lower()
                if err.errno in (2003, 2002, 2005) or "can't connect" in err_str:
                    raise Exception(
                        f"❌ MySQL engine is not running or reachable at {self.host}:{self.port}. "
                        f"Please ensure MySQL service is started on your computer."
                    )
                elif err.errno in (1045, 1044) or "access denied" in err_str:
                    raise Exception(
                        f"❌ MySQL Password Authentication Failed for user '{self.user}'. "
                        f"Please verify your MySQL password in Settings."
                    )
                elif err.errno == 1049 or "unknown database" in err_str:
                    raise Exception(f"❌ MySQL database '{target_db}' does not exist on your server.")
                else:
                    raise Exception(f"❌ MySQL Connection Error: {str(err)}")

    def test_connection(self) -> Dict[str, Any]:
        """Tests connection to the configured database engine."""
        try:
            conn = self.get_connection()
            engine_label = "PostgreSQL 🐘" if self.db_type == "postgres" else "MySQL 🐬"
            conn.close()
            return {
                "status": "success",
                "message": f"Successfully connected to {engine_label} at {self.host}:{self.port} as user '{self.user}'!"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_all_databases(self) -> List[str]:
        """Lists all databases available on the server."""
        try:
            conn = self.get_connection(db_name_override=None if self.db_type == "mysql" else "postgres")
            cursor = conn.cursor()
            
            if self.db_type == "postgres":
                cursor.execute(
                    "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres', 'rdsadmin') ORDER BY datname;"
                )
                rows = cursor.fetchall()
                dbs = [r[0] for r in rows]
            else:
                cursor.execute("SHOW DATABASES;")
                rows = cursor.fetchall()
                dbs = [r[0] for r in rows if r[0] not in ('information_schema', 'mysql', 'performance_schema', 'sys')]
            
            cursor.close()
            conn.close()
            return dbs
        except Exception as e:
            print("Error fetching all databases:", e)
            return []

    def get_database_tree(self, db_name_override: Optional[str] = None) -> Dict[str, Any]:
        """Returns tables and column schema tree for the specified database."""
        target_db = db_name_override if db_name_override is not None else self.database
        all_dbs = self.get_all_databases()

        if not target_db:
            target_db = all_dbs[0] if all_dbs else ("school_management" if self.db_type == "mysql" else "postgres")

        result = {
            "database": target_db,
            "db_type": self.db_type,
            "allDatabases": all_dbs,
            "tables": []
        }

        try:
            conn = self.get_connection(db_name_override=target_db)
            cursor = conn.cursor()

            if self.db_type == "postgres":
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;"
                )
                table_names = [r[0] for r in cursor.fetchall()]

                for t_name in table_names:
                    cursor.execute(
                        "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position;",
                        (t_name,)
                    )
                    cols = cursor.fetchall()
                    
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{t_name}";')
                        r_count = cursor.fetchone()[0]
                    except Exception:
                        r_count = 0

                    result["tables"].append({
                        "name": t_name,
                        "rowCount": r_count,
                        "columns": [
                            {"name": c[0], "type": c[1], "nullable": c[2] == "YES"}
                            for c in cols
                        ]
                    })
            else:
                # MySQL
                cursor.execute("SHOW TABLES;")
                table_names = [r[0] for r in cursor.fetchall()]

                for t_name in table_names:
                    cursor.execute(f"DESCRIBE `{t_name}`;")
                    cols = cursor.fetchall()
                    
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM `{t_name}`;")
                        r_count = cursor.fetchone()[0]
                    except Exception:
                        r_count = 0

                    result["tables"].append({
                        "name": t_name,
                        "rowCount": r_count,
                        "columns": [
                            {"name": c[0], "type": c[1], "nullable": c[2] == "YES"}
                            for c in cols
                        ]
                    })

            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error reading schema tree for {target_db}:", e)

        return result

    def get_schema_summary(self, db_name_override: Optional[str] = None) -> str:
        """Generates a text summary of the database schema for the LLM prompt."""
        tree = self.get_database_tree(db_name_override)
        db = tree["database"]
        engine_label = "PostgreSQL" if self.db_type == "postgres" else "MySQL"
        
        if not tree["tables"]:
            return f"Active Database ({engine_label}): `{db}` (0 tables present)."

        summary = [f"Active Database ({engine_label}): `{db}` with {len(tree['tables'])} table(s):"]
        for t in tree["tables"]:
            col_strs = [f"{c['name']} ({c['type']})" for c in t["columns"]]
            quote = '"' if self.db_type == "postgres" else "`"
            summary.append(f" - Table {quote}{t['name']}{quote} ({t['rowCount']} rows): [{', '.join(col_strs)}]")

        return "\n".join(summary)

    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Executes a SQL query against MySQL or PostgreSQL and returns formatted results."""
        clean_sql = sql_query.strip().rstrip(';') + ';'
        
        import time
        start_time = time.time()

        try:
            conn = self.get_connection()
            
            if self.db_type == "postgres":
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(clean_sql)
                exec_time = round((time.time() - start_time) * 1000, 2)

                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    raw_rows = cursor.fetchall()
                    rows = [dict(r) for r in raw_rows]
                    cursor.close()
                    conn.close()
                    return {
                        "success": True,
                        "is_select": True,
                        "columns": columns,
                        "rows": rows,
                        "affected_rows": len(rows),
                        "execution_time_ms": exec_time,
                        "error": None
                    }
                else:
                    affected = cursor.rowcount if cursor.rowcount >= 0 else 0
                    cursor.close()
                    conn.close()
                    return {
                        "success": True,
                        "is_select": False,
                        "columns": [],
                        "rows": [],
                        "affected_rows": affected,
                        "execution_time_ms": exec_time,
                        "error": None
                    }
            else:
                # MySQL
                cursor = conn.cursor(dictionary=True)
                cursor.execute(clean_sql)
                exec_time = round((time.time() - start_time) * 1000, 2)

                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    return {
                        "success": True,
                        "is_select": True,
                        "columns": columns,
                        "rows": rows,
                        "affected_rows": len(rows),
                        "execution_time_ms": exec_time,
                        "error": None
                    }
                else:
                    conn.commit()
                    affected = cursor.rowcount
                    cursor.close()
                    conn.close()
                    return {
                        "success": True,
                        "is_select": False,
                        "columns": [],
                        "rows": [],
                        "affected_rows": affected,
                        "execution_time_ms": exec_time,
                        "error": None
                    }
        except Exception as err:
            exec_time = round((time.time() - start_time) * 1000, 2)
            return {
                "success": False,
                "is_select": False,
                "columns": [],
                "rows": [],
                "affected_rows": 0,
                "execution_time_ms": exec_time,
                "error": str(err)
            }
