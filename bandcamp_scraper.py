import json
import requests
import time
from multiprocessing.pool import ThreadPool
import db_transcations as dbt
from functools import partial
from models import * 

# This is only for ONE function where we need to get album_id
# All other scraping is with json requests
from bs4 import BeautifulSoup

# This global is so we pause our scraper every once in a while
global requestsN
requestsN = 0

# =============================================================================
# SCRAPER "Mains", this is where functions that "start the scraping process are
# =============================================================================

# getFanAlbums: takes an album-`url` and scrapes all the fans related
# `n` is to specify if you want to go addional depths and scrape the albums you've scraped fan collections
def getFanAlbums(url, n = 1):
    # Get the albums fans
    fans = getFans(url)
    # Store the fans in our DB
    fans = saveFans(fans)
    
    # Scrapes each fans collection
    collection_albums = fanAlbumHelper(fans)
        
    # If n is of greater depth we repeat this process with each album we've scraped
    if n > 1:
        for album in collection_albums:
            getFanAlbums(album, (n-1))
    
    return collection_albums

# getGenreAlbums: is an "endless" scraping of a particular genre.
# With the defaults it doesn't stop til it's scrapped every album in that tag
def getGenreAlbums(tag, start_page = 1, end_page = 999):
    # The internal url for where you request albums relating to a genre
    genre_album_url = "https://bandcamp.com/api/hub/2/dig_deeper"
    # Is returned with the request to specify if there are more albums in the tag
    more_available = True
    
    # Different bandcamp apis have different mappings for same fields
    keys = {
        "title":"title",
        "url":"tralbum_url",
        "band":"band_name",
        "art":"art_id",
        "bid":"band_id",
        "aid":"tralbum_id"
            }
    
    # Empty list
    albums = []
    
    # Our request
    data = {
        "filters": {
            "format":"all",
            "location":0,
            "sort":"date",
            "tags": [tag]
            },
        "page": start_page
        } 
    
    # Our loop for scraping bandcamp tag pages
    while more_available and data["page"] <= end_page:
        res = request_loop(genre_album_url, data)
        data["page"] += 1
        
        try:
            collection = res.json()["items"]
        except:
            print("\nCollection Error\n")
            print(tag)
            print(page)
            print(res)
            print("\n")
            raise
        
        try:
            more_available = res.json()["more_available"]
        except:
            more_available = False
            
        # We return album urls
        albums.extend(addAlbumCollection(collection, keys))
    
    # We then add the fans to each Album so we can scrape those fans later (outside of function)
    for album_url in albums:
        album = dbt.getAlbum(album_url)
        fans = getFans(album_url)
        fans = saveFans(fans)
        for fan in fans:
            dbt.addFantoAlbum(fan, album)
    
    print("\nFinal Page: ")
    print(data["page"])
        
    return albums


          
# updateFans: updates the fans with n or less albums in their collection
#             Super useful for after scraping genre pages.
def updateFans(n = 1):
    fans = dbt.getFanswithAlbums(n = n)
    albums_added = fanAlbumHelper(fans)
    
    return albums_added

# =============================================================================
# HELPERS
# =============================================================================
# getAlbumTags: with a bandId and albumId we return the list of coresponding genres
def getAlbumTags(bandId, albumId):
    # This is where you can internally post tag requests. Hard to find.
    tag_url = "https://bandcamp.com/api/mobile/17/tralbum_tags"
    
    # Setting up our data. It doesn't seem to matter if tralbum_type is a or t
    data = {
        "band_id":bandId,
        "tralbum_type":"a",
        "tralbum_id":albumId
    }
    
    # Send our request to our loop
    res = request_loop(tag_url, data)
    
    # Get the json
    genres_json = res.json()
    try:
        # If the json has tags we can continue but if not...
        genres_json["tags"]
    except:
        # ...we return an empty array
        return []
    
    # goes through our genres and saves what we want
    genres = saveGenres([{'name':tag["norm_name"], 'isloc':tag["isloc"]} for tag in genres_json["tags"]])
    
    # return genres, which should be a list of Genre objects
    return genres

# scrapeFanCollection: it adds every album in this `fan`'s collection to our db
def scrapeFanCollection(fan: Fan):    
    # Different bandcamp apis have different mappings for same fields
    keys = {
        "title":"item_title",
        "url":"item_url",
        "band":"band_name",
        "art":"item_art_url",
        "bid":"band_id",
        "aid":"album_id"
            }
    
    # We need this for the query
    fan_id = fan.temp_id
    # the internal url 
    collection_items_url = "https://bandcamp.com/api/fancollection/1/collection_items"

    # our request, the older_than_token is set to max value
    data = {
        "fan_id": fan_id,
        "older_than_token": "9999999999:999999999:a::",
        "count": 10000,
    }

    res = request_loop(collection_items_url, data)

    try:
        # We see if the request worked
        collection = res.json()
    except:
        print("\nCollection Error\n")
        print(fan.temp_id)
        print(res)
        print("\n")
        raise
        
    # Add each album to our db
    albums = addAlbumCollection(collection["items"], keys)
    
    # Add the fan to the album
    for album_url in albums:
        album = dbt.getAlbum(album_url)
        dbt.addFantoAlbum(fan, album)
    
    return albums

