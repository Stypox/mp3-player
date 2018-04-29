import vlc
import os
import fileinput
import random
from time import sleep
from mutagen.easyid3 import EasyID3
import msvcrt as keyboard


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

ARROW_UP = b"H"
ARROW_DN = b"P"
ARROW_DX = b"M"
ARROW_SX = b"K"


def getSongs():
    files = os.listdir()
    songs = []
    for file in files:
        if file[-4:] == ".mp3":
            songs.append(file)
    return songs
def getSettings():
    settings = []
    file = open(SETTINGS_FILENAME, "r")
    line = file.readline().strip()
    print(line)
    if (line in ALPHABETICAL_ORDER_CODES):
        settings.append(ALPHABETICAL_ORDER)
    elif (line in TITLE_ORDER_CODES):
        settings.append(TITLE_ORDER)
    elif (line in PRODUCER_ORDER_CODES):
        settings.append(PRODUCER_ORDER)
    elif (line in TRACK_NUMBER_ORDER_CODES):
        settings.append(TRACK_NUMBER_ORDER)
    elif (line in RANDOM_ORDER_CODES):
        settings.append(RANDOM_ORDER)

    line = file.readline().strip()
    print(line)
    if line is "":
        settings.append(0)
    else:
        settings.append(int(line))

    return settings


def orderTitle(songs):
    songTitles = []
    nrSongs = len(songs)
    for currentSong in range(0, nrSongs):
        try:
            songFile = EasyID3(songs[currentSong])
            songTitles.append(songFile["title"])
        except:
            songTitles.append(-1)
            print("Error")
    
    for i in range(0, nrSongs):
        for j in range(0, nrSongs - 1):
            if (min(songTitles[j], songTitles[j + 1]) == songTitles[j + 1]):
                songTitles[j], songTitles[j + 1] = songTitles[j + 1], songTitles[j]
                songs[j], songs[j + 1] = songs[j + 1], songs[j]
    return songs
def orderProducer(songs):
    songProducers = []
    nrSongs = len(songs)
    for currentSong in range(0, nrSongs):
        try:
            songFile = EasyID3(songs[currentSong])
            songProducers.append(songFile["artist"])
        except:
            songProducers.append(-1)
            print("Error")
    
    for i in range(0, nrSongs):
        for j in range(0, nrSongs - 1):
            if (min(songProducers[j], songProducers[j + 1]) == songProducers[j + 1]):
                songProducers[j], songProducers[j + 1] = songProducers[j + 1], songProducers[j]
                songs[j], songs[j + 1] = songs[j + 1], songs[j]
    return songs
def orderTrackNumber(songs):
    songNumbers = []
    nrSongs = len(songs)
    for currentSong in range(0, nrSongs):
        try:
            songFile = EasyID3(songs[currentSong])

            convertedString = ""
            for letter in songFile["tracknumber"]:
                convertedString += letter
            songNumbers.append(int(convertedString))
        except:
            songNumbers.append(0)
            print("Error")
    
    for i in range(0, nrSongs):
        for j in range(0, nrSongs - 1):
            if (songNumbers[j] > songNumbers[j + 1]):
                songNumbers[j], songNumbers[j + 1] = songNumbers[j + 1], songNumbers[j]
                songs[j], songs[j + 1] = songs[j + 1], songs[j]

    return songs


def playSongs(songs, playOrder, startSong):
    nrSongs = len(songs)
    currentSong = startSong
    while 1:
        player = vlc.MediaPlayer(songs[currentSong])
        player.play()
        print("Now playing \"{}\"".format(songs[currentSong][:-4]))

        while player.get_state() != vlc.State.Ended:
            sleep(0.1)

            if keyboard.kbhit():
                key = keyboard.getch()
                if key is b"p":
                    player.pause()
                elif key is b"s":
                    settingsFile = open(SETTINGS_FILENAME, "w")
                    settingsFile.write("{}\n".format(playOrder))
                    if playOrder is not RANDOM_ORDER: settingsFile.write("{}\n".format(currentSong))
                    return
                elif key is b"e":
                    return
                elif key is b"\xe0":
                    key = keyboard.getch()
                    if key is ARROW_UP or key is ARROW_DX:
                        player.stop()
                        break
                    elif (key is ARROW_DN or key is ARROW_SX) and (currentSong > 0):
                        player.stop()
                        currentSong -= 2
                        break

        currentSong += 1
        if (currentSong >= nrSongs): currentSong = 0


def main():
    songs = getSongs()

    settings = getSettings()
    print(settings)
    if (settings[0] == TITLE_ORDER):
        songs = orderTitle(songs)
    elif (settings[0] == PRODUCER_ORDER):
        songs = orderProducer(songs)
    elif (settings[0] == TRACK_NUMBER_ORDER):
        songs = orderTrackNumber(songs)
    elif (settings[0] == RANDOM_ORDER):
        random.shuffle(songs)
        
    print(songs)
    playSongs(songs, settings[0], settings[1])


main()
