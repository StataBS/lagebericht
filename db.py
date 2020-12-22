import numpy as np
import pandas as pd
import const
import streamlit as st
import pyodbc 
import sqlalchemy
import urllib

def append_pd_table(df, table_name, fields):
    try:
        params = urllib.parse.quote_plus(get_conn_string(const.SERVER, const.DATABASE))   
        engine = sqlalchemy.create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
        if fields!=[]:
            df = df[fields]
        df.to_sql(table_name, engine, if_exists='replace')
        return 1
    except Exception as ex:
        print(ex)
        return 0

def get_conn_string(srv: str, db_name: str) -> str:
    return f"Driver={{SQL Server}};Server={srv};Database={db_name};Trusted_Connection=yes;Timeout=600"


def get_connection(srv:str, db_name:str):
    """Generates the connection string using the specified server and database name"""

    connection_string = get_conn_string(srv, db_name)
    return pyodbc.connect(connection_string)


def get_server_name(conn: object) -> str:
    """Returns the username for the current user"""

    qry = const.SERVER_NAME
    return get_recordset(conn, qry)['server_name'][0]

def get_user_kuerzel(con: object)->str:
    """Gibt den User-Kürzel des Windows-Login zurück, z.b bs\ssscal"""

    qry = const.USER_LOGIN
    return get_recordset(conn, qry)['login'][0]


def get_user_info(conn: object, login: str) -> dict:
    """
    Gibt die wichtigsten User Attribute des current user zurück. Connection muss die Datenbank stata_produkte 
    enthalten
    """

    qry = const.USER_INFO.format(login)
    result = get_recordset(conn, qry).to_dict()

    return result


def get_sql_expr(value, is_string):
    """
    converts a value into a valid sql expression that can be used in an update statement
    None > Null
    Hans > 'Hans'
    50 > 50  
    """

    result = ''
    if value in (None, 'None'):
        result = 'Null'
    elif value in ('True','False'):
        result = 0 if value == 'False' else 1
    else:
        if is_string:
            value = value.replace("'", "''")
            result = f"'{value}'"
        else:
            result = value
    return result


def get_recordset(conn: object, query: str) -> pd.DataFrame:
    """Returns a list of databases given a specified connection"""
    
    cursor = conn.cursor()
    result = pd.read_sql_query(query, conn)
    return result


def exec_non_query(conn: object, cmd: str) -> int:
    """executes a command on the database"""

    result = 0
    try:
        cursor = conn.cursor()
        cursor.execute(cmd)

        print(cmd)
        conn.commit()
        result = 1
    except Exception as ex:
        print(ex)
        conn.rollback()
        result = 0
    return result

def get_value(conn: object, query: str) -> str:
    """
    return a single value for a specified query
    """
    result = pd.DataFrame()
    try:
        cursor = conn.cursor()
        result = pd.read_sql_query(query, conn)
    except Exception as ex:
        print(ex)

    if len(result) > 0:
        return result['result'][0]
    else:
        return None


def get_db_value(value: str, type: int):
    result = ''
    if type == 1:
        result = f"'{value}'"
    elif type == 2:
        result = 'Null' if value in ('None','') else value
    elif type == 3:
        result = 'Null' if value in ('None','') else value.replace(',','.')
    return result