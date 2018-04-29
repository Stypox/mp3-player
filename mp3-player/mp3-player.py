import vlc
import os
import fileinput
from random import randint
from time import sleep
from mutagen.easyid3 import EasyID3


SETTINGS_FILENAME = "mp3-player-settings.txt"

ALPHABETICAL_ORDER = 0
ALPHABETICAL_ORDER_CODES = ["0", "a", "alphabetical", "alphabet"]
TITLE_ORDER = 1
TITLE_ORDER_CODES = ["1", "t", "title", "name"]
PRODUCER_ORDER = 2
PRODUCER_ORDER_CODES = ["2", "p", "producer", "artist", "author"]
TRACK_NUMBER_ORDER = 3
TRACK_NUMBER_ORDER_CODES = ["3", "n", "numerical", "track", "track number", "number"]
RANDOM_ORDER = 4
RANDOM_ORDER_CODES = ["4", "r", "random", "rand"]


def getSongs():
    files = os.listdir()
    songs = []
    for file in files:
        if file[-4:] == ".mp3":
            songs.append(file)
    return songs
def getSettings():
    playOrder = open(SETTINGS_FILENAME, "r").readline()
    if (playOrder in ALPHABETICAL_ORDER_CODES):
        return ALPHABETICAL_ORDER
    elif (playOrder in TITLE_ORDER_CODES):
        return TITLE_ORDER
    elif (playOrder in PRODUCER_ORDER_CODES):
        return PRODUCER_ORDER
    elif (playOrder in TRACK_NUMBER_ORDER_CODES):
        return TRACK_NUMBER_ORDER
    elif (playOrder in RANDOM_ORDER_CODES):
        return RANDOM_ORDER


def orderTitle(songs):
    return songs
def orderProducer(songs):
    return songs
def orderTrackNumber(songs):
    return songs
def orderRandom(songs):
    nrSongs = len(songs)
    for currentSong in range(0, nrSongs):
       swapSong = randint(0, nrSongs - 1)
       songs[currentSong], songs[swapSong] = songs[swapSong], songs[currentSong]
    return songs


def playSongs(songs):
    for song in songs:
        player = vlc.MediaPlayer(song)
        player.play()
        print("Now playing \"{}\"".format(song[:-4]))
        while player.get_state() != vlc.State.Ended: pass



def main():
    songs = getSongs()

    playOrder = getSettings()
    if (playOrder == TITLE_ORDER):
        songs = orderTitle(songs)
    elif (playOrder == PRODUCER_ORDER):
        songs = orderProducer(songs)
    elif (playOrder == TRACK_NUMBER_ORDER):
        songs = orderTrackNumber(songs)
    elif (playOrder == RANDOM_ORDER):
        songs = orderRandom(songs)
        
    playSongs(songs)


main()
while 1: pass
