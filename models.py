## This is where we create our classes to model the objects we'll be storing
from neomodel import StructuredNode, StringProperty, BooleanProperty, DateTimeProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom
from datetime import datetime

# =============================================================================
# The Album Class is to represent the key "item" of our db.
# =============================================================================
class Album(StructuredNode):
    # We assign a uid instead of using bandcamps internal id because it's not always
    #   consistent. Instead we use the url as our unique "key" since no two albums
    #   could have the same link.
    uid = UniqueIdProperty()
    url = StringProperty(unique_index=True)
    
    # Name of the album
    name = StringProperty()
    # We store the band name because it's useful for filtering so you don't just 
    #   reccommend the same bands albums to a person.
    band_name = StringProperty()
    
    # genres and fans are our "foreign keys" edges to our Genre and Fan classes
    genres = RelationshipTo('Genre', 'TAGGED')
    fans = RelationshipFrom('Fan', 'BOUGHTBY')
    
    # Returns all Genres connected to the Album
    def getGenres(self):
        results, columns = self.cypher("MATCH (a) WHERE a.url = '{}' MATCH (a)-[:TAGGED]->(b) RETURN b".format(self.url))
        return [self.inflate(row[0]) for row in results]
    
    # Returns all Fans connected to the Album
    def getFans(self):
        results, columns = self.cypher("MATCH (a) WHERE a.url = '{}' MATCH (a)<-[:BOUGHTBY]-(b) RETURN b".format(self.url))
        return [self.inflate(row[0]) for row in results]

# =============================================================================
# The Fan Class is to represent the "users" of our db.
# =============================================================================
class Fan(StructuredNode):
    # So much like Album we still assign an internal unique id and index on 
    #    url for the same reasons. However here we store Bandcamp's own internal
    #    id so it's easier to do some scraping later on in our process. I don't
    #    love it but it does make things much faster.
    uid = UniqueIdProperty()
    url = StringProperty(unique_index=True)
    temp_id = StringProperty()
    # We also store their name just for potential display purposes.
    name = StringProperty()
    
    # Return all Albums connects to the Fan
    def getAlbums(self):
        results, columns = self.cypher("MATCH (a) WHERE a.url = '{}' MATCH (a)-[:BOUGHTBY]->(b) RETURN b".format(self.url))
        return [self.inflate(row[0]) for row in results]

# =============================================================================
# The Genre Class is to have the an important layer to our Album class.
# Since we also want to store location I made it a class.
# =============================================================================
class Genre(StructuredNode):
    # Genre (or tag in bandcamp internal language) doesn't actually have even an internal id
    #   so we just store the name (which has been normalized)
    uid = UniqueIdProperty()
    name = StringProperty(unique_index=True)
    # Bandcamp stores whether or not the tag is representing a location and I
    #   am not sure how I'll use it yet but I think it's pretty neat.
    isloc = BooleanProperty()
    # It would be fun to see if users have a preference for buying in their geo-graphical locations.
    #   Whether that means they support their community or that they have an ingrained sensbility.
    