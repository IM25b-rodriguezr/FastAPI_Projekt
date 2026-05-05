# ....
import os
import sys
from fastapi import FastAPI, Request
import mysql.connector
from colorama import Fore    
app = FastAPI()
PASSWORD = os.getenv('PASWORD')
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

import mysql.connector

