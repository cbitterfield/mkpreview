import os
import sys
import sqlite3
from sqlite3 import Error

import datetime
from time import time
import time
from shutil import copyfile

# Globals
DEBUG=False
QUIET=False

# Tables
TABLE=dict()

class Database():
    '''
    Database class provides a higher level connector to SQLite3
    It provides methods for:

    Usage:
    myDB = Database('/tmp/filename.db')

    Methods:
    create()        : Creates a Database or tests existence of database
                    : Allows the database to be backed up if it exists.
    name()          : Returns the current database filename. Flag is true if the database exist
    connect()       : Connects this class to the initialized database
    close()         : Commits and Closes the current connection
    createTable()   : Creates a table from a dictionary and adds primary indexes
                    : Allows overwrite (drop the data in the table)
    insertORupdate(): Allows for an insert if not there and an update if there.
                    : Uses a dictionary. Checks dictionary against columns to avoid errors
    isTable()       : Returns True if the tables exists
    backupTable()   : Makes a copy of the table and renames it with a current timestamp
    dropTable()     : Remove all of the data from the table
    sqlExecute()    : Executes an arbitrary SQL Script against the open database.
    deleteData()    : removes database based on table and where.

    Variables:
    global DEBUG    : Used for output
    global QUIET    : User for output
    local message   : Return Message for all methods
    local data(dict): A dictionary for method use.
    local flag      : True / False for results of method
    self.database   : database name for all methods
    self.method     : calling method name
    self.class      : name of the class being called
    self.db_connect : name of the connection


    Returns:
    All methods return a [True | False] and a message
    If bad values are passed, it will fast fail and return a message.
    No further evaluations are made.

    '''
    global DEBUG
    global QUIET
    data = dict()
    flag = False
    message = ""

    def __init__(self,database):
        self.database = database
        self.class_name = self.__class__.__name__
        method = sys._getframe().f_code.co_name
        if not QUIET: print(
            "{class_name}:{method}:initialized database:{database}".format(method=method, class_name=self.class_name,
                                                                           database=database))
        return None

    def __enter__(self):
        self.connect()

    def __exit__(self):
        self.close()

    def name(self,**kwargs):
        '''
        PARAMS:
        -------
        None

        RETURN
        -----
            FLAG = True if the file exists / False if not
            MESSAGE = database name

        '''
        method = sys._getframe().f_code.co_name
        message = self.database
        flag = True
        if DEBUG: print('Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method, args=kwargs))

        if os.path.isfile(self.database):
            flag=True
        else:
            flag=False
        if DEBUG: print("Database file exists {}".format(flag))
        if not QUIET: print("Database {}".format(message))
        return flag, message

    def create(self,**kwargs):
        '''PARAMS:
        -------
        overwrite = [True | False]
        backup = [True | False]

        If database exists, with overwrite FALSE and backup FALSE, method exists with False
        If database does not exist it is created
        If database exists and overwrite without backup, it is deleted
        If database exists and backup is set, database will be backed up; regardless of overwrite.

        RETURN
        -----
            FLAG = True if a database is created, False if a database is not created.
            MESSAGE = database name + actions taken
        '''
        method = sys._getframe().f_code.co_name
        message = self.database + " "
        flag = True
        db_exists = False
        now = time.time()
        bak_name = ""
        modifier = time.strftime("%Y-%m-%d-%s", time.gmtime(now))
        overwrite = kwargs.get('overwrite',False)
        backup = kwargs.get('backup',True)

        if DEBUG: print('Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method, args=kwargs))

        db_exists = self.name()[0]

        if DEBUG and db_exists: print('Database {database} exists'.format(database=self.database))

        if backup:
            if DEBUG: print("Database backed up to filename is {}".format(bak_name))

            dir_name = os.path.dirname(self.database)
            base_name = os.path.basename(self.database)
            file_name, file_ext = base_name.rsplit('.', 1)
            bak_name = dir_name + "/" + file_name + "_" + modifier + "." + file_ext
            try:
                copyfile(self.database, bak_name)
                message += "- File was backed up"
            except IOError as e:
                message += "- Error file was not backed up {error}".format(error=e)
                return False, message

        if overwrite and db_exists:
                try:
                    os.remove(self.database)
                    message += "- database file deleted"

                except Error as e:
                    message += "- Error file was not deleted {error}".format(error=e)
                    return False, message

        self.connect()
        wal = "PRAGMA journal_mode=WAL;"
        cur = self.db_connect.cursor()
        cur.execute(wal)
        results = cur.fetchall()
        message += "- " + str(sqlite3.version) + ":" + str(results)
        if db_exists and not overwrite:
            message += "- Wal mode is enabled"
        else:
            message += "- New Database created with WAL mode enabled"
        self.db_connect.close()

        return flag, message

    def connect(self,**kwargs):
        '''connect class to database
        '''
        method = sys._getframe().f_code.co_name
        message = ""
        flag = True
        if DEBUG: print(
            'Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method,
                                                                        args=kwargs))

        try:
            self.db_connect = sqlite3.connect(self.database)
            flag = True

        except Error as e:
            print('connect_db Error {error}'.format(error=e))
            flag = False

        message = sqlite3.version
        if DEBUG: print('DB Creatate {message}'.format(message=message))

        return flag

    def close(self, **kwargs):
        '''Close the database connection
        '''
        method = sys._getframe().f_code.co_name
        message = ""
        flag = True
        if DEBUG: print(
            'Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method,
                                                                        args=kwargs))

        self.db_connect.commit()
        self.db_connect.close()
        if DEBUG: print('Database transactions commited and connection is closed')

    def commit(self,**kwargs):
        '''Close the database connection
        '''
        method = sys._getframe().f_code.co_name
        message = ""
        flag = True
        if DEBUG: print('Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method, args=kwargs))

        self.db_connect.commit()
        if DEBUG: print('Database transactions commited ')

    def createTable(self,**kwargs):
        '''create a table, optional drop if exists (default)
        If overwrite set to false, table will error if it exists
        '''
        method = sys._getframe().f_code.co_name
        message = ""
        flag = True
        if DEBUG: print('Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method, args=kwargs))

        table_name = kwargs.get('table',None)
        table_fields = kwargs.get('fields',None)
        overwrite = kwargs.get('overwrite',False)
        unique_fields = kwargs.get('unique',None)
        sql_statment=""

        if not table_name and not table_fields:
            return False, "Error wrong parameters"

        if self.isTable(table=table_name) and overwrite:
            c = self.db_connect.cursor()
            c.execute("""DROP TABLE `{TABLE}` ;   """.format(TABLE=table_name))

        elif self.isTable(table=table_name) and not overwrite:
            return True, 'Table Exists'

        if DEBUG: print('Table: {0} Fields: {1}'.format(table_name,table_fields))

        sql_start = "CREATE TABLE IF NOT EXISTS '{table_name}' (".format(table_name=table_name)
        sql_end = ");"
        sql_fields = " 'text',\n".join(table_fields)
        sql_statment += sql_start
        sql_statment += sql_fields
        sql_statment += sql_end

        if DEBUG: print('SQL: {0}'.format(sql_statment))
        try:
            c = self.db_connect.cursor()
            results = c.execute(sql_statment)
            self.db_connect.commit()

        except Error as e:
            message = 'Create Table Error {error}'.format(error=e)
            return False, message

        if unique_fields:
            sql_statement = ""
            # Create Unique indexes on these fields
            for unique in unique_fields:
                sql_statement += "CREATE UNIQUE INDEX `idx_{index}` ON `{table}` (`{index}`); ".format(table=table_name,
                                                                                                       index=unique)
            try:
                c.executescript(sql_statement)
            except:
                print('Failed: Index not added')

        return True, str(results)

    def insertORupdate(self,**kwargs):
        '''Insert a row or update the row with the field names in a dictionary
        parameters:
        -----------
        table = Table Name
        key_field = Field for initial update and where value
        key_value = Where Value
        data = Data to update


        '''
        method = sys._getframe().f_code.co_name
        message = ""
        flag = True
        if DEBUG: print('Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method, args=kwargs))

        header_row = list()
        table_name = kwargs.get('table', None)
        key_field = kwargs.get('key_field',None)
        key_value = kwargs.get('key_value', None)
        data = kwargs.get('data',None)

        if not table_name and not key_field and not key_value and not data:
            return False, 'Invalid arguments {}'.format(kwargs)

        # Build the header for all field names.
        sql_statement = "SELECT name FROM PRAGMA_TABLE_INFO('{TABLE}');".format(TABLE=table_name)
        if DEBUG: print(sql_statement)

        try:
            c = self.db_connect.cursor()
            c.execute(sql_statement)
            for field_header in c.fetchall():
                header_row.append(field_header[0])

            if DEBUG: print(header_row)

        except Error as e:
            message = 'Create Table Error {error}'.format(error=e)
            if DEBUG: print('Error {}'.format(message))
            return False, message

        # Insert or ignore the key field
        sql_statement = "INSERT or ignore INTO `{table}` (`{key_field}`) VALUES(?) ; ".format(table=table_name,
                                                                                              key_field=key_field)
        if DEBUG: print('Insert/Ignore SQL {}'.format(sql_statement))
        c = self.db_connect.cursor()
        results = c.execute(sql_statement, [key_value])
        if DEBUG: print(c.lastrowid)
        if results: self.db_connect.commit()

        # Update the previous row inserted
        sql_statement =""
        sql_list = list()
        sql_statement = "UPDATE `{TABLE}` SET \n".format(TABLE=table_name)
        for field in header_row:
            if data.get(field,None):
                sql_list.append("`{field}`='{value}'\n".format(field=field,value=data.get(field,None)))

        sql_statement += ", ".join(sql_list)
        sql_statement += " WHERE `{key_field}` like '%{key_value}%';".format(key_field=key_field,key_value=key_value)
        try:
            if DEBUG: print(sql_statement)
            c.execute(sql_statement)
        except Error as e:
            if DEBUG: print('Error {}'.format(e))

        return True, c.lastrowid

    def isTable(self,**kwargs):
        '''
        Test if table exists; if so return true
        '''
        method = sys._getframe().f_code.co_name
        message = ""
        flag = True
        if DEBUG: print('Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method, args=kwargs))

        table_name = kwargs.get('table', None)
        FLAG = False
        c = self.db_connect.cursor()
        c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{TABLE}' '''.format(TABLE=table_name))
        if c.fetchone()[0] == 1:
            FLAG = True
        else:
            FLAG = False
        return FLAG

    def backupTable(self,**kwargs):
        method = sys._getframe().f_code.co_name
        message = ""
        flag = True
        now = time.time()
        if DEBUG: print('Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method, args=kwargs))
        modifier = time.strftime("%Y-%m-%d-%s", time.gmtime(now))
        table_name = kwargs.get('table',None)
        table_back = table_name + "_" + modifier
        sql_statement = "CREATE TABLE `{table_back}` as SELECT * from `{table}`;".format(table_back=table_back,table=table_name)

        if DEBUG: print('{classname}:{method}:from{table} to:{table_back}'.
                        format(classname=self.class_name,
                               method=method,
                               table=table_name,
                               table_back=table_back
                              ))
        flag, message = self.sqlExecute(sql=sql_statement)

        return flag, message

    def sqlExecute(self,**kwargs):
        '''
        PARAMS:
        --------
        SQL     : SQL Statement (no expansion)

        RETURNS:
        ---------

        flag    : True / False
        results : SQL Results

        '''
        method = sys._getframe().f_code.co_name
        message = ""
        flag = True
        sql_statement = kwargs.get('sql', None)

        if DEBUG: print('Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method, args=kwargs))

        if not sql_statement:
            flag = False
            message = "SQL Statement missing"
        else:
            try:
                c = self.db_connect.cursor()
                c.executescript(sql_statement)
                self.db_connect.commit()
                message = c.fetchall()
            except Error as e:
                print('Failed: {}'.format(e))

        if DEBUG: print('SQL executed {flag} statement: {sql}'.format(flag=flag,sql=sql_statement))

        return flag,message

    def deleteData(self,**kwargs):
        method = sys._getframe().f_code.co_name
        message = ""
        flag = True
        if DEBUG: print(
            'Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method,
                                                                        args=kwargs))
        table_name = kwargs.get('table', None)
        key_field = kwargs.get('key_field', None)
        key_value = kwargs.get('key_value', None)

        sql_statement = "DELETE FROM `{TABLE}` WHERE {KEY} is like '%{VALUE}%';"
        if DEBUG: print('SQL statement: {sql}'.format(flag=flag, sql=sql_statement))
        flag, message = self.sqlExecute(sql_statement)

        return flag, message

    def truncateTable(self, **kwargs):
        '''truncates the table using delete
        table='Table Name'
        '''
        method = sys._getframe().f_code.co_name
        message = ""
        table_name = kwargs.get('table', None)
        flag = True
        if DEBUG: print(
            'Class {classname} Method {method} Arguments {args}'.format(classname=self.class_name, method=method,
                                                                        args=kwargs))
        sql_statement = "DELETE FROM `{TABLE}`;".format(TABLE=table_name)
        flag, message = self.sqlExecute(sql=sql_statement)

        return flag, message
