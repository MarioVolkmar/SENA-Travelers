import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.database = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")

    def get_connection(self):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )

            if connection.is_connected():
                return connection

        except Error as error:
            print(f"Error connecting to MySQL: {error}")
            return None

    def test_connection(self):
        connection = self.get_connection()

        if connection is None:
            return False

        connection.close()
        return True