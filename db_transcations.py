## This is where we interface with our neo4j transcations
from neomodel import db, config
from models import Genre, Fan, Album

# Set the db url so we can comminucate with neo4j
config.DATABASE_URL = 'bolt://:@localhost:7687'
# This can mess stuff up if it thinks we want to install a new class
config.AUTO_INSTALL_LABELS = False

def getAlbumwithParams(genres, fans, skip):
    query = "MATCH (a:Album) Where not a.band_name in {}".format(skip)
    if genres:
        query = query + " MATCH (a)-[:TAGGED]->(g:Genre) Where g.name in {}".format(genres)
    if fans:
        query = query + " MATCH (a)<-[:BOUGHTBY]-(f:Fan) Where f.url in {}".format(fans)
    query = query + " RETURN a"
    results, meta = db.cypher_query(query)
    return [Album.inflate(row[0]) for row in results]

def getFanswithAlbums(n = 1):
    query = "Match (f:Fan) Where size((f)-[:BOUGHTBY]->()) <= {}".format(n)
    query += " RETURN f"
    
    results, meta = db.cypher_query(query)
    return [Fan.inflate(row[0]) for row in results]

def getGenre(name):
    with db.read_transaction:
        genre = Genre.nodes.get_or_none(name=name)
    return genre

def getFan(url):
    with db.read_transaction:
        fan = Fan.nodes.get_or_none(url=url)
    return fan

def getAlbum(url):
    with db.read_transaction:
        album = Album.nodes.get_or_none(url=url)
    return album

def getGenres():
    with db.read_transaction:
        genres = Genre.nodes.all()
    return genres

def getFans():
    with db.read_transaction:
        fans = Fan.nodes.all()
    return fans

def getAlbums():
    with db.read_transaction:
        albums = Album.nodes.all()
    return albums

def createGenres(genres):
    with db.transaction:
        genres = Genre.create_or_update(*genres)
    return genres

def createFans(fans):
    with db.transaction:
        fan = Fan.create_or_update(*fans)
    return fans

def createGenre(name, isloc):
    with db.read_transaction:
        genre = Genre.nodes.get_or_none(name=name, isloc=isloc)
    if genre == None:
        with db.write_transaction:
            genre = Genre(name=name, isloc=isloc).save()
    return genre

def createFan(name, url, temp_id):
    with db.read_transaction:
        fan = Fan.nodes.get_or_none(name=name, url=url)
    if fan == None:
        with db.write_transaction:
            fan = Fan(name=name, url=url, temp_id=temp_id).save()
    return fan

def createAlbum(name, url, band_name, art_url):
    with db.read_transaction:
        album = Album.nodes.get_or_none(name=name, url=url, band_name=band_name)
        album2 = Album.nodes.get_or_none(name=name, url=url)
        album3 = Album.nodes.get_or_none(url=url)
    if album == None and album3 == None and album2 == None:
        with db.write_transaction:
            album = Album(name=name, url=url, band_name=band_name, art_url=art_url).save()
    return  album if album != None else (album2 if album2 != None else album3)

def addFantoAlbum(fan: Fan, album: Album):
    if fan not in album.getFans():
        album.fans.connect(fan)
        fan.save()
        album.save()

def addGenretoAlbum(genre: Genre, album: Album):
    if genre not in album.getGenres():
        album.genres.connect(genre)
        genre.save()
        album.save()