# getFans: scrapes each fan from an album_url
# if album_id is provided we can skip a BIG step 
def getFans(url, album_id = None):
    # Where we're posting our request
    request_url = url.split(".com")[0] + ".com/api/tralbumcollectors/2/"
    # These are fans that left no written review
    thumbs_url = request_url + "thumbs"
    # These are fans that left a review
    reviews_url = request_url + "reviews"
    
    # If we're not provided the album_id we find it on the page
    if album_id == None:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "lxml")
        album = json.loads(soup.find(id="pagedata")["data-blob"])
        album_id = album["album_id"]

    data = {
        "tralbum_type": "a",
        "tralbum_id": album_id,
        "count": 10000,
        # Largest possible value
        "token":"1:9999999999:9999999:0:1:0",
    }

# Gets all the fans from an album (people who write reviews and people who just buy the album are separated out)
# Also we do the try except block because some might not have one or the other

    thumbs_res = request_wrapper(thumbs_url, data)
    try:
        thumbs = thumbs_res.json()["results"]
    except:
        thumbs = []

    reviews_res = request_wrapper(reviews_url, data)
    try:
        reviews = reviews_res.json()["results"]
    except:
        reviews = []

    fans = []

    for review in reviews:
        fans.append((review["url"], review["fan_id"], review["name"]))

    for thumb in thumbs:
        fans.append((thumb["url"], thumb["fan_id"], thumb["name"]))
        
    return fans


# =============================================================================
# DB Interfacers
# =============================================================================
# saveGenres: takes a list of genres with provided tags and saves them to our db
def saveGenres(genres_old):
    genres = []
    for genre in genres_old:
        genre_new = dbt.getGenre(genre["name"])
        if genre_new == None:
            genre_new = dbt.createGenre(genre["name"], genre["isloc"])
        genres.append(genre_new)
    return genres
    
# addAlbumCollection: adds a list of albums to our db
# the keys argument is passed to saveAlbum where it maps the item's fields to an abstracted field
def addAlbumCollection(collection, keys):
    collection_albums = []

    for item in collection:
        album = saveAlbum(item, keys)
        collection_albums.append(album.url)
        
    return collection_albums

# saveAlbum: takes an album and a dictionary of keys coresponding to what each field is called and saves the album to our db
def saveAlbum(album_old, keys):
    album = dbt.getAlbum(album_old[keys["url"]])
    if album == None:
        album = dbt.createAlbum(album_old[keys["title"]], album_old[keys["url"]], album_old[keys["band"]], album_old[keys["art"]])
    if not album.getGenres():
        genres = getAlbumTags(album_old[keys["bid"]], album_old[keys["aid"]])
        for genre in genres:
            dbt.addGenretoAlbum(genre, album)
    return album

# saveFans: adds a list of fans to our db
def saveFans(fans_old):
    fans = []
    for fan in fans_old:
        fan_new = dbt.getFan(fan[0])
        if fan_new == None:
            fan_new = dbt.createFan(fan[2], fan[0], fan[1])
        fans.append(fan_new)
    return fans
    

#Scrapes all albums of fans provided
def fanAlbumHelper(fans):
    with ThreadPool(5) as p:
        collection_albums = p.map(scrapeFanCollection, fans)
        
    # we create a set so we ensure no duplication
    collection_albums = set([item for sublist in collection_albums for item in sublist])
    
    return collection_albums

# =============================================================================
# UTIL FUNCTIONS
# =============================================================================
# request_wrapper: posts a request, pausing after evert pauseMod times
def request_wrapper(url, data, pauseMod = 300):
    # specify we're using the global variable
    global requestsN
    requestsN += 1
    
    # sleep if we've had pauseMod requests inbetween pausing
    if requestsN % pauseMod == 0:
        time.sleep(pauseMod)
    
    # finally we post the request!
    return requests.post(url, json=data)
    
# request_loop: keeps posting request til we get data
# I found that I often got back status_codes instead of data so I made this function
def request_loop(url, data, i = 100, sleep = 10):
    # see what we got back from our request
    res = request_wrapper(url, data)   
    
    i = 0
    # if it's one of these status codes, sleep then post again
    while res.status_code in [429, 503, 504]:
        time.sleep(sleep)
        res = request_wrapper(url, data) 
        i+=1
        # just in case of an infinite while
        if i == 100:
            break 
        
    return res