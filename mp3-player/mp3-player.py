#!/usr/bin/env python3

#os
import platform
OS_NAME = platform.system()
OS_WINDOWS = "Windows"
OS_LINUX = "Linux"

#misc
import vlc
import os
import fileinput
import random
from time import sleep
from mutagen.easyid3 import EasyID3
import sys
from enum import Enum


SETTINGS_FILENAME = "mp3-player-settings.txt"
DEFAULT_SONGS_DIRECTORY = "./mp3-player-songs/"

ALPHABETICAL_ORDER_CODES = ["0", "a", "alphabetical", "alphabet"]
TITLE_ORDER_CODES = ["1", "t", "title", "name"]
ARTIST_ORDER_CODES = ["2", "p", "producer", "artist", "author"]
TRACK_NUMBER_ORDER_CODES = ["3", "n", "numerical", "track", "track number", "number"]
RANDOM_ORDER_CODES = ["4", "r", "random", "rand"]
class Order(Enum):
	alphabetical = 0
	title = 1
	artist = 2
	trackNumber = 3
	random = 4
	default = trackNumber

ABORT_KEYS = ['e', 'a']
SAVE_KEYS = ['s']
PAUSE_KEYS = ['p', '\n']
RESTART_KEYS = ['r', '[H']
NEXT_SONG_KEYS = ['[B', '[C', '[6']
PREV_SONG_KEYS = ['[A', '[D', '[5']
class Action(Enum):
	none = -1
	abort = 0
	save = 1
	pause = 2
	nextSong = 3
	prevSong = 4
	restart = 5


#keyboard input
if OS_NAME == OS_WINDOWS:
	import msvcrt
	class Keyboard:
		@staticmethod
		def init():
			pass
		@staticmethod
		def hit():
			return msvcrt.kbhit()
		@staticmethod
		def getAction():
			if Keyboard.hit():
				readChar = sys.stdin.read(1)
			else:
				return Action.none

			while Keyboard.hit():
				readChar = sys.stdin.read(1)
			if readChar == '\x1B':				#not sure if this works on windows
				readChar = sys.stdin.read(1)
				if readChar == '[':
					readChar += sys.stdin.read(1)
					
			if readChar in ABORT_KEYS:
				return Action.abort
			elif readChar in SAVE_KEYS:
				return Action.save
			elif readChar in PAUSE_KEYS:
				return Action.pause
			elif readChar in NEXT_SONG_KEYS:
				return Action.nextSong
			elif readChar in PREV_SONG_KEYS:
				return Action.prevSong
			else:
				return Action.none
else:
	if (OS_NAME != OS_LINUX):
		print("The operating system \"%s\" may not be supported" % OS_NAME)
	import termios, atexit, select
	class TerminalSettings:
		fileDescriptor = sys.stdin.fileno()
		old = termios.tcgetattr(fileDescriptor)
		new = old[:3] + [old[3] & ~termios.ICANON & ~termios.ECHO] + old[4:]

		@staticmethod
		def setOld():
			termios.tcsetattr(TerminalSettings.fileDescriptor, termios.TCSAFLUSH, TerminalSettings.old)
		@staticmethod
		def setNew():
			termios.tcsetattr(TerminalSettings.fileDescriptor, termios.TCSAFLUSH, TerminalSettings.new)
	class Keyboard:
		@staticmethod
		def init():
			atexit.register(TerminalSettings.setOld)
			TerminalSettings.setNew()
		@staticmethod
		def hit():
			return select.select([sys.stdin,],[],[],0.0)[0] != []
		@staticmethod
		def getAction():
			if Keyboard.hit():
				readChar = sys.stdin.read(1)
			else:
				return Action.none

			while Keyboard.hit():
				readChar = sys.stdin.read(1)
			if readChar == '\x1B':
				readChar = sys.stdin.read(1)
				if readChar == '[':
					readChar += sys.stdin.read(1)
					
			if readChar in ABORT_KEYS:
				return Action.abort
			elif readChar in SAVE_KEYS:
				return Action.save
			elif readChar in PAUSE_KEYS:
				return Action.pause
			elif readChar in NEXT_SONG_KEYS:
				return Action.nextSong
			elif readChar in PREV_SONG_KEYS:
				return Action.prevSong
			elif readChar in RESTART_KEYS:
				return Action.restart
			else:
				return Action.none
	Keyboard.init()


