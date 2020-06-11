import sqlite3

# Load database
conn = sqlite3.connect("db/movies.db")

# Create database cursor
db = conn.cursor()

genres = db.execute("SELECT genre FROM genres GROUP BY genre")

genres.fetchall()

for i in genres:
	print(i)

