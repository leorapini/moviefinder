import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from flask import Flask, flash, redirect, render_template, request

from helpers import coverlookup
from coolness import votes, low_votes


# Setup application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses are cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "public, must-revalidate, max-age = 120"
    return response

# Create Database engine
engine = create_engine('postgres://tpflajgyklddkb:51c254e94d13e4191d66b81520edc11cb83327aba40e3a5baad74399a7df8d2d@ec2-3-231-16-122.compute-1.amazonaws.com:5432/dt25ea812kb1h')

# Create a Database Scoped Session
db = scoped_session(sessionmaker(bind=engine))

@app.teardown_request
def remove_session(ex=None):
    db.remove()

# Index
@app.route("/", methods=["GET"])
def index():

	return render_template("index.html")

# About
@app.route("/about", methods=["GET"])
def about():

	return render_template("about.html")


# Genre Search
@app.route("/genresearch", methods=["GET", "POST"])
def genresearch():
	
	# Check if method is sending info
	if request.method == "POST":
		
		# Get user's genre choice from form
		original_genre = request.form.get("genre")

		# Get user's level of coolness from form
		coolness = request.form.get("coolness")

		# Number of votes for database search based on coolness factor
		if original_genre == "Documentary" or original_genre == "Western" or original_genre == "War" or original_genre == "Musical":

			coolness_votes = low_votes

		else:

			coolness_votes = votes


		# Query database for 12 top rated movies in original_genre
		moviesdb = db.execute("""SELECT primaryTitle, movies.tconst, poster, numVotes, averageRating 
	                   FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
	                   WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
	                   WHERE genre = :genre AND ratings.averageRating > 6.4 
	                   AND ratings.numVotes BETWEEN :minNumVotes AND :maxNumVotes)
	                   ORDER BY ratings.averageRating DESC, ratings.numVotes ASC LIMIT 18""", 
	                   {"genre": original_genre, "minNumVotes": coolness_votes[coolness]["minNumVotes"], 
	                   "maxNumVotes": coolness_votes[coolness]["maxNumVotes"]}).fetchall()

		# Check lenght of movies 
		if len(moviesdb) < 18:

			# Make search less restrictive
			moviesdb = db.execute("""SELECT primaryTitle, movies.tconst, poster, numVotes, averageRating 
						   FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
						   WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
						   WHERE genre = :genre) AND ratings.averageRating > 5.9 
						   AND ratings.numVotes BETWEEN :minNumVotes AND :maxNumVotes
						   ORDER BY ratings.averageRating DESC, ratings.numVotes ASC LIMIT 18""", 
		                   {"genre": original_genre, 
		                   	"minNumVotes": coolness_votes[coolness]["minNumVotes"] - coolness_votes[coolness]["lowNumVotes"], 
		                    "maxNumVotes": coolness_votes[coolness]["maxNumVotes"]}).fetchall()

		# Empty list of movies for results
		movies = []

		# Generate Movie Posters URLs
		coverlookup(moviesdb, movies)

		# Render template for results
		return render_template("results.html", movies = movies, original_genre = original_genre, 
							   coolness = coolness)
	
	# Request method is GET
	else:

		# Execute SQL command
		genres = db.execute("SELECT genre FROM genres GROUP BY genre").fetchall()

		# Return genre search template
		return render_template("genresearch.html", genres = genres)