class Song:
	def __init__(self, path):
		self.path = path
		try: self.songID3 = EasyID3(path)
		except: self.ID3fail = True
		self.ID3fail = False
	
	def title(self):
		if self.ID3fail or self.songID3["title"][0] == "": return chr(0x10ffff)
		return self.songID3["title"][0]
	def artist(self):
		if self.ID3fail or self.songID3["artist"][0] == "": return chr(0x10ffff)
		return self.songID3["artist"][0]
	def trackNumber(self):
		if self.ID3fail: return 0xffffffff
		try:
			return int(self.songID3["tracknumber"][0])
		except:
			return 0xffffffff

	def __repr__(self):
		if self.ID3fail: return self.path
		return self.songID3["title"][0]


def getSongs(songsDirectory):
	try: files = os.listdir(songsDirectory)
	except FileNotFoundError:
		print("No such file or directory: \"%s\"" % songsDirectory)
		return []
	songs = []
	for file in files:
		if file[-4:] == ".mp3":
			songs.append(Song(songsDirectory + file))
	return songs
def readSettings(arguments):
	songsDirectory = ""
	playOrder = ""
	startSong = ""
	try:
		settingsFile = open(SETTINGS_FILENAME, "r")
		songsDirectory = settingsFile.readline().strip()
		playOrder = settingsFile.readline().strip()
		startSong = settingsFile.readline().strip()
	except FileNotFoundError:
		pass

	if len(arguments) > 1:
		songsDirectory = arguments[1]
		if len(arguments) > 2:
			playOrder = arguments[2]
			if len(arguments) > 3:
				startSong = arguments[3]
		
	
	if songsDirectory == "":
		songsDirectory = DEFAULT_SONGS_DIRECTORY
	elif songsDirectory[-1] != '/':
		songsDirectory += '/'
	
	if   playOrder in ALPHABETICAL_ORDER_CODES:	playOrder = Order.alphabetical
	elif playOrder in TITLE_ORDER_CODES:		playOrder = Order.title
	elif playOrder in ARTIST_ORDER_CODES:		playOrder = Order.artist
	elif playOrder in TRACK_NUMBER_ORDER_CODES:	playOrder = Order.trackNumber
	elif playOrder in RANDOM_ORDER_CODES:		playOrder = Order.random
	else:										playOrder = Order.default

	try: startSong = int(startSong)
	except ValueError: startSong = 0

	return [songsDirectory, playOrder, startSong]
def writeSettings(songsDirectory, playOrder, startSong):
	if playOrder == Order.random:
		startSong = 0
	settingsFile = open(SETTINGS_FILENAME, "w")
	settingsFile.write("%s\n%s\n%s" % (songsDirectory, playOrder, startSong))


def playSongs(songs, songsDirectory, playOrder, startSong):
	nrSongs = len(songs)
	if nrSongs == 0: return
	currentSong = startSong

	while 1:
		player = vlc.MediaPlayer(songs[currentSong].path)
		player.play()
		print("Now playing \"%s\""% songs[currentSong].title())

		while player.get_state() != vlc.State.Ended:
			sleep(0.1)

			nextAction = Keyboard.getAction()
			if nextAction == Action.abort:
				return
			elif nextAction == Action.save:
				writeSettings(songsDirectory, playOrder, currentSong)
				return
			elif nextAction == Action.pause:
				player.pause()
			elif nextAction == Action.nextSong:
				player.stop()
				break
			elif nextAction == Action.prevSong:
				player.stop()
				currentSong -= 2
				break
			elif nextAction == Action.restart:
				player.stop()
				currentSong = -1
				break

		currentSong += 1
		if (currentSong >= nrSongs): currentSong = 0
		elif (currentSong < 0): currentSong += nrSongs


def main(arguments):
	songsDirectory, playOrder, startSong = readSettings(arguments)
	print(songsDirectory, playOrder, startSong)
	
	songs = getSongs(songsDirectory)

	if   playOrder == Order.title:			songs = sorted(songs, key = lambda song: song.title())
	elif playOrder == Order.artist:			songs = sorted(songs, key = lambda song: song.artist())
	elif playOrder == Order.trackNumber:	songs = sorted(songs, key = lambda song: song.trackNumber())
	elif playOrder == Order.random:			random.shuffle(songs)
	
	print(songs)
	playSongs(songs, songsDirectory, playOrder, startSong)


if __name__ == '__main__':
	main(sys.argv)