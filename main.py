"""Is the main file and contains all the routes and logic separated by commented text.
"""
import os
import sys
from fastapi import FastAPI, Request
import mysql.connector
from colorama import Fore    
from dotenv import load_dotenv
from difflib import SequenceMatcher
from fastapi.responses import FileResponse
import re
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
    """This returns the data displayed on the Home website.

    Returns:
        dict: The data displayed when the website gets called.
    """
    return {"Welcome to our Website": "This is the root endpoint. Please use /api to see all available endpoints."}

@app.get('/api')
def links(request: Request):
    """This returns all the links of the current app.

    Args:
        request (Request): The request that called the website.

    Returns:
        List[Dict[str,str]] : The data displayed when the website gets called.
    """
    urls = [{'link':route.path,'name':route.name
             ,'clickable_link':f'<a href="{str(request.base_url).rstrip('/')}{route.path}">{route.path.lstrip('/')}</a>'
             }
               for route in app.routes]
    return urls

# SELECT FUNCTION 
@app.get("/{tableName}/select")
def read_table(tableName: str, pk: int | None = None):
    """Returns the data of the given table. If a primary key is given it returns only the data with that pk else everything from that table.

    Args:
        tableName (str): The table name the data is wanted from.
        pk (int | None, optional): The primary key to filter the results with. Defaults to None.

    Returns:
        List[Dict[str, Any]]: The selected data.
    """
    if pk is not None:
        query = f"SELECT * FROM {tableName} WHERE {tableName}.{tableName}ID = {pk}"
        mycursor.execute(query)
        resp = mycursor.fetchall()
    else: 
        query = f"SELECT * FROM {tableName}"
        mycursor.execute(query)
        resp = mycursor.fetchall()
    
    print(query)
    result = reformat_response(resp,get_column_names(tableName))
    return result 


# DELETE FUNCTION
@app.get('/{tableName}/{pk}/delete')
def delete(tableName:str, pk: int):
    """This command executes a SQL command that deletes everything in the given table matching the given pk.

    Args:
        tableName (str): The table to delete from.
        pk (int): The pk to filter what's getting deleted.

    Returns:
        str : A string containing if the command was successful or what was wrong.
    """
    mycursor.execute('SHOW TABLES')
    table_names = [name[0].upper() for name in mycursor]
    if tableName.upper() not in table_names:
        return INVALID_TABLE_MSG.format(tableName)
    query = f'DELETE FROM {tableName} WHERE {tableName}.{tableName}ID = {pk}'
    mycursor.execute(query)
    mydb.commit()

    return "Erfolgreich gelöscht"

# UPDATE FUNCTION
@app.get('/{tableName}({pk}/update')
def process_cmd(tableName:str, pk: int, attribute_name : str | None =  None, value = None):
    """This command executes a SQL command that updates everything in the given table matching the given pk and attribute name with the given values.

    Args:
        tableName (str): The table to update in.
        pk (int): The primary key to match.
        attribute_name (str | None, optional): The attribute to match. Defaults to None.
        value (Any, optional): The values to update to. Defaults to None.

    Returns:
        str : A string containing if the command was successful or what was wrong.
    """
    everything_correct = checks(table_name=tableName,pk =pk,attribute_name=attribute_name,values=value)
    if isinstance(everything_correct,str):
        return everything_correct
    cmd = f'UPDATE {tableName} SET {tableName}.{attribute_name} = %s where {tableName}.{tableName}ID = {pk}'
    mycursor.execute(cmd,(value,))
    mydb.commit()
    return "Erfolgreich aktualisiert"
    
@app.get('/{tableName}/insert')
def insert_cmd(tableName: str , values: str = None):
    """This command executes a SQL command that inserts the given values into the given table.

    Args:
        tableName (str): The table to insert into.
        values (str, optional): The values to insert. Defaults to None.

    Returns:
       str | List[str] : A string containing if the command was successful or what was wrong. If SQL raised warnings on command execution these will be returned in form of a list.
    """
    if not values:
        return MISSING_ARGS_MSG.format(*['values']*2)
    values_list = [value.strip('()') for value in values.split(',')]
    everything_correct = checks(table_name=tableName,needs_attribute_name = False,values=values,needs_pk=False)
    if isinstance(everything_correct,str):
        return everything_correct
    if len(values.strip('()')) != len(values)-2:
        return 'You did not provide a valid values format. Please ensure that your values are surounded by ().'
    mycursor.execute(f'SHOW COLUMNS FROM {tableName}')
    existing_columns = sum(1 for column in mycursor)
    given_columns = len(values_list)
    if existing_columns != given_columns:
        return f'You did not provide the correct amount of columns. The given amount was {given_columns} the needed amount was {existing_columns}'
    cmd = f'INSERT IGNORE INTO {tableName} VALUES ({('%s,'*existing_columns).rstrip(',')})'
    mycursor.execute(cmd,tuple(values_list))
    if not mycursor.rowcount and mycursor.warnings:# if its 0
        return list(f'{warning[0]} {warning[1]}: {warning[2]}' for warning in mycursor.warnings)
        #'\n'.join(f'{warning[0]} {warning[1]}: {warning[2]}' for warning in mycursor.warnings) 
        # only use this if the browser supports \n correctly in a string
    mydb.commit()
    return "Erfolgreich eingefügt"


