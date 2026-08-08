import re
import difflib

def is_destructive_query(sql: str) -> bool:
    """
    Determines if a SQL query is destructive or irreversible.
    Requires explicit user confirmation before executing:
    - DROP (database, table, column, index)
    - TRUNCATE
    - REVOKE
    - DELETE without WHERE clause (or any mass DELETE)
    - UPDATE without WHERE clause
    - ALTER containing DROP
    """
    if not sql:
        return False

    clean_sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE).strip()
    upper = clean_sql.upper()

    # 1. Direct DDL & DCL destructive commands
    if any(upper.startswith(cmd) for cmd in ['DROP', 'TRUNCATE', 'REVOKE']):
        return True

    if 'ALTER TABLE' in upper and 'DROP' in upper:
        return True

    # 2. DELETE without WHERE clause or ALL rows deletion
    if upper.startswith('DELETE'):
        if 'WHERE' not in upper:
            return True
        # Check if WHERE is a trivial true clause like WHERE 1=1 or WHERE true
        if re.search(r'WHERE\s+(1\s*=\s*1|TRUE)\b', upper):
            return True
        return True # Confirm all DELETE commands for maximum safety

    # 3. UPDATE without WHERE clause
    if upper.startswith('UPDATE'):
        if 'WHERE' not in upper or re.search(r'WHERE\s+(1\s*=\s*1|TRUE)\b', upper):
            return True

    return False


def format_actionable_error(error_str: str, sql: str, db_manager) -> dict:
    """
    Parses MySQL error output into user-friendly, actionable feedback with clear next steps.
    """
    err_lower = error_str.lower()
    
    # 1. Permission Denied Error (MySQL 1142, 1044, 1045)
    if 'access denied' in err_lower or 'command denied' in err_lower or '1142' in error_str or '1044' in error_str:
        user = db_manager.user or 'current user'
        return {
            "message": (
                f"🚫 **Permission Denied**: Your MySQL user (`{user}`) does not have the required privileges to execute this command.\n\n"
                f"**Attempted SQL:**\n```sql\n{sql}\n```\n\n"
                f"💡 **Next Step:** You may need an admin to run `GRANT` privileges for your user. Would you like to try a different query or switch MySQL credentials?"
            ),
            "auth_required": False
        }

    # 2. Unknown Table / Column Error (MySQL 1146, 1054)
    if "doesn't exist" in err_lower or "unknown column" in err_lower or '1146' in error_str or '1054' in error_str:
        # Extract missing identifier
        missing_item = None
        m_tbl = re.search(r"table ['`\"]?([^'\"`]+)['`\"]? doesn't exist", error_str, re.IGNORECASE)
        m_col = re.search(r"unknown column ['`\"]?([^'\"`]+)['`\"]?", error_str, re.IGNORECASE)
        
        if m_tbl:
            missing_item = m_tbl.group(1)
            db_tree = db_manager.get_database_tree()
            available_tables = [t['name'] for t in db_tree.get('tables', [])]
            closest = difflib.get_close_matches(missing_item, available_tables, n=3, cutoff=0.3)
            suggestions = ", ".join([f"`{c}`" for c in closest]) if closest else ", ".join([f"`{t}`" for t in available_tables[:5]])
            return {
                "message": (
                    f"❓ **Unknown Table**: There is no table named `{missing_item}` in database `{db_manager.database}`.\n\n"
                    f"💡 **Did you mean one of these tables?** {suggestions}\n\n"
                    f"Would you like me to query one of those tables instead?"
                ),
                "auth_required": False
            }
        elif m_col:
            missing_item = m_col.group(1)
            return {
                "message": (
                    f"❓ **Unknown Column**: The column `{missing_item}` was not found in the target table.\n\n"
                    f"💡 **Next Step:** Please check your column spelling or ask me: *'What columns are in this table?'*"
                ),
                "auth_required": False
            }

    # 3. Syntax Error (MySQL 1064)
    if 'syntax error' in err_lower or '1064' in error_str or 'right syntax to use near' in err_lower:
        near_match = re.search(r"near ['`\"]?([^'\"]+)['`\"]?", error_str, re.IGNORECASE)
        near_text = near_match.group(1) if near_match else "the end of query"
        return {
            "message": (
                f"⚠️ **SQL Syntax Issue**: The query has a syntax issue near `{near_text}`.\n\n"
                f"**Generated SQL:**\n```sql\n{sql}\n```\n\n"
                f"💡 **Next Step:** Would you like me to fix the syntax and retry the query for you?"
            ),
            "auth_required": False
        }

    # 4. Constraint Violations (Foreign Key 1451/1452, Unique 1062, NOT NULL 1048)
    if 'foreign key constraint fails' in err_lower or '1451' in error_str or '1452' in error_str:
        return {
            "message": (
                f"🔗 **Foreign Key Constraint Failed**: Cannot insert or delete this record because it is referenced by another table.\n\n"
                f"💡 **Next Step:** Make sure the referenced parent ID exists, or delete dependent child records first. Would you like me to check the related parent records?"
            ),
            "auth_required": False
        }

    if 'duplicate entry' in err_lower or '1062' in error_str:
        dup_val = re.search(r"duplicate entry ['`\"]?([^'\"]+)['`\"]?", error_str, re.IGNORECASE)
        val_str = f" for `{dup_val.group(1)}`" if dup_val else ""
        return {
            "message": (
                f"🚫 **Duplicate Value Error**: A record with this unique key{val_str} already exists.\n\n"
                f"💡 **Next Step:** Use a different primary key/unique value or run an `UPDATE` command instead. Would you like me to perform an update?"
            ),
            "auth_required": False
        }

    if "cannot be null" in err_lower or '1048' in error_str:
        null_col = re.search(r"column ['`\"]?([^'\"]+)['`\"]? cannot be null", error_str, re.IGNORECASE)
        col_str = f" for column `{null_col.group(1)}`" if null_col else ""
        return {
            "message": (
                f"⚠️ **Missing Required Value**: A required field{col_str} was left empty.\n\n"
                f"💡 **Next Step:** Please provide a value for all required columns and try again."
            ),
            "auth_required": False
        }

    # 5. Connection / Auth Failures (MySQL 2003, 1045)
    if 'can\'t connect' in err_lower or '2003' in error_str or '1045' in error_str:
        return {
            "message": (
                f"🔌 **Database Connection Error**: Lost connection to your MySQL server.\n\n"
                f"💡 **Next Step:** Please verify your MySQL server is running and re-authenticate with your password."
            ),
            "auth_required": True
        }

    # Generic Fallback Error
    return {
        "message": (
            f"❌ **Database Error**: {error_str}\n\n"
            f"**Attempted Query:**\n```sql\n{sql}\n```\n\n"
            f"💡 **Next Step:** Please check your input or ask me to list the available database tables to try again."
        ),
        "auth_required": False
    }
