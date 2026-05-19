# ....
import os
import sys
from fastapi import FastAPI, Request
import mysql.connector
from colorama import Fore
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()
PASSWORD = os.getenv('PASSWORD')
DB_NAME = 'taskplaner'

mydb = mysql.connector.connect(
    host = 'localhost',
    username = 'root',
    password = PASSWORD
)
mycursor = mydb.cursor()
mycursor.execute('SHOW DATABASES')
DB_NAMES = [str(db).strip('(),\'') for db in mycursor]
if all(name != DB_NAME for name in DB_NAMES):
    print(f'{Fore.RED}There is no currently existing db called {DB_NAME} please either change the DB_NAME var or create a new database called {DB_NAME}.')
    print(Fore.RESET,end='')
    sys.exit()
mydb = mysql.connector.connect(
    host = 'localhost',
    username = 'root',
    password = PASSWORD,
    database = DB_NAME
)
mycursor = mydb.cursor()
print(f'{Fore.GREEN}Successfully connected to db {mydb}')
print(Fore.RESET,end='')

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/test")
def read_wuh():
    return {"Test": "test"}

@app.get('/api')
def links(request: Request):
    urls = [{'link':route.path,'name':route.name
             ,'clickable_link':f'<a href="{str(request.base_url).rstrip('/')}{route.path}">{route.path.lstrip('/')}</a>'
             }
               for route in app.routes]
    return urls

# SELECT FUNCTION 
@app.get("/{tableName}/select")
def read_table(tableName: str, pk: str | None = None):
    if pk is not None:
        query = f"SELECT * FROM {tableName} WHERE {tableName}.{tableName}ID = {pk}"
    else: 
        query = f"SELECT * FROM {tableName}"
    mycursor.execute(query)
    resp = mycursor.fetchall()
    result = reformat_response(resp,get_column_names(tableName))
    return result 

# DELETE FUNCTION
@app.get("/{tableName}/delete")
def read_table(tableName: str, pk: str | None = None):
    query = f"DELETE FROM {tableName} WHERE {tableName}.{tableName}ID = {pk}"
    mycursor.execute(query)
    return 'Erfolgreich gelöscht'

# INSERT FUNCTION
@app.get("/{tableName}/insert")

def read_table(tableName: str, pk: str | None = None):
    query = f"INSERT INTO {tableName} VALUES ({pk})"
    mycursor.execute(query)
    mycursor.fetchall()
    return '' 

# UPDATE FUNCTION
@app.get("/{tableName}/update")
def read_table(tableName: str, attribut: str | None = None, pk: str | None = None, value: str | None = None):
    if attribut is not None and pk is not None and value is not None:
        print(get_column_datatype(tableName, attribut))
        match get_column_datatype(tableName, attribut):
            case 'int':
                query = f"UPDATE {tableName} SET {attribut} = {value} WHERE {tableName}ID = {pk}"
            case "datetime":
                query = f"UPDATE {tableName} SET {attribut} = \"{value}\" WHERE {tableName}ID = {pk}"
            case "varchar(255)","varchar(100)", "TEXT":
                query = f"UPDATE {tableName} SET {attribut} = \"{value}\" WHERE {tableName}ID = {pk}"
            case "boolean":
                query = f"UPDATE {tableName} SET {attribut} = {value} WHERE {tableName}ID = {pk}"
            case "BLOB":
                return "BLOB values cannot be updated via this endpoint"
            case "None":
                return "error"
        mycursor.execute(query)
        mycursor.fetchall()
        return 'Erfolgreich aktualisiert'
    else:
        return 'Aktualisierung fehlgeschlagen, sie müssen alle drei Parameter (attribut, pk, value) angeben'
# Helper functions

def get_column_datatype(table_name, column_name):
    query = f"SHOW COLUMNS FROM {table_name}"
    mycursor.execute(query)
    columns = mycursor.fetchall()
    for column in columns:
        if column[0] == column_name:
            return column[1]


def get_column_names(table_name):
    query = "SHOW COLUMNS FROM %s" % table_name
    mycursor.execute(query)
    columns = mycursor.fetchall()
    column_names = []
    for column in columns:
        column_names.append(column[0])
    return column_names

def reformat_response(response, column_names):
    result = []
    for record in response:
       record_dict = {}
       for i in range(len(record)):
           record_dict[column_names[i]] = record[i]
       result.append(record_dict)     
    return result
