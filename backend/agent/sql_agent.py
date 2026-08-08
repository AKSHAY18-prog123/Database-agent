import re
import json
from typing import Dict, Any, List, TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from backend.config import settings
from backend.db_manager import DBManager
from backend.agent.query_safety import is_destructive_query, format_actionable_error

# Helper to instantiate LLM supporting standard OpenAI & OpenRouter keys
def get_llm_instance(api_key: Optional[str] = None, temperature: float = 0.1):
    key = api_key or settings.OPENAI_API_KEY
    if not key:
        return None
    if key.startswith("sk-or-"):
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=key,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            temperature=temperature
        )
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        openai_api_key=key,
        temperature=temperature
    )

# Agent State Schema
class SQLAgentState(TypedDict):
    user_query: str
    openai_api_key: Optional[str]
    db_manager: DBManager
    schema_summary: str
    is_relevant: bool
    guardrail_message: Optional[str]
    generated_sql: Optional[str]
    operation_type: str  # READ, DML, DDL, DCL, TCL
    query_result: Optional[Dict[str, Any]]
    final_response: str
    requires_confirmation: Optional[bool]
    confirmed: Optional[bool]
    pending_sql: Optional[str]
    auth_required: Optional[bool]
    switched_database: Optional[str]

# Node 1: Intent Classifier & Guardrail Node
def guardrail_node(state: SQLAgentState) -> SQLAgentState:
    user_query = state['user_query'].strip()
    lower_query = user_query.lower()
    all_dbs = state['db_manager'].get_all_databases()
    
    # Check if user confirmed or cancelled a pending destructive query
    if state.get('confirmed') and state.get('pending_sql'):
        state['generated_sql'] = state['pending_sql']
        state['is_relevant'] = True
        return state

    if lower_query in ['no', 'cancel', 'stop', 'abort', "don't", 'dont', 'n']:
        if state.get('pending_sql'):
            state['is_relevant'] = True
            state['generated_sql'] = None
            state['operation_type'] = "CHAT"
            state['final_response'] = "🚫 **Operation Cancelled**: The destructive command was aborted and no changes were made to your database."
            return state

    # Top N Records / Data Natural Language Query Handler (e.g. "show top 10 records from exam")
    top_match = re.search(r'\b(?:show|print|display|view|get|list|fetch)\s+(?:top\s+(\d+)\s+)?(?:records|rows|data|items)?\s*(?:from|in|of)?\s+`?([a-zA-Z0-9_]+)`?', lower_query)
    if top_match and not any(lower_query.startswith(x) for x in ['show tables', 'show databases', 'show columns', 'show create', 'show status', 'show variables']):
        limit_val = top_match.group(1) or "10"
        tbl_name = top_match.group(2)
        if tbl_name and tbl_name not in ['tables', 'databases', 'dbs', 'columns', 'my', 'the', 'this', 'all']:
            state['is_relevant'] = True
            state['generated_sql'] = f"SELECT * FROM `{tbl_name}` LIMIT {limit_val};"
            state['operation_type'] = "READ"
            return state

    # Direct SQL Query Bypass (e.g. SELECT * FROM subscriptions LIMIT 50;)
    raw_sql_starts = ['select', 'insert', 'update', 'delete', 'create', 'drop', 'alter', 'grant', 'revoke', 'commit', 'rollback', 'describe', 'desc']
    is_raw_show = any(lower_query.startswith(x) for x in ['show tables', 'show databases', 'show columns', 'show create', 'show status', 'show variables', 'show grants', 'show index'])
    first_word = lower_query.split()[0] if lower_query.split() else ""
    if first_word in raw_sql_starts or is_raw_show:
        state['is_relevant'] = True
        state['generated_sql'] = user_query
        if first_word in ['select', 'describe', 'desc'] or is_raw_show:
            state['operation_type'] = "READ"
        elif first_word in ['insert', 'update', 'delete']:
            state['operation_type'] = "DML"
        else:
            state['operation_type'] = "DDL"
        return state

    # 1. Casual Chat / Greetings Handling
    casual_greetings = [
        'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening',
        'thanks', 'thank you', 'thx', 'who are you', 'what can you do', 'help', 'bye', 'goodbye'
    ]
    words = re.findall(r'\b\w+\b', lower_query)
    db_keywords = [
        'table', 'database', 'sql', 'query', 'show', 'list', 'select', 'student', 'teacher',
        'department', 'course', 'grade', 'count', 'create', 'insert', 'update', 'delete', 'drop',
        'alter', 'grant', 'revoke', 'commit', 'rollback', 'transaction', 'find', 'get', 'how many',
        'print', 'display', 'view', 'fetch', 'output', 'see', 'check', 'records', 'rows', 'data',
        'go', 'switch', 'use', 'change', 'open', 'connect', 'to'
    ]
    db_keywords.extend([db.lower() for db in all_dbs])

    # 1.5 Natural Language Database Switch Intent (e.g. "can you go to school_management", "switch to world")
    matched_db = next((db for db in all_dbs if db.lower() in lower_query), None)
    if matched_db and any(p in lower_query for p in ['go', 'switch', 'use', 'open', 'change', 'connect', 'select']):
        state['is_relevant'] = True
        state['generated_sql'] = f"USE `{matched_db}`;"
        state['operation_type'] = "READ"
        state['switched_database'] = matched_db
        state['final_response'] = f"✅ Switched active database to `{matched_db}`. I am now inspecting database `{matched_db}`."
        state['query_result'] = {
            "success": True,
            "is_select": True,
            "columns": ["Active_Database"],
            "rows": [{"Active_Database": matched_db}],
            "affected_rows": 0,
            "execution_time_ms": 1.0,
            "error": None
        }
        return state

    is_pure_casual = any(w in casual_greetings for w in words) and not any(k in lower_query for k in db_keywords)
    
    if is_pure_casual or lower_query in ['hi', 'hello', 'hey', 'thanks', 'thank you']:
        state['is_relevant'] = True
        state['generated_sql'] = None
        state['operation_type'] = "CHAT"
        if 'thank' in lower_query:
            state['final_response'] = "You're welcome! Let me know if you need anything else with your databases or tables."
        elif 'who are you' in lower_query or 'what can you do' in lower_query:
            state['final_response'] = "I am your AI SQL Assistant! I support all 4 SQL sub-languages (DDL, DML, DCL, TCL) to query, create, update, alter, or drop databases & tables."
        else:
            state['final_response'] = "Hi! How can I help you with your MySQL databases and tables today?"
        return state

    # 2. Meta Queries Handling (Databases list/count & Tables list/count)
    if bool(re.search(r'\b(database|databases|dbs)\b', lower_query)) and any(p in lower_query for p in ['how many', 'what', 'list', 'show', 'which', 'all']) and not any(k in lower_query for k in ['table', 'tables']):
        all_dbs = state['db_manager'].get_all_databases()
        state['is_relevant'] = True
        state['generated_sql'] = "SHOW DATABASES;"
        state['operation_type'] = "READ"
        
        if len(all_dbs) == 0:
            state['final_response'] = "No databases present on your MySQL server."
            state['query_result'] = {"success": True, "is_select": True, "columns": ["Database"], "rows": [], "affected_rows": 0, "execution_time_ms": 1.0, "error": None}
        else:
            db_list_str = ", ".join([f"`{db}`" for db in all_dbs])
            state['final_response'] = f"You have **{len(all_dbs)}** database(s) available: {db_list_str}."
            state['query_result'] = {
                "success": True,
                "is_select": True,
                "columns": ["Database"],
                "rows": [{"Database": db} for db in all_dbs],
                "affected_rows": len(all_dbs),
                "execution_time_ms": 1.0,
                "error": None
            }
        return state

    # 3. Ambiguity & Empty Table Check
    if any(k in lower_query for k in ['table', 'tables']) and any(p in lower_query for p in ['how many', 'list', 'show', 'what']):
        all_dbs = state['db_manager'].get_all_databases()
        if len(all_dbs) == 0:
            state['is_relevant'] = True
            state['generated_sql'] = None
            state['operation_type'] = "CHAT"
            state['final_response'] = "No databases present on your MySQL server."
            return state

        mentioned_db = next((db for db in all_dbs if db.lower() in lower_query), None)
        
        if not mentioned_db:
            db_opts = ", ".join([f"`{db}`" for db in all_dbs])
            state['is_relevant'] = True
            state['generated_sql'] = None
            state['operation_type'] = "CHAT"
            state['final_response'] = f"Which database would you like me to inspect for tables? Your available databases are: {db_opts}."
            return state
        else:
            tree = state['db_manager'].get_database_tree(mentioned_db)
            if len(tree.get('tables', [])) == 0:
                state['is_relevant'] = True
                state['generated_sql'] = f"SHOW TABLES FROM `{mentioned_db}`;";
                state['operation_type'] = "READ"
                state['final_response'] = f"No tables present in database `{mentioned_db}`."
                state['query_result'] = {"success": True, "is_select": True, "columns": [f"Tables_in_{mentioned_db}"], "rows": [], "affected_rows": 0, "execution_time_ms": 1.0, "error": None}
                return state

    # If query contains any database keyword, bypass off-topic classifier
    if any(k in lower_query for k in db_keywords):
        state['is_relevant'] = True
        return state

    # 4. Standard LLM Guardrail / Off-Topic Classifier
    llm = get_llm_instance(state.get('openai_api_key'), temperature=0.0)
    if llm:
        try:
            prompt = f"""
You are a strict Database Guardrail Classifier.
Determine if the user query is related to SQL databases, database schemas, tables, fields, querying data, inserting/updating/deleting data, DDL (create/alter/drop), DCL (grant/revoke), or TCL (commit/rollback).

Schema Context:
{state.get('schema_summary', '')}

User Query: "{user_query}"

Respond with ONLY a JSON object:
{{"is_relevant": true/false, "reason": "brief explanation if false"}}
"""
            res = llm.invoke([HumanMessage(content=prompt)])
            cleaned_res = res.content.strip()
            if "```json" in cleaned_res:
                cleaned_res = cleaned_res.split("```json")[1].split("```")[0].strip()
            parsed = json.loads(cleaned_res)
            
            is_relevant = parsed.get("is_relevant", True)
            if not is_relevant:
                state['is_relevant'] = False
                state['guardrail_message'] = (
                    "🚫 **Guardrail Triggered**: I am a specialized SQL Database Assistant. "
                    "I can only help you query, explore, create, alter, grant, or manipulate MySQL databases and tables. "
                    "Please ask a question related to your database!"
                )
                state['final_response'] = state['guardrail_message']
                return state
        except Exception as e:
            print("Guardrail LLM check error:", e)

    state['is_relevant'] = True
    return state

