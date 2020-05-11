import sqlite3 as sql

class DataBase:
    """Class for keeping DB interactions in one place."""
    DB = "./data/db.db"

    def __init__(self):
        self.insert_raw_query = "INSERT INTO raw_goods (title, shop_id, price, price_ship, url, available, date, good_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
    
    def create_connection(self):
        """Creates a connection with DB according to the documentation of
        sqlite3.
        Attributes:
            db(path): Location of .db file in the system.
        """
        try:
            conn = sql.connect(self.DB)
            return conn
        except sql.Error as e:
            print(e)
        return None

    def insert_raws(self, raws):
        with self.create_connection() as conn:
            cur = conn.cursor()
            for row in raws:
                cur.execute(self.insert_raw_query, row)
            conn.commit()
