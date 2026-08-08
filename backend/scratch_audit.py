import json
from backend.db_manager import DBManager
from backend.agent.sql_agent import run_agent_query

def audit_system():
    print("=== STARTING FULL SYSTEM AUDIT ===")
    
    db_mgr = DBManager()
    
    # 1. Connection Test
    conn_res = db_mgr.test_connection()
    print(f"[1/6] Connection Test: status={conn_res['status']} ({conn_res['message']})")
    assert conn_res['status'] == 'success', "Connection failed!"

    # 2. Casual Chat / Intent Classifier Test
    res_chat = run_agent_query("hi hello how are you", db_mgr)
    print(f"[2/6] Casual Chat Test: op={res_chat['operation_type']}, sql={res_chat['sql']}")
    assert res_chat['operation_type'] == 'CHAT', "Casual chat was not classified as CHAT!"
    assert res_chat['sql'] is None, "Casual chat generated SQL unexpectedly!"

    # 3. Meta Queries (Databases count)
    res_meta_db = run_agent_query("how many databases do I have?", db_mgr)
    print(f"[3/6] Meta Query (Databases): response='{res_meta_db['response']}'")
    assert "database(s) available" in res_meta_db['response'] or "No databases" in res_meta_db['response']

    # 4. Table Ambiguity Query
    res_amb = run_agent_query("how many tables", db_mgr)
    print(f"[4/6] Ambiguity Query ('how many tables'): response='{res_amb['response']}'")
    assert "Which database would you like me to inspect" in res_amb['response']

    # 5. DDL Drop Database Test
    db_mgr.execute_query("CREATE DATABASE IF NOT EXISTS audit_temp_db;")
    res_drop = run_agent_query("can you delete the database audit_temp_db", db_mgr)
    print(f"[5/6] DDL Drop Database: sql={res_drop['sql']}, op={res_drop['operation_type']}")
    assert res_drop['sql'] == "DROP DATABASE `audit_temp_db`;", f"Expected DROP DATABASE, got {res_drop['sql']}"
    assert 'audit_temp_db' not in db_mgr.get_all_databases(), "Database was not dropped!"

    # 6. Read Query on school_management
    res_read = run_agent_query("show top 5 students by gpa in school_management", db_mgr)
    print(f"[6/6] Read Query: sql={res_read['sql']}, rows={len(res_read['rows'])}")
    assert res_read['sql'] is not None, "Failed to generate read query!"
    assert len(res_read['rows']) > 0, "No rows returned for students!"

    print("\n✅ ALL BACKEND & AGENT AUDIT TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    audit_system()