# Node 2: Schema Inspection Node
def schema_inspection_node(state: SQLAgentState) -> SQLAgentState:
    db_mgr = state['db_manager']
    state['schema_summary'] = db_mgr.get_schema_summary()
    return state

# Node 3: SQL Generator Node
def sql_generation_node(state: SQLAgentState) -> SQLAgentState:
    if not state.get('is_relevant') or state.get('operation_type') == 'CHAT' or state.get('query_result') is not None or state.get('generated_sql'):
        return state

    user_query = state['user_query']
    schema_summary = state['schema_summary']
    db_type = getattr(state['db_manager'], 'db_type', 'mysql')
    llm = get_llm_instance(state.get('openai_api_key'), temperature=0.1)

    if llm:
        try:
            engine_name = "PostgreSQL" if db_type == "postgres" else "MySQL"
            quote_char = '"' if db_type == "postgres" else "`"
            auto_inc = "SERIAL PRIMARY KEY" if db_type == "postgres" else "INT PRIMARY KEY AUTO_INCREMENT"
            
            system_prompt = f"""
You are an expert {engine_name} SQL Engineer supporting all 4 SQL sub-languages:
1. DDL (Data Definition Language): CREATE, ALTER, DROP, TRUNCATE (databases, tables, columns, indexes).
2. DML (Data Manipulation Language): SELECT, INSERT, UPDATE, DELETE.
3. DCL (Data Control Language): GRANT, REVOKE.
4. TCL (Transaction Control Language): COMMIT, ROLLBACK, SAVEPOINT, START TRANSACTION.

Current {engine_name} Database Schema:
{schema_summary}

Rules:
1. Return ONLY a valid JSON object with keys "sql" and "operation_type" ("READ", "DML", "DDL", "DCL", "TCL").
2. Ensure table and column names match the schema exactly using proper identifier quotes ({quote_char}table_name{quote_char}).
3. For natural language queries asking to create a table, alter a column, or drop a database/table, output proper DDL SQL using {engine_name} data types (e.g., {auto_inc}).
4. For natural language queries asking to insert, update, or delete data, output proper DML SQL.
5. For queries asking to grant/revoke permissions, output proper DCL SQL.
6. For queries asking for transaction control (start transaction, commit, rollback), output proper TCL SQL.
7. Do NOT write markdown prose outside the JSON.

Example outputs:
- {{"sql": "SELECT * FROM {quote_char}students{quote_char} WHERE {quote_char}gpa{quote_char} > 3.5 ORDER BY {quote_char}gpa{quote_char} DESC;", "operation_type": "DML"}}
- {{"sql": "CREATE TABLE {quote_char}library_books{quote_char} ({quote_char}book_id{quote_char} {auto_inc}, {quote_char}title{quote_char} VARCHAR(255));", "operation_type": "DDL"}}
- {{"sql": "START TRANSACTION;", "operation_type": "TCL"}}
"""
            res = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ])
            cleaned_res = res.content.strip()
            if "```json" in cleaned_res:
                cleaned_res = cleaned_res.split("```json")[1].split("```")[0].strip()
            elif "```sql" in cleaned_res:
                sql_str = cleaned_res.split("```sql")[1].split("```")[0].strip()
                cleaned_res = json.dumps({"sql": sql_str, "operation_type": "DML"})
            elif "```" in cleaned_res:
                sql_str = cleaned_res.split("```")[1].split("```")[0].strip()
                cleaned_res = json.dumps({"sql": sql_str, "operation_type": "DML"})
                
            parsed = json.loads(cleaned_res)
            sql = parsed.get("sql")
            op_type = parsed.get("operation_type", "DML")
            
            state['generated_sql'] = sql
            state['operation_type'] = op_type
            
            # Check destructive confirmation gate
            if is_destructive_query(sql) and not state.get('confirmed'):
                state['requires_confirmation'] = True
                state['pending_sql'] = sql
                state['final_response'] = (
                    f"⚠️ **Confirmation Required for Destructive Action**\n\n"
                    f"I generated the following **{op_type}** SQL statement:\n"
                    f"```sql\n{sql}\n```\n\n"
                    f"⚠️ *This operation will permanently alter or remove database structures or records.* Are you sure you want to execute it?"
                )
            return state
        except Exception as e:
            print("LLM generation error:", e)

    # Heuristic SQL generator fallback (when OpenAI key is missing or API errors)
    lower = user_query.lower()
    
    # 1. Drop / Delete Database queries
    if any(action in lower for action in ['delete', 'drop', 'remove', 'destroy']) and any(target in lower for target in ['database', 'db']):
        all_dbs = state['db_manager'].get_all_databases()
        matched_db = next((db for db in all_dbs if db.lower() in lower), None)
        if not matched_db:
            words = lower.split()
            for idx, w in enumerate(words):
                if w in ['database', 'db'] and idx + 1 < len(words):
                    matched_db = words[idx + 1].strip('`"\'.,;')
                    break
        if matched_db:
            sql = f"DROP DATABASE `{matched_db}`;"
            state['generated_sql'] = sql
            state['operation_type'] = "DDL"
            if not state.get('confirmed'):
                state['requires_confirmation'] = True
                state['pending_sql'] = sql
                state['final_response'] = (
                    f"⚠️ **Confirmation Required for Destructive Action**\n\n"
                    f"I generated the following **DDL** SQL statement:\n"
                    f"```sql\n{sql}\n```\n\n"
                    f"⚠️ *This action will permanently drop the entire database `{matched_db}`.* Are you sure you want to proceed?"
                )
            return state

    # 2. Drop / Delete Table queries
    if any(action in lower for action in ['delete', 'drop', 'remove', 'destroy', 'truncate']) and any(target in lower for target in ['table', 'tbl']):
        words = lower.split()
        matched_table = None
        for idx, w in enumerate(words):
            if w in ['table', 'tbl'] and idx + 1 < len(words):
                matched_table = words[idx + 1].strip('`"\'.,;')
                break
        if matched_table:
            sql = f"DROP TABLE `{matched_table}`;"
            state['generated_sql'] = sql
            state['operation_type'] = "DDL"
            if not state.get('confirmed'):
                state['requires_confirmation'] = True
                state['pending_sql'] = sql
                state['final_response'] = (
                    f"⚠️ **Confirmation Required for Destructive Action**\n\n"
                    f"I generated the following **DDL** SQL statement:\n"
                    f"```sql\n{sql}\n```\n\n"
                    f"⚠️ *This action will permanently drop table `{matched_table}`.* Are you sure you want to proceed?"
                )
            return state

    # 3. Print / Display / View table queries (e.g. "now print", "print", "display data")
    if any(k in lower for k in ['print', 'display', 'show data', 'see table', 'show table', 'view table']):
        tree = state['db_manager'].get_database_tree()
        tables = tree.get('tables', [])
        if tables:
            matched_t = next((t['name'] for t in tables if t['name'].lower() in lower), tables[0]['name'])
            state['generated_sql'] = f"SELECT * FROM `{matched_t}` LIMIT 50;"
            state['operation_type'] = "READ"
            return state

    # 4. TCL Commands (commit, rollback, start transaction)
    if 'commit' in lower:
        state['generated_sql'] = "COMMIT;"
        state['operation_type'] = "TCL"
        return state
    elif 'rollback' in lower:
        state['generated_sql'] = "ROLLBACK;"
        state['operation_type'] = "TCL"
        return state
    elif 'start transaction' in lower or 'begin transaction' in lower:
        state['generated_sql'] = "START TRANSACTION;"
        state['operation_type'] = "TCL"
        return state

    # 5. Read / Query Fallbacks
    if any(dept in lower for dept in ['physics', 'math', 'chemistry', 'computer science', 'literature', 'humanities']):
        dept_match = 'physics' if 'physics' in lower else ('computer' if 'computer' in lower or 'cs' in lower else ('math' if 'math' in lower else ('chemistry' if 'chemistry' in lower else 'literature')))
        state['generated_sql'] = f"SELECT s.first_name, s.last_name, s.email, s.gpa, d.department_name FROM `students` s JOIN `departments` d ON s.department_id = d.department_id WHERE d.department_name LIKE '%{dept_match}%';"
        state['operation_type'] = "READ"
    elif "student" in lower or "who" in lower or "people" in lower or "person" in lower:
        if "top" in lower or "highest gpa" in lower or "best" in lower:
            state['generated_sql'] = "SELECT * FROM `students` ORDER BY `gpa` DESC LIMIT 5;"
        elif "count" in lower or "how many" in lower:
            state['generated_sql'] = "SELECT COUNT(*) as total_students FROM `students`;"
        else:
            state['generated_sql'] = "SELECT s.student_id, s.first_name, s.last_name, s.email, s.gpa, d.department_name FROM `students` s LEFT JOIN `departments` d ON s.department_id = d.department_id LIMIT 50;"
        state['operation_type'] = "READ"
    elif "teacher" in lower or "faculty" in lower or "professor" in lower:
        state['generated_sql'] = "SELECT t.teacher_id, t.first_name, t.last_name, t.email, t.salary, d.department_name FROM `teachers` t LEFT JOIN `departments` d ON t.department_id = d.department_id;"
        state['operation_type'] = "READ"
    elif "department" in lower:
        state['generated_sql'] = "SELECT * FROM `departments`;"
        state['operation_type'] = "READ"
    elif "course" in lower:
        state['generated_sql'] = "SELECT c.course_code, c.course_name, c.credits, d.department_name FROM `courses` c LEFT JOIN `departments` d ON c.department_id = d.department_id;"
        state['operation_type'] = "READ"
    elif "grade" in lower or "score" in lower:
        state['generated_sql'] = "SELECT s.first_name, s.last_name, c.course_name, g.grade_letter, g.score, g.remarks FROM `grades` g JOIN `enrollments` e ON g.enrollment_id = e.enrollment_id JOIN `students` s ON e.student_id = s.student_id JOIN `courses` c ON e.course_id = c.course_id ORDER BY g.score DESC;"
        state['operation_type'] = "READ"
    elif "show tables" in lower or "list tables" in lower:
        state['generated_sql'] = "SHOW TABLES;"
        state['operation_type'] = "READ"
    else:
        state['generated_sql'] = "SHOW TABLES;"
        state['operation_type'] = "READ"
    
    return state

