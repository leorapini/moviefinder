import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request
from datetime import datetime

from helpers import coverlookup
from coolness import votes, low_votes


# Setup application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

"""
# Ensure responses are cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "public, must-revalidate, max-age = 120"
    return response
"""

# Load database
db = SQL("sqlite:///db/movies.db")


# Index
@app.route("/")
def index():

	return render_template("index.html")


# About
@app.route("/about")
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
		if original_genre == "Documentary" or original_genre == "Western":

			coolness_votes = low_votes

		else:

			coolness_votes = votes


		# Query database for 12 top rated movies in original_genre
		movies = db.execute("""SELECT primaryTitle, movies.tconst, poster, numVotes, averageRating 
			                   FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
			                   WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
			                   WHERE genre = :original_genre) AND ratings.averageRating > 6.4 
			                   AND ratings.numVotes BETWEEN :minNumVotes AND :maxNumVotes 
			                   ORDER BY ratings.averageRating DESC, ratings.numVotes ASC LIMIT 18""", 
			                   original_genre = original_genre, minNumVotes = coolness_votes[coolness]["minNumVotes"], 
			                   maxNumVotes = coolness_votes[coolness]["maxNumVotes"])


		# Check lenght of movies 
		if len(movies) < 18:

			# Make search less restrictive
			movies = db.execute("""SELECT primaryTitle, movies.tconst, poster, numVotes, averageRating 
								   FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
								   WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
								   WHERE genre = :original_genre) AND ratings.averageRating > 6.0 
								   AND ratings.numVotes BETWEEN :minNumVotes AND :maxNumVotes
								   ORDER BY ratings.averageRating DESC, ratings.numVotes ASC LIMIT 15""", 
				                   original_genre = original_genre, minNumVotes = coolness_votes[coolness]["minNumVotes"] 
				                   - coolness_votes[coolness]["lowNumVotes"], 
				                   maxNumVotes = coolness_votes[coolness]["maxNumVotes"])

		
		# Get movie covers
		coverlookup(movies)

		# Render template for results
		return render_template("results.html", movies = movies, original_genre = original_genre, 
							   coolness = coolness)
	
	# Request method is GET
	else:

		# Search database for genres list
		genres = db.execute("SELECT genre FROM genres GROUP BY genre")

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
		movies = []

		# List variable to store movies ids to avoid duplicates
		movies_id = []

		# List variable to store genre results
		genres = []

		# Find crossgenres for chosen genre 
		crossgenres = db.execute("""SELECT ogenre, cgenre, matches 
									FROM crossgenre 
									WHERE ogenre = :ogenre AND matches != 0 
									ORDER BY matches DESC LIMIT 5""", ogenre = original_genre)

		# Loop over top 5 genre matches
		for cgenre in crossgenres: 

			# Query database for movies in original_genre matching each genre in top 5 LIMIT 4 movies per crossgenre
			movies_in_genre = db.execute("""SELECT primaryTitle, movies.tconst, poster, averageRating 
										    FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
										    WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
										    WHERE genre = :original_genre) AND movies.tconst 
										    IN (SELECT genres.tconst FROM genres WHERE genre = :cgenre) 
										    AND ratings.averageRating > 6.0 AND ratings.numVotes 
										    BETWEEN :minNumVotes AND :maxNumVotes 
										    ORDER BY ratings.averageRating DESC, 
										    ratings.numVotes ASC LIMIT 12""", 
										    original_genre = original_genre, cgenre = cgenre["cgenre"], 
										    minNumVotes = coolness_votes[coolness]["minNumVotes"], 
										    maxNumVotes = coolness_votes[coolness]["maxNumVotes"])

			# Check lenght of movies_in_genre
			if len(movies_in_genre) < 6:

				movies_in_genre = db.execute("""SELECT primaryTitle, movies.tconst, poster, averageRating 
										    FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
										    WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
										    WHERE genre = :original_genre) AND movies.tconst 
										    IN (SELECT genres.tconst FROM genres WHERE genre = :cgenre) 
										    AND ratings.averageRating > 6.0 AND ratings.numVotes 
										    BETWEEN :minNumVotes AND :maxNumVotes 
										    ORDER BY ratings.averageRating DESC, 
										    ratings.numVotes ASC LIMIT 9""", 
										    original_genre = original_genre, cgenre = cgenre["cgenre"], 
										    minNumVotes = coolness_votes[coolness]["minNumVotes"] - coolness_votes[coolness]["lowNumVotes"], 
										    maxNumVotes = coolness_votes[coolness]["maxNumVotes"])

			# Check lenght of movies_in_genre
			if len(movies_in_genre) != 0:

				# Loop over each film in movies_in_genre
				for movie in movies_in_genre:

					# Check if movies list is empty
					if len(movies) == 0:

						# Append each item and add genre item
						movies.append({'primaryTitle': movie["primaryTitle"], 'tconst': movie["tconst"],
									   'poster': movie["poster"], 'genre': cgenre["cgenre"], 
									   'averageRating': movie['averageRating']})

						# Append movie's tconst to movies_id to avoid duplicates
						movies_id.append(movie['tconst'])

						# Add genre to final genres list
						genres.append(cgenre["cgenre"])


					else:

						if movie['tconst'] not in movies_id:

							# Append each item and add genre item
							movies.append({'primaryTitle': movie["primaryTitle"], 'tconst': movie["tconst"],
										   'poster': movie["poster"], 'genre': cgenre["cgenre"], 
										   'averageRating': movie['averageRating']})

							# Append movie's tconst to movies_id to avoid duplicates
							movies_id.append(movie['tconst'])

							if cgenre["cgenre"] not in genres:

								# Add genre to final genres list
								genres.append(cgenre["cgenre"])


		# Generate Movie Posters URLs
		coverlookup(movies)

		# Render template for results
		return render_template("crossgenres.html", movies = movies, original_genre = original_genre, 
							   genres = genres, coolness = coolness)

	# If method = GET
	else:

		# Search database for genres list
		genres = db.execute("SELECT genre FROM genres GROUP BY genre")

		# Render crossgenre template for search
		return render_template("crossgenre.html", genres = genres)





