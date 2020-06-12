import os 

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Create engine
engine = create_engine('sqlite:///db/movies.db')

# Create a scoped session
db = scoped_session(sessionmaker(bind=engine))

original_genre = "Action"

minNumVotes = 60000

maxNumVotes = 2000000

moviesdb = db.execute("""SELECT primaryTitle, movies.tconst, poster, numVotes, averageRating 
	                   FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
	                   WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
	                   WHERE genre = :genre AND ratings.averageRating > 6.4 
	                   AND ratings.numVotes BETWEEN :minNumVotes AND :maxNumVotes)
	                   ORDER BY ratings.averageRating DESC, ratings.numVotes ASC LIMIT 18""", 
	                   {"genre": original_genre, "minNumVotes": minNumVotes, 
	                   "maxNumVotes": maxNumVotes}).fetchall()

movies = []

def posters(moviesdb, movies):

	for movie in moviesdb:

	    local_movie = dict(movie.items())

	    local_movie['poster'] = "No poster"

	    movies.append(local_movie)

	return movies

posters(moviesdb, movies)

print(movies)

