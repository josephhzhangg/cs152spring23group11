import sqlite3


class Database:

    @staticmethod
    def initialize_db():
        con = sqlite3.connect("discord.db")
        cur = con.cursor()
        # cur.execute("CREATE TABLE reported(id)")
        # cur.execute("CREATE TABLE warned(id)")
        con.commit()
        return cur, con