# Cross genres 
@app.route("/crossgenre", methods=["GET", "POST"])
def crossgenre():
	
	# Check if method is sending info
	if request.method == "POST":
		
		# Get user choice from form
		original_genre = request.form.get("genre")

		# Get user's level of coolness from form
		coolness = request.form.get("coolness")

		# Initiate number of votes variables
		maxNumVotes = 0
		minNumVotes = 0
		lowNumVotes = 0

		# Check if genre is a low ranking gender to adjust number of votes
		if original_genre == "Documentary" or original_genre == "Western" or original_genre == "Musical" or original_genre == "Sport" or original_genre == "War" or original_genre == "Animation":

			coolness_votes = low_votes

		else:

			coolness_votes = votes

		# List variable to store movie results
		moviesdb = []

		# List variable to store movies ids to avoid duplicates
		movies_id = []

		# List variable to store genre results
		genres = []

		# Find crossgenres for chosen genre 
		crossgenres = db.execute("""SELECT ogenre, cgenre, matches 
									FROM crossgenre 
									WHERE ogenre = :ogenre AND matches != 0 
									ORDER BY matches DESC LIMIT 5""", {"ogenre": original_genre}).fetchall()

		# Loop over top 5 genre matches
		for cgenre in crossgenres: 

			# Query database for movies in original_genre matching each genre in top 5 LIMIT 4 movies per crossgenre
			movies_in_genre = db.execute("""SELECT primaryTitle, movies.tconst, poster, averageRating 
										    FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
										    WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
										    WHERE genre = :original_genre) AND movies.tconst 
										    IN (SELECT genres.tconst FROM genres WHERE genre = :cgenre) 
										    AND ratings.averageRating > 5.9 AND ratings.numVotes 
										    BETWEEN :minNumVotes AND :maxNumVotes 
										    ORDER BY ratings.averageRating DESC, 
										    ratings.numVotes ASC LIMIT 12""", 
										    {"original_genre": original_genre, "cgenre": cgenre["cgenre"], 
										    "minNumVotes": coolness_votes[coolness]["minNumVotes"], 
										    "maxNumVotes": coolness_votes[coolness]["maxNumVotes"]}).fetchall()


			# Check lenght of movies_in_genre
			if len(movies_in_genre) < 6:

				movies_in_genre = db.execute("""SELECT primaryTitle, movies.tconst, poster, averageRating 
											    FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
											    WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
											    WHERE genre = :original_genre) AND movies.tconst 
											    IN (SELECT genres.tconst FROM genres WHERE genre = :cgenre) 
											    AND ratings.averageRating > 5.9 AND ratings.numVotes 
											    BETWEEN :minNumVotes AND :maxNumVotes 
											    ORDER BY ratings.averageRating DESC, 
											    ratings.numVotes ASC LIMIT 12""", 
											    {"original_genre": original_genre, "cgenre": cgenre["cgenre"], 
											    "minNumVotes": coolness_votes[coolness]["minNumVotes"] - coolness_votes[coolness]["lowNumVotes"], 
											    "maxNumVotes": coolness_votes[coolness]["maxNumVotes"]}).fetchall()

			# Check lenght of movies_in_genre
			if len(movies_in_genre) != 0:

				# Loop over each film in movies_in_genre
				for movie in movies_in_genre:

					# Check if movies list is empty
					if len(moviesdb) == 0:

						# Append each item and add genre item
						moviesdb.append({'primaryTitle': movie["primaryTitle"], 'tconst': movie["tconst"],
									   'poster': movie["poster"], 'genre': cgenre["cgenre"], 
									   'averageRating': movie['averageRating']})

						# Append movie's tconst to movies_id to avoid duplicates
						movies_id.append(movie['tconst'])

						# Add genre to final genres list
						genres.append(cgenre["cgenre"])


					else:

						if movie['tconst'] not in movies_id:

							# Append each item and add genre item
							moviesdb.append({'primaryTitle': movie["primaryTitle"], 'tconst': movie["tconst"],
										   'poster': movie["poster"], 'genre': cgenre["cgenre"], 
										   'averageRating': movie['averageRating']})

							# Append movie's tconst to movies_id to avoid duplicates
							movies_id.append(movie['tconst'])

							if cgenre["cgenre"] not in genres:

								# Add genre to final genres list
								genres.append(cgenre["cgenre"])


		# Empty list of movies for results
		movies = []

		# Generate Movie Posters URLs
		coverlookup(moviesdb, movies)

		# Render template for results
		return render_template("crossgenres.html", movies = movies, original_genre = original_genre, 
							   genres = genres, coolness = coolness)



	# If method = GET
	else:

		# Search database for genres list
		genres = db.execute("SELECT genre FROM genres GROUP BY genre").fetchall()

		# Render crossgenre template for search
		return render_template("crossgenre.html", genres = genres)





# Genre Mix
@app.route("/genremix", methods=["GET", "POST"])
def genremix():

	# Check if sending information
	if request.method == "POST":

		# Get user's genre choice from form
		genremix = request.form.getlist("genres")

		# Check if user selected 2 or 3 genres
		if len(genremix) != 2 and len(genremix) != 3:

			# Search database for genres list
			genres = db.execute("SELECT genre FROM genres GROUP BY genre").fetchall()

			whoops = "You must choose 2 or 3 genres."
			return render_template("genremix.html", whoops = whoops, genres = genres)

		# Get user's coolness choice from form
		coolness = request.form.get("coolness")

		# Number of votes for database search based on coolness factor
		coolness_votes = low_votes


		if len(genremix) == 2:

			# Query database for movies in original_genre matching each genre in top 5 LIMIT 4 movies per crossgenre
			moviesdb = db.execute("""SELECT primaryTitle, movies.tconst, poster, averageRating 
								    FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
								    WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
								    WHERE genre = :genre0) AND movies.tconst 
								    IN (SELECT genres.tconst FROM genres WHERE genre = :genre1) 
								    AND ratings.averageRating > 5.9 AND ratings.numVotes 
								    BETWEEN :minNumVotes AND :maxNumVotes 
								    ORDER BY ratings.averageRating DESC, 
								    ratings.numVotes ASC LIMIT 18""", 
								    {"genre0": genremix[0], "genre1": genremix[1], 
								    "minNumVotes": coolness_votes[coolness]["minNumVotes"], 
								    "maxNumVotes": coolness_votes[coolness]["maxNumVotes"]}).fetchall()


		elif len(genremix) == 3:

			# Query database for movies in original_genre matching each genre in top 5 LIMIT 4 movies per crossgenre
			moviesdb = db.execute("""SELECT primaryTitle, movies.tconst, poster, averageRating 
								    FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
								    WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
								    WHERE genre = :genre0) AND movies.tconst 
								    IN (SELECT genres.tconst FROM genres WHERE genre = :genre1)
								    AND movies.tconst IN (SELECT genres.tconst FROM genres 
								    WHERE genre = :genre2)
								    AND ratings.averageRating > 5.9 AND ratings.numVotes 
								    BETWEEN :minNumVotes AND :maxNumVotes 
								    ORDER BY ratings.averageRating DESC, 
								    ratings.numVotes ASC LIMIT 18""", 
								    {"genre0": genremix[0], "genre1": genremix[1], 
								    "genre2": genremix[2], 
								    "minNumVotes": coolness_votes[coolness]["minNumVotes"], 
								    "maxNumVotes": coolness_votes[coolness]["maxNumVotes"]}).fetchall()


		# Empty list of movies for results
		movies = []

		# Generate Movie Posters URLs
		coverlookup(moviesdb, movies)

		return render_template("genremixed.html", genremix = genremix, coolness = coolness, movies = movies)


	# Not sending information
	else:

		# Search database for genres list
		genres = db.execute("SELECT genre FROM genres GROUP BY genre").fetchall()

		# Render crossgenre template for search
		return render_template("genremix.html", genres = genres)







	