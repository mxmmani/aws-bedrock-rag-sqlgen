import pyodbc
import boto3
import json

def get_secret():
    secret_name = "awsdatabasemxmsec"  
    region_name = "us-east-1"   

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        # Handle the error according to your needs
        raise e

    # Decode and return the secret JSON string
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

def run_query(query):
    try:
        # Fetch database connection details from Secrets Manager
        secret = get_secret()
        server = secret['host']
        database = secret['database']
        username = secret['username']
        password = secret['password']

        # Set up the connection string for MSSQL
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        conn = pyodbc.connect(conn_str)
        
        print('\n<mssql_helper> Query to be Executed: ')
        print(query)
        
        with conn:
            cur = conn.cursor()
            cur.execute(query)
            
            # Fetch column names
            column_names = [col[0] for col in cur.description]
            print('\n<mssql_helper> Column Names: ')
            print(column_names)

            # Fetch all rows
            rows = cur.fetchall()
            
            print('\n<mssql_helper> Rows: ')
            print(rows)
            
            # Format rows: Each row is a tuple of values
            formatted_rows = [tuple(row) for row in rows]
            print('\n<mssql_helper> Formattes Rows: ')
            print(formatted_rows)

            return "success", column_names, formatted_rows

    except Exception as e:
        print('\n<mssql_helper> Exception: ')
        print(str(e))
        return "fail", [], str(e)
