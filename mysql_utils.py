import mysql.connector
import os
import uuid
import logging
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger('uvicorn.error')


def execute_query(sql: str, params: Optional[Tuple] = None, dictionary: bool = True, connection=None) -> Optional[List[Dict[str, Any]]]:
    """
    Execute a SELECT query with parameterized inputs to prevent SQL injection.
    
    Args:
        sql: SQL query with %s placeholders
        params: Tuple of parameters to bind to the query
        dictionary: Whether to return results as dictionaries
        connection: Optional existing connection to use
        
    Returns:
        List of dictionaries (if dictionary=True) or tuples, or None on error
    """
    standalone_connection = False
    if connection is None:
        connection = create_mysql_connection()
        standalone_connection = True
    
    cursor = connection.cursor(dictionary=dictionary)
    try:
        cursor.execute(sql, params or ())
        data = cursor.fetchall()
        return data
    except mysql.connector.Error as err:
        logger.error("Executing query failed!")
        logger.error(f"SQL:   {sql}")
        logger.error(f"Params: {params}")
        logger.error(f"Error: {err}")
        return None
    finally:
        cursor.close()
        if standalone_connection: 
            connection.close()


def execute_single_query(sql: str, params: Optional[Tuple] = None, connection=None) -> Optional[Dict[str, Any]]:
    """
    Execute a SELECT query that returns a single row with parameterized inputs.
    
    Args:
        sql: SQL query with %s placeholders
        params: Tuple of parameters to bind to the query
        connection: Optional existing connection to use
        
    Returns:
        Dictionary with the first result, or None if no results
    """
    result = execute_query(sql, params, dictionary=True, connection=connection)
    if isinstance(result, list) and len(result) > 0:
        return result[0]
    return None


def execute_modification_query(sql: str, params: Optional[Tuple] = None, connection=None) -> Optional[int]:
    """
    Execute an INSERT, UPDATE, or DELETE query with parameterized inputs.
    
    Args:
        sql: SQL query with %s placeholders
        params: Tuple of parameters to bind to the query
        connection: Optional existing connection to use
        
    Returns:
        Last inserted ID for INSERT queries, or number of affected rows
    """
    standalone_connection = False
    if connection is None:
        connection = create_mysql_connection()
        standalone_connection = True
    
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params or ())
        connection.commit()
        # For INSERT queries, return the last inserted ID
        # For UPDATE/DELETE queries, return the number of affected rows
        return cursor.lastrowid if cursor.lastrowid > 0 else cursor.rowcount
    except mysql.connector.Error as err:
        logger.error("Executing modification query failed!")
        logger.error(f"SQL:   {sql}")
        logger.error(f"Params: {params}")
        logger.error(f"Error: {err}")
        raise
    finally:
        cursor.close()
        if standalone_connection:
            connection.close()


def create_mysql_connection(host=None, port=None, user=None, password=None, database=None):
    """Creates and returns a connection to the database"""
    if host is None: 
        try: host = os.environ["DB_HOST"]
        except: host = "localhost"
    if port is None:
        try: port = os.environ["DB_PORT"]
        except: port = 3306
    if user is None:
        try: user = os.environ["DB_USER"]
        except: user = "root"
    if password is None: password = os.environ["DB_PASSWORD"]
    if database is None: database = os.environ["DB_NAME"]

    return mysql.connector.connect(host=host, user=user, password=password, database=database, port=port)


def generate_uuid(table_name, max_tries=1000, connection=None):
    """Generate a unique UUID for a table using secure parameterized queries"""
    uid = str(uuid.uuid4())
    response = execute_query("SELECT id FROM " + table_name + " WHERE id = %s", (uid,), connection=connection)
    tries = 0
    while (response and len(response) > 0 and tries < max_tries):
        uid = str(uuid.uuid4())
        response = execute_query("SELECT id FROM " + table_name + " WHERE id = %s", (uid,), connection=connection)
        tries += 1

    if tries == max_tries: 
        return None
    return uid