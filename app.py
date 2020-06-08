import os
import urllib.request

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request
from bs4 import BeautifulSoup
from datetime import datetime


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


# Homepage Machine
@app.route("/", methods=["GET", "POST"])
def index():
	
	# Check if method is sending info
	if request.method == "POST":
		
		# Get user's genre choice from form
		original_genre = request.form.get("genre")

		# Get user's level of coolness from form
		coolness = request.form.get("coolness")

		# numVotes variables for database search
		maxNumVotes = 0
		minNumVotes = 0

		# Low numVotes variable
		lowNumVotes = 0


		# Adjust low numVotes variable do Documentary
		if original_genre == "Documentary" or original_genre == "Western":

			if coolness == "Popular":

				maxNumVotes = 100000000
				minNumVotes = 60000
				lowNumVotes = 0

			elif coolness == "Not So Popular":

				maxNumVotes = 60000
				minNumVotes = 25000
				lowNumVotes = 0

			elif coolness == "Lesser Known":

				maxNumVotes = 25000
				minNumVotes = 10000
				lowNumVotes = 0

		else:

			# Check coolness level a set appropriate max and min amount of votes
			if coolness == "Popular":

				maxNumVotes = 100000000
				minNumVotes = 400000
				lowNumVotes = 200000

			elif coolness == "Not So Popular":

				maxNumVotes = 300000
				minNumVotes = 100000
				lowNumVotes = 50000

			elif coolness == "Lesser Known":

				maxNumVotes = 100000
				minNumVotes = 60000
				lowNumVotes = 30000

		# Query database for 12 top rated movies in original_genre
		movies = db.execute("""SELECT primaryTitle, movies.tconst, poster, numVotes, averageRating 
			                   FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
			                   WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
			                   WHERE genre = :original_genre) AND ratings.averageRating > 6.4 
			                   AND ratings.numVotes BETWEEN :minNumVotes AND :maxNumVotes 
			                   ORDER BY ratings.averageRating DESC, ratings.numVotes ASC LIMIT 15""", 
			                   original_genre = original_genre, minNumVotes = minNumVotes, 
			                   maxNumVotes = maxNumVotes)


		# Check lenght of movies 
		if len(movies) < 15:

			# Make search less restrictive
			movies = db.execute("""SELECT primaryTitle, movies.tconst, poster, numVotes, averageRating 
								   FROM movies JOIN ratings ON movies.tconst = ratings.tconst 
								   WHERE movies.tconst IN (SELECT genres.tconst FROM genres 
								   WHERE genre = :original_genre) AND ratings.averageRating > 6.0 
								   AND ratings.numVotes BETWEEN :minNumVotes AND :maxNumVotes
								   ORDER BY ratings.averageRating DESC, ratings.numVotes ASC LIMIT 12""", 
				                   original_genre = original_genre, minNumVotes = minNumVotes - lowNumVotes, 
				                   maxNumVotes = maxNumVotes)

		

		# Generate Movie Posters URLs
		for movie in movies:

			# Check if movie already doesn't have a poster
			if movie["poster"] == "\\N":

				# Define URL for BeautifulSoup 
				url = "https://www.imdb.com/title/" + movie["tconst"] + "/"

				# Create response variable for urllib request
				with urllib.request.urlopen(url) as response:

					# Variables for parsing
					html = response.read()
					soup = BeautifulSoup(html, 'html.parser')

					try:

						# Get image URL from html file
						image_url = soup.find('div', class_='poster').a.img['src']

						# Add poster key with url item do each movie list item
						movie["poster"] = image_url

						# Add poster URL to Database
						db.execute("""UPDATE movies SET poster = :poster 
									  WHERE tconst = :tconst""", 
									  poster = image_url, tconst = movie["tconst"])

					except AttributeError:

						movie["poster"] = "/static/notfound.jpg"

						pass


		# Render template for results
		return render_template("results.html", movies = movies, original_genre = original_genre, 
							   coolness = coolness)
	
	# Request method is GET
	else:

		# Search database for genres list
		genres = db.execute("SELECT genre FROM genres GROUP BY genre")

		# Return index template
		return render_template("index.html", genres = genres)


# Crossgenres Machine
@app.route("/crossgenre", methods=["GET", "POST"])
def crossgenre():
	
	# Check if method is sending info
	if request.method == "POST":
		
		# Get user choice from form
		original_genre = request.form.get("genre")

		# Get user's level of coolness from form
		coolness = request.form.get("coolness")

		# numVotes variables for database search
		maxNumVotes = 0
		minNumVotes = 0

		# Low numVotes variable
		lowNumVotes = 0


		# Adjust low numVotes variable do Documentary
		if original_genre == "Documentary" or original_genre == "Western":

			if coolness == "Popular":

				maxNumVotes = 100000000
				minNumVotes = 60000
				lowNumVotes = 0

			elif coolness == "Not So Popular":

				maxNumVotes = 60000
				minNumVotes = 25000
				lowNumVotes = 0

			elif coolness == "Lesser Known":

				maxNumVotes = 25000
				minNumVotes = 10000
				lowNumVotes = 0

		else:

			# Check coolness level a set appropriate max and min amount of votes
			if coolness == "Popular":

				maxNumVotes = 100000000
				minNumVotes = 400000
				lowNumVotes = 200000

			elif coolness == "Not So Popular":

				maxNumVotes = 300000
				minNumVotes = 100000
				lowNumVotes = 50000

			elif coolness == "Lesser Known":

				maxNumVotes = 100000
				minNumVotes = 60000
				lowNumVotes = 30000

		# List variable to store movie results
		movies = []

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
										    ratings.numVotes ASC LIMIT 6""", 
										    original_genre = original_genre, cgenre = cgenre["cgenre"], 
										    minNumVotes = minNumVotes, maxNumVotes = maxNumVotes)

			# Check lenght of movies_in_genre
			if len(movies_in_genre) != 0:

				# Add genre to final genres list
				genres.append(cgenre["cgenre"])

				# Loop over each film in movies_in_genre
				for movie in movies_in_genre:

					# Append each item and add genre item
					movies.append({'primaryTitle': movie["primaryTitle"], 'tconst': movie["tconst"],
								   'poster': movie["poster"], 'genre': cgenre["cgenre"], 
								   'averageRating': movie['averageRating']})

		# Generate Movie Posters URLs
		for movie in movies:

			# Check if movie already doesn't have a poster
			if movie["poster"] == "\\N":

				# Define URL for BeautifulSoup 
				url = "https://www.imdb.com/title/" + movie["tconst"] + "/"

				# Create response variable for urllib request
				with urllib.request.urlopen(url) as response:

					# Variables for parsing
					html = response.read()
					soup = BeautifulSoup(html, 'html.parser')

					try:

						# Get image URL from html file
						image_url = soup.find('div', class_='poster').a.img['src']

						# Add poster key with url item do each movie list item
						movie["poster"] = image_url

						# Add poster URL to Database
						db.execute("UPDATE movies SET poster = :poster WHERE tconst = :tconst", 
									poster = image_url, tconst = movie["tconst"])

					except AttributeError:

						movie["poster"] = "/static/notfound.jpg"

						pass

		# Render template for results
		return render_template("crossgenres.html", movies = movies, original_genre = original_genre, 
							   genres = genres, coolness = coolness)

	# If method = GET
	else:

		# Search database for genres list
		genres = db.execute("SELECT genre FROM genres GROUP BY genre")

		# Render crossgenre template for search
		return render_template("crossgenre.html", genres = genres)


# About Machine
@app.route("/about")
def about():

	return render_template("about.html")

	