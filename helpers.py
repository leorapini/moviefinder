import os
import urllib.request

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from bs4 import BeautifulSoup

# Create Database engine
engine = create_engine('postgres://tpflajgyklddkb:51c254e94d13e4191d66b81520edc11cb83327aba40e3a5baad74399a7df8d2d@ec2-3-231-16-122.compute-1.amazonaws.com:5432/dt25ea812kb1h')

# Create a Database Scoped Session
db = scoped_session(sessionmaker(bind=engine))

def coverlookup(moviesdb, movies):

	# Generate Movie Posters URLs
	for moviedb in moviesdb:

		# Create local movie variable for updating
		movie = dict(moviedb.items())

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
					movie['poster'] = image_url

					# Add poster URL to Database
					db.execute("""UPDATE movies SET poster = :poster 
								  WHERE tconst = :tconst""", 
								  {"poster": image_url, "tconst": movie["tconst"]})

					# Commit changes to database
					db.commit()

					# Append updated movie to movies list
					movies.append(movie)

				except AttributeError:

					# In case of poster not found (or failure) use notfound.jpg
					movie['poster'] = "/static/notfound.jpg"

					# Append updated movie to movies list
					movies.append(movie)

					pass

		else:

			# Append movie with poster to movies list
			movies.append(movie)

	# Close database
	db.close()

	# Return updated list
	return movies
