import mysql.connector

import new


class DataHandler:
    """
    Custom class created with Mysql Connector for adding scraped data to database table
    :param host: Hostname of the MySQL database.
    :param user: Username for connecting to the MySQL database.
    :param password: Password for connecting to the MySQL database.
    :param database: Name of the database to connect.
    """
    def __init__(self, host, user, password, database):
        self.db_config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establish a connection to the MySQL database."""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            print("Connected to the database.")
        except mysql.connector.Error as error:
            print(f"Error connecting to database: {error}")

    def disconnect(self):
        """Close the connection to the MySQL database."""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("Database connection closed.")

    def drop_and_create_table(self, table_name):
        """
        Drop the table if it exists and create a new one.
        :param table_name:  Table Name in database to be Created.
        """
        try:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"Table '{table_name}' dropped.")
            create_query = f"""
                CREATE TABLE {table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    route VARCHAR(100),
                    url VARCHAR(255),
                    bus_id VARCHAR(255),
                    bus_type VARCHAR(50),
                    departure_time TIME,
                    duration VARCHAR(20),
                    arrival_time TIME,
                    rating FLOAT,
                    price DECIMAL(10, 2),
                    seats_available INT
                );
            """
            self.cursor.execute(create_query)
            print(f"Table '{table_name}' created.")
        except mysql.connector.Error as error:
            print(f"Error during table creation: {error}")

    def insert_data(self, table_name, data):
        """
        Insert data from a nested list into the specified table.
        :param table_name:  Table Name in database to be inserted.
        :param data:  Data to be inserted in Table.
        """

        try:
            insert_query = f"""
                INSERT INTO {table_name} (route, url, bus_id, bus_type, departure_time, duration, arrival_time, rating, 
                price, seats_available)
                VALUES (%s, %s, %s, %s, STR_TO_DATE(%s, '%H:%i'), %s, STR_TO_DATE(%s, '%H:%i'), %s, %s, %s)
            """
            self.cursor.executemany(insert_query, data)
            self.connection.commit()
            print("Data inserted successfully!")
        except mysql.connector.Error as error:
            print(f"Error inserting data: {error}")

    def add_scraped_data_to_database(self, table_name, data):
        """
        Custom method to add scraped data in Database using MYSQL Connector.
        :param table_name: Table Name in database to be added.
        :param data: Data to be inserted in Database.
        """
        self.connect()
        self.drop_and_create_table(table_name)
        self.insert_data(table_name, data)
        self.disconnect()


if __name__ == "__main__":
    # SQL database connection details
    db_manager = DataHandler(
        host='localhost',
        user='root',
        password='Push@1612',
        database='webscrape')

    # db_manager.add_scraped_data_to_database('bus_routes', new.l2)