# Node 4: SQL Execution Node
def sql_execution_node(state: SQLAgentState) -> SQLAgentState:
    if not state.get('is_relevant') or state.get('operation_type') == 'CHAT' or state.get('query_result') is not None or not state.get('generated_sql'):
        return state

    # If confirmation is required and user has not confirmed, do not execute
    if state.get('requires_confirmation') and not state.get('confirmed'):
        return state

    db_mgr = state['db_manager']
    sql = state['generated_sql']
    
    try:
        result = db_mgr.execute_query(sql)
        state['query_result'] = result
        
        if not result.get('success'):
            err_info = format_actionable_error(result.get('error', 'Execution failed'), sql, db_mgr)
            state['final_response'] = err_info['message']
            state['auth_required'] = err_info.get('auth_required', False)
    except Exception as e:
        err_info = format_actionable_error(str(e), sql, db_mgr)
        state['final_response'] = err_info['message']
        state['auth_required'] = err_info.get('auth_required', False)

    return state

# Node 5: Response Synthesis Node
def response_synthesis_node(state: SQLAgentState) -> SQLAgentState:
    if not state.get('is_relevant') or state.get('operation_type') == 'CHAT':
        return state

    if state.get('requires_confirmation') and not state.get('confirmed'):
        return state

    if state.get('final_response') and ('No tables present' in state.get('final_response') or 'No databases present' in state.get('final_response') or 'Permission Denied' in state.get('final_response') or 'Unknown' in state.get('final_response') or 'Syntax Issue' in state.get('final_response')):
        return state

    user_query = state['user_query']
    sql = state.get('generated_sql', '')
    result = state.get('query_result') or {}
    llm = get_llm_instance(state.get('openai_api_key'), temperature=0.3)

    if not result.get('success') and state.get('final_response'):
        return state

    # If write, DDL, DCL, or TCL operation
    if not result.get('is_select'):
        op_name = state.get('operation_type', 'DATABASE')
        state['final_response'] = (
            f"✅ **{op_name} Command Executed Successfully!**\n\n"
            f"**Executed SQL:**\n```sql\n{sql}\n```\n\n"
            f"**Impact:** {result.get('affected_rows', 0)} row(s) affected / schema updated in database `{state['db_manager'].database}`."
        )
        return state

    rows = result.get('rows', [])
    columns = result.get('columns', [])
    
    if len(rows) == 0:
        if "SHOW TABLES" in sql.upper():
            state['final_response'] = "No tables present in database."
        elif "SHOW DATABASES" in sql.upper():
            state['final_response'] = "No databases present on your MySQL server."
        else:
            state['final_response'] = f"Executed SQL: `{sql}`\n\nNo records found matching your criteria."
        return state

    if llm:
        try:
            data_sample = json.dumps(rows[:10]) if rows else "No rows returned"
            prompt = f"""
You are a helpful AI Assistant for non-technical database users.
Synthesize a clear, concise answer in markdown format explaining the SQL query results to the user.

User Question: "{user_query}"
Executed SQL: `{sql}`
Total Rows Returned: {len(rows)}
Sample Data: {data_sample}

Guidelines:
1. Explain what the data shows clearly and conversationally.
2. Mention key numbers, averages, top performers, or specific insights found.
3. Keep it readable and brief. Do not print full ASCII tables as the UI will render a rich interactive table component automatically.
"""
            res = llm.invoke([HumanMessage(content=prompt)])
            state['final_response'] = res.content.strip()
            return state
        except Exception as e:
            print("Synthesis LLM error:", e)

    # Fallback explanation when no LLM key or LLM error
    state['final_response'] = f"Found **{len(rows)}** record(s) matching your request.\n\n**Executed SQL:**\n```sql\n{sql}\n```\n\nSee the interactive table below for the full dataset."
    return state


