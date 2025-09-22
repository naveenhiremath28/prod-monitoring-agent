class IssueQueries:
    GET_ALL_ISSUES = """
        SELECT id, title, description, analysis, issue_logs,
            application_type, occurrence, status,
            severity, error_type,
            created_at, updated_at
        FROM issues
        ORDER BY created_at DESC;
    """

    GET_ISSUE_BY_ID = """
        SELECT id, title, description, analysis, issue_logs,
            application_type, occurrence, status,
            severity, error_type,
            created_at, updated_at
        FROM issues
        WHERE id = :issue_id;
    """

    CREATE_ISSUE = """
        INSERT INTO issues (
            id, title, description, analysis, issue_logs, application_type,
            occurrence, status, severity, error_type,
            created_at, updated_at
        ) VALUES (
            :id,:title, :description, :analysis, :issue_logs, :application_type,
            :occurrence, :status, :severity, :error_type,
            now(), now()
        )
        RETURNING id, title, description, analysis, issue_logs, application_type,
                occurrence, status, severity, error_type,
                created_at, updated_at;
    """

    UPDATE_ISSUE = """
        UPDATE issues
        SET occurrence = :occurrence,
            issue_logs = :issue_logs,
            updated_at = :updated_at
        WHERE id = :issue_id
        RETURNING id, title, description, occurrence, issue_logs, created_at, updated_at;
    """

    DELETE_ISSUE = """
        DELETE FROM issues
        WHERE id = :issue_id;
    """

    GET_ISSUE_BY_TITLE = """
        SELECT id, title, description, analysis, issue_logs,
            application_type, occurrence, status,
            severity, error_type,
            created_at, updated_at
        FROM issues
        WHERE title = :title;
    """