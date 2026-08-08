from backend.db_manager import DBManager
from backend.agent.sql_agent import run_agent_query
from backend.agent.query_safety import is_destructive_query, format_actionable_error

def test_requirements():
    print("=== TESTING REQUIREMENTS 1 - 5 ===")
    db_mgr = DBManager()

    # 1. Test Confirmation Gate
    sql_dest = "DROP DATABASE `test_drop_db`;"
    assert is_destructive_query(sql_dest) == True, "DROP DATABASE should be destructive!"
    assert is_destructive_query("SELECT * FROM students;") == False, "SELECT should not be destructive!"
    print("[PASS] Req 3: Confirmation Gate classification works!")

    # 2. Test Destructive Command Gate Response (without confirmation)
    db_mgr.execute_query("CREATE DATABASE IF NOT EXISTS test_drop_db;")
    res_dest = run_agent_query("delete database test_drop_db", db_mgr)
    print(f"Req 3 Gate Response: requires_confirmation={res_dest['requires_confirmation']}")
    assert res_dest['requires_confirmation'] == True, "Destructive query must require confirmation!"
    assert 'test_drop_db' in db_mgr.get_all_databases(), "Database should NOT be dropped before confirmation!"

    # 3. Test Confirming Destructive Action
    res_confirmed = run_agent_query("yes", db_mgr, confirmed=True, pending_sql="DROP DATABASE `test_drop_db`;")
    clean_resp = res_confirmed['response'].encode('ascii', 'ignore').decode('ascii')
    print(f"Req 3 Confirmed Response: response='{clean_resp}'")
    assert 'test_drop_db' not in db_mgr.get_all_databases(), "Database should be dropped after confirmation!"
    print("[PASS] Req 3: Confirmation Gate execution works!")

    # 4. Test Actionable Error Handling (Unknown Table)
    err_info = format_actionable_error("Table 'school_management.non_existent_table' doesn't exist", "SELECT * FROM non_existent_table;", db_mgr)
    clean_msg = err_info['message'].encode('ascii', 'ignore').decode('ascii')
    print(f"Req 4 Error Response: {clean_msg}")
    assert "Did you mean one of these tables?" in err_info['message'] or "Unknown Table" in err_info['message']
    print("[PASS] Req 4: Actionable Error formatting works!")

    # 5. Test Actionable Error Handling (Permission Denied)
    err_perm = format_actionable_error("1142 - DROP command denied to user 'root'@'localhost' for table 'foo'", "DROP TABLE foo;", db_mgr)
    assert "Permission Denied" in err_perm['message']
    assert "GRANT" in err_perm['message']
    print("[PASS] Req 5: Least-Privilege safety error works!")

    print("\nALL REQ 1-5 UNIT TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_requirements()
