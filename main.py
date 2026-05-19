import os
import sys
from fastapi import FastAPI, Request
import mysql.connector
from colorama import Fore    
from dotenv import load_dotenv
from fastapi.responses import FileResponse
load_dotenv()
app = FastAPI()
PASSWORD = os.getenv('PASSWORD')
DB_NAME = 'taskplaner'
NEEDS_VALUES = ['INSERT']
VALUES_NOT_NEEDED = ['UPTADE','DELETE']
OPTIONS = NEEDS_VALUES + VALUES_NOT_NEEDED

MISSING_ARGS_MSG = 'You did not provide a {} but a {} is required for this command to work.'
INVALID_TABLE_MSG = 'The table name {} is not a valid table'
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
    return {"Welcome to our Website": "This is the root endpoint. Please use /api to see all available endpoints."}

@app.get('/api')
def links(request: Request):
    urls = [{'link':route.path,'name':route.name
             ,'clickable_link':f'<a href="{str(request.base_url).rstrip('/')}{route.path}">{route.path.lstrip('/')}</a>'
             }
               for route in app.routes]
    return urls

# SELECT FUNCTION 
@app.get("/{tableName}/select")
def read_table(tableName: str, pk: int | None = None):
    if pk is not None:
        query = f"SELECT * FROM {tableName} WHERE {tableName}.{tableName}ID = {pk}"
        mycursor.execute(query)
        resp = mycursor.fetchall()
    else: 
        query = f"SELECT * FROM {tableName}"
        mycursor.execute(query)
        resp = mycursor.fetchall()
    
    
    result = reformat_response(resp,get_column_names(tableName))
    return result 

# DELETE FUNCTION
@app.get('/{tableName}/{pk}/delete')
def process_cmd(tableName:str, pk: int):
    mycursor.execute('SHOW TABLES')
    table_names = [name[0].upper() for name in mycursor]
    if tableName.upper() not in table_names:
        return INVALID_TABLE_MSG.format(tableName)
    query = f'DELETE FROM {tableName} WHERE {tableName}.{tableName}ID = {pk}'
    mycursor.execute(query)
    mydb.commit()

    return "Erfolgreich gelöscht"

# UPDATE FUNCTION
@app.get('/{tableName}/update')
def process_cmd(tableName:str, pk: int | None = None, attribute_name : str | None =  None, value = None):
    
    
    if not tableName:
        return MISSING_ARGS_MSG.format(*['table name']*2)
    mycursor.execute('SHOW TABLES')
    table_names = [name[0].upper() for name in mycursor]
    if tableName.upper() not in table_names:
        return INVALID_TABLE_MSG.format(tableName)
    if not attribute_name:
        return MISSING_ARGS_MSG.format(*['attribute name']*2) 
    if not pk:
        return MISSING_ARGS_MSG.format(*['primary key']*2)
    if not value:
        return MISSING_ARGS_MSG.format(*['values']*2)
    mycursor.execute(f'SHOW COLUMNS FROM {tableName}')
    attr_names = [attr[0].upper() for attr in mycursor]
    attributeName = attribute_name.upper()
    if attributeName not in attr_names:
        print(attr_names)
        return INVALID_TABLE_MSG.format(attribute_name,'attribute name')
    query = f'UPDATE {tableName} SET {tableName}.{attribute_name} = %s where {tableName}.{tableName}ID = {pk}'
    mycursor.execute(query,(value,))
    mydb.commit()

    return "Erfolgreich aktualisiert"
    

# Logic functions

def get_column_names(table_name):
    query = f"SHOW COLUMNS FROM {table_name}"
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

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('bzz_icon.ico')