@app.get('/view/')
def read_view() -> list[dict[str]]:
    """Returns a preset SQL view.

    Returns:
        list[dict[str, Any]]: The data returned from the view.
    """
    mycursor.execute("""
    CREATE OR REPLACE VIEW Benutzeraufgaben AS
    SELECT BENUTZER.BENUTZERNAME, AUFGABE.TITEL, AUFGABE.ORT, AUFGABE.NOTIZ  
    FROM BENUTZER JOIN AUFGABE
	ON BENUTZER.BENUTZERID = AUFGABE.BENUTZERID;
    """)
    mydb.commit()
    mycursor.execute("""
    SELECT * FROM Benutzeraufgaben;
                    """)
    return reformat_response(mycursor.fetchall(),['Benutzername','Titel','Ort','Notiz'])

# Logic functions

def get_column_names(table_name:str) -> list[str]:
    """Returns a list containing all column names of the given table.

    Args:
        table_name (str): The table to get all column names from.

    Returns:
        List[str]: The list with all column names.
    """
    query = f"SHOW COLUMNS FROM {table_name}"
    mycursor.execute(query)
    columns = mycursor.fetchall()
    column_names = []
    for column in columns:
        column_names.append(column[0])
    return column_names

def reformat_response(response:list, column_names:list) -> list[dict[str]]:
    """Returns a list containing a dictionary with the keys being from column_names and the values being from response. 
    The keys and values will be paired depending on their position in the list.
    Example:
        The first object in the list column_names is the key for the first object in the list response.

    Args:
        response (list): The list of values.
        column_names (list): The list of keys.

    Returns:
        list[dict[str, Any]]: The keys and values paired.
    """
    result = []
    for record in response:
       record_dict = {}
       for i in range(len(record)):
           record_dict[column_names[i]] = record[i]
       result.append(record_dict)     
    return result

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    """Sets the website Icon.

    Returns:
        FileResponse: The file that is the website icon.
    """
    return FileResponse('bzz_icon.ico')

def checks(**kwargs) -> bool | str:
    """Checks the given parameters for all keyword arguments given and returns a corresponding error message if something is wrong with the data given.
    Example:
        Returns 'You did not provide a table name but a table name is required for this command to work.' if a table name was not explicitly marked as not needed, 
        and no table name was provided.

    Returns:
        bool | str: Either True if everything is correct with the given data or a string containing a message of what is wrong with the data.
    """
    table_name : str = kwargs.get('table_name')
    pk : int  = kwargs.get('pk')
    values = kwargs.get('values')
    attribute_name = kwargs.get('attribute_name')
    request : Request | None  =  kwargs.get('request')
    called_with : str = str(request.url) if request else ''
    ERROR_MSG = 'You did not provide a {} but a {} is required for this command to work.'
    NOT_VALID_ERROR_MSG = '{} is not a valid {}.'
    if kwargs.get(f'needs_table_name', True):
        if not table_name:
            return ERROR_MSG.format(*['table name']*2)
        mycursor.execute('SHOW TABLES')
        table_names = [name[0].upper() for name in mycursor]
        table_name = table_name.upper()
        if table_name not in table_names:
            best_match = return_nearest(table_name,table_names)
            needed = 'table_name'
            return f'{NOT_VALID_ERROR_MSG.format(table_name,'table name')}{f' Did you mean {best_match}? Fixed link: {re.sub(f'{needed}='+r'(\w|%27)*',f'{needed}={best_match}',called_with)}' if best_match and called_with else ''} '
    if kwargs.get(f'needs_attribute_name', True):
        if not attribute_name :
            return ERROR_MSG.format(*['attribute name']*2) 
        mycursor.execute(f'SHOW COLUMNS FROM {table_name}')
        attr_names = [attr[0].upper() for attr in mycursor]
        attribute_name = attribute_name.upper()
        if attribute_name not in attr_names:
            best_match = return_nearest(table_name,table_names)
            needed = 'attribute_name'
            return f'{NOT_VALID_ERROR_MSG.format(attribute_name,'attribute name')}{f' Did you mean {best_match}? Fixed link: {called_with.replace(f'{needed}={table_name}',f'{needed}={best_match}')}' if best_match and called_with else ''} '
    if not pk and kwargs.get(f'needs_pk', True):
        return ERROR_MSG.format(*['primary key']*2)
    if not values and kwargs.get(f'needs_values', True):
        return ERROR_MSG.format(*['values']*2)
    return True

def return_nearest(word:str, options:list[str]):
    """Returns the nearest match of the given string and all the strings in the given list.

    Args:
        word (str): The string to find the most similar to.
        options (list[str]): The list in which to find the most similar string.

    Returns:
        str | None: The best matching string or None if there was no good enough matching string.
    """
    best_match = None
    highest_ratio = 0.0
    for option in options:
        ratio = SequenceMatcher(None, word, option).ratio()
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = option
    return best_match if highest_ratio > 0.5 else None