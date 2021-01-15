#run docker.bat before running code and make sure to have Neo4j image installed

# if you're starting the DB on your localhost for the first time uncomment these
#from neomodel import install_all_labels, remove_all_labels
from neomodel import db
from bandcamp_scraper import getFanAlbums, getGenreAlbums, updateFans
import db_transcations as dbt
import numpy as np

# WORKFLOW #1, Scrape from an Album
# A URL of an album you want to start your scraping from
url = "https://wildcatstrikeband.bandcamp.com/album/mustard-coloured-years-2"
# the scraping begins
getFanAlbums(url, n =1)

# WORKFLOW #2, Scrape from a tag/genre
tag = "folk"
# the scraping of this genre begins 
# (what's nice is we don't need the genre in the db because we will add it if nesscary in the scraping)
getGenreAlbums(tag)
# We now update any album Fans we added with only that album
updateFans()


# IF we want to run our simpleRecEngine uncomment these
#from models import Album
#from rec_engine import simpleRecEngine

#simpleRecEngine(startingAlbum = getAlbum("https://tonerca.bandcamp.com/album/tar"))
    