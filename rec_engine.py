from db_transcations import getAlbumwithParams
from random import sample 
from collections import Counter
from models import Genre, Fan, Album

def calculateFilters(albumsLiked, albumsDisLiked):
    genreCount = Counter()
    userCount = Counter()
    
    for album in albumsLiked:
        genreCount.update([genre.name for genre in album.getGenres()])
        userCount.update([fan.url for fan in album.getFans()])
        
    for album in albumsDisLiked:
        genreCount.subtract([genre.name for genre in album.getGenres()])
        userCount.subtract([fan.url for fan in album.getFans()])
        
        
    return genreCount, userCount

#def getRandAlbumLessimple(albumsLiked, albumsDisliked, skip):

def lesssimpleRecEngine(startingAlbum: Album, n = 5):
    albumsLiked = []
    albumsDisLiked = []
    skip = []
    recs = []
    
    #If we have a starting album we add them to our sublists
    if startingAlbum != None:
        skip.append(startingAlbum.band_name)
        albumsLiked.extend(startingAlbum)
    
    while len(recs) <= n:
        rec = calculateFilters(albumsLiked, albumsDisLiked)
        if not rec:
            break
        else:
            rec = rec[0]
            
        print(rec.url)
        
        doTheyLike = 'NOT SET'
        while doTheyLike not in ['l', 'd', 's']:
            doTheyLike = input('Whatcha think? [(l)ike, (d)islike, (s)kip]\n')
        
        if doTheyLike == "l":
            recs.append(rec)
            skip.append(rec.band_name)
            albumsLiked.extend(rec)
            
        elif doTheyLike == "d":
            skip.append(rec.band_name)
            albumsDisLiked.extend(rec)
            
        elif doTheyLike == "s":
            skip.append(rec.band_name)
    
    return recs
        

def getRandAlbumSimple(genreLikes, userLikes, skip):
    randSet = getAlbumwithParams(genreLikes, userLikes, skip)
    
    return sample(randSet, 1)

def simpleRecEngine(startingAlbum = None, n = 5):
    recs = []
    genreLikes = []
    userLikes = []
    skip = []
    
    #If we have a starting album we add them to our sublists
    if startingAlbum != None:
        skip.append(startingAlbum.band_name)
        genreLikes.extend([genre.name for genre in startingAlbum.getGenres()])
        userLikes.extend([fan.url for fan in startingAlbum.getFans()])
    
    while len(recs) <= n:
        rec = getRandAlbumSimple(genreLikes, userLikes, skip)
        if not rec:
            break
        else:
            rec = rec[0]
            
        print(rec.url)
        
        doTheyLike = 'NOT SET'
        while doTheyLike not in ['l', 'd', 's']:
            doTheyLike = input('Whatcha think? [(l)ike, (d)islike, (s)kip]\n')
        
        if doTheyLike == "l":
            recs.append(rec)
            skip.append(rec.band_name)
            genreLikes.extend([genre.name for genre in rec.getGenres()])
            userLikes.extend([fan.url for fan in rec.getFans()])
            
        elif doTheyLike == "d":
            skip.append(rec.band_name)
            genreLikes = [x for x in genreLikes if x not in [genre.name for genre in rec.getGenres()]]
            userLikes = [x for x in userLikes if x not in [fan.url for fan in rec.getFans()]]
            
        elif doTheyLike == "s":
            skip.append(rec.band_name)
    
    return recs