def build_sql_agent_graph():
    graph = StateGraph(SQLAgentState)

    graph.add_node("guardrail", guardrail_node)
    graph.add_node("schema_inspection", schema_inspection_node)
    graph.add_node("sql_generation", sql_generation_node)
    graph.add_node("sql_execution", sql_execution_node)
    graph.add_node("response_synthesis", response_synthesis_node)

    graph.set_entry_point("schema_inspection")
    graph.add_edge("schema_inspection", "guardrail")

    def check_guardrail(state: SQLAgentState):
        if not state.get('is_relevant'):
            return END
        return "sql_generation"

    graph.add_conditional_edges("guardrail", check_guardrail, {
        "sql_generation": "sql_generation",
        END: END
    })

    graph.add_edge("sql_generation", "sql_execution")
    graph.add_edge("sql_execution", "response_synthesis")
    graph.add_edge("response_synthesis", END)

    return graph.compile()

# Global Agent Runner Instance
sql_agent_app = build_sql_agent_graph()

def run_agent_query(
    user_query: str,
    db_manager: DBManager,
    openai_api_key: Optional[str] = None,
    confirmed: bool = False,
    pending_sql: Optional[str] = None
) -> Dict[str, Any]:
    
    # Check direct confirmation of pending query
    lower_q = user_query.strip().lower()
    if lower_q in ['yes', 'y', 'confirm', 'proceed', 'do it', 'run it', 'ok', 'sure'] or confirmed:
        confirmed = True

    initial_state = {
        "user_query": user_query,
        "openai_api_key": openai_api_key,
        "db_manager": db_manager,
        "schema_summary": "",
        "is_relevant": True,
        "guardrail_message": None,
        "generated_sql": pending_sql if confirmed else None,
        "operation_type": "READ",
        "query_result": None,
        "final_response": "",
        "requires_confirmation": False,
        "confirmed": confirmed,
        "pending_sql": pending_sql
    }

    final_state = sql_agent_app.invoke(initial_state)

    query_res = final_state.get('query_result') or {}
    return {
        "query": user_query,
        "is_relevant": final_state.get('is_relevant', True),
        "guardrail_message": final_state.get('guardrail_message'),
        "sql": final_state.get('generated_sql'),
        "operation_type": final_state.get('operation_type', 'READ'),
        "requires_confirmation": final_state.get('requires_confirmation', False),
        "pending_sql": final_state.get('pending_sql'),
        "columns": query_res.get('columns', []),
        "rows": query_res.get('rows', []),
        "affected_rows": query_res.get('affected_rows', 0),
        "execution_time_ms": query_res.get('execution_time_ms', 0),
        "response": final_state.get('final_response', ''),
        "error": query_res.get('error'),
        "auth_required": final_state.get('auth_required', False),
        "switched_database": final_state.get('switched_database')
    }
