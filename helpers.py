import urllib.request

from bs4 import BeautifulSoup
from cs50 import SQL

# Load database
db = SQL("sqlite:///db/movies.db")

def coverlookup(movies):

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

	return movies
