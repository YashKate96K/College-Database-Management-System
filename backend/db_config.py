import os
import mysql.connector
from mysql.connector import pooling

DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', 'y@shkate96K')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'college_db')

pool = pooling.MySQLConnectionPool(
    pool_name = "cms_pool",
    pool_size = 5,
    host = DB_HOST,
    user = DB_USER,
    password = DB_PASS,
    database = DB_NAME
)

def get_connection():
    return pool.get_connection()
