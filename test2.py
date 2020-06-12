import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Create engine
engine = create_engine(os.getenv("DATABASE_URL"))

# Create a scoped session
db = scoped_session(sessionmaker(bind=engine))

# Execute SQL command
genres = db.execute("SELECT genre FROM genres GROUP BY genre").fetchall()

for genre in genres:
	print(genre.genre)