# Genre Mix
@app.route("/genremix", methods=["GET", "POST"])
def genremix():

	# Check if sending information
	if request.method == "POST":

		# Get user's genre choice from form
		genremix = request.form.getlist("genres")

		print(len(genremix))

		# Check if user selected 2 or 3 genres
		if len(genremix) != 2 and len(genremix) != 3:

			# Search database for genres list
			genres = db.execute("SELECT genre FROM genres GROUP BY genre")

			whoops = "You must choose 2 or 3 genres."
			return render_template("genremix.html", whoops = whoops, genres = genres)

		# Get user's coolness choice from form
		coolness = request.form.get("coolness")

		# Number of votes for database search based on coolness factor
		coolness_votes = low_votes


		if len(genremix) == 2:

			# Query database for movies in original_genre matching each genre in top 5 LIMIT 4 movies per crossgenre
			movies = db.execute("""SELECT primaryTitle, movies.tconst, poster, averageRating 
										    FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
										    WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
										    WHERE genre = :genre0) AND movies.tconst 
										    IN (SELECT genres.tconst FROM genres WHERE genre = :genre1) 
										    AND ratings.averageRating > 6.0 AND ratings.numVotes 
										    BETWEEN :minNumVotes AND :maxNumVotes 
										    ORDER BY ratings.averageRating DESC, 
										    ratings.numVotes ASC LIMIT 18""", 
										    genre0 = genremix[0], genre1 = genremix[1], 
										    minNumVotes = coolness_votes[coolness]["minNumVotes"], 
										    maxNumVotes = coolness_votes[coolness]["maxNumVotes"])


		elif len(genremix) == 3:

			# Query database for movies in original_genre matching each genre in top 5 LIMIT 4 movies per crossgenre
			movies = db.execute("""SELECT primaryTitle, movies.tconst, poster, averageRating 
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
										    genre0 = genremix[0], genre1 = genremix[1], 
										    genre2 = genremix[2], 
										    minNumVotes = coolness_votes[coolness]["minNumVotes"], 
										    maxNumVotes = coolness_votes[coolness]["maxNumVotes"])

		# If no movies were found
		else:

			# Return empty movies list
			movies = []


		# Generate Movie Posters URLs
		coverlookup(movies)

		return render_template("genremixed.html", genremix = genremix, coolness = coolness, movies = movies)


	# Not sending information
	else:

		# Search database for genres list
		genres = db.execute("SELECT genre FROM genres GROUP BY genre")

		# Render crossgenre template for search
		return render_template("genremix.html", genres = genres)














	