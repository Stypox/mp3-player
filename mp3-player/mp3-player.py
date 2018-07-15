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
DIRECTORIES_FILENAME = "mp3-player-directories.txt"

PATH_ORDER_CODES = ["0", "p", "path"]
TITLE_ORDER_CODES = ["1", "t", "title", "name"]
ARTIST_ORDER_CODES = ["2", "a", "artist", "author"]
TRACK_NUMBER_ORDER_CODES = ["3", "n", "numerical", "track", "track number", "tracknumber", "number"]
RANDOM_ORDER_CODES = ["4", "r", "random", "rand"]
class Order(Enum):
	path = 0
	title = 1
	artist = 2
	trackNumber = 3
	random = 4
	default = trackNumber
	
	@staticmethod
	def cast(playOrder):
		if type(playOrder) is Order:
			return playOrder
		elif type(playOrder) is str:
			if   playOrder in PATH_ORDER_CODES:			return Order.alphabetical
			elif playOrder in TITLE_ORDER_CODES:		return Order.title
			elif playOrder in ARTIST_ORDER_CODES:		return Order.artist
			elif playOrder in TRACK_NUMBER_ORDER_CODES:	return Order.trackNumber
			elif playOrder in RANDOM_ORDER_CODES:		return Order.random
		return None

ABORT_KEYS = ['e', 'a']
SAVE_KEYS = ['s']
PAUSE_KEYS = ['p', '\n']
RESTART_KEYS = ['r', '[H']
NEXT_SONG_KEYS = ['[B', '[C']
PREV_SONG_KEYS = ['[A', '[D']
NEXT_PLAYLIST_KEYS = ['[6']
PREV_PLAYLIST_KEYS = ['[5']
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
	def __repr__(self):
		if self.ID3fail: return self.path
		return self.songID3["title"][0]
	
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
class Playlist:
	def __init__(self, directory = None, playOrder = None, startSong = None):
		if directory is None:
			directory = "./"
		elif len(directory) > 0 and directory[-1] != "/":
			directory += "/"
		self.directory = directory
		
		self.playOrder = Order.cast(playOrder)
		if playOrder is not None and self.playOrder is None:
			raise RuntimeError("Invalid play order at playlist %s" % self.directory)

		try:
			self.currentSong = int(startSong)
		except ValueError:
			self.currentSong = None
		if startSong is not None and self.currentSong is None:
			raise RuntimeError("Invalid start song at playlist %s" % self.directory)

		if self.playOrder is None or self.currentSong is None:
			try:
				settingsFile = open(directory + SETTINGS_FILENAME, "r")
				filePlayOrder = settingsFile.readline().strip()
				fileStartSong = settingsFile.readline().strip()

				self.playOrder = Order.cast(filePlayOrder)
				try:
					self.currentSong = int(fileStartSong)
				except ValueError: pass
			except FileNotFoundError: pass
				
			if self.playOrder is None:
				self.playOrder = Order.default
			if self.currentSong is None:
				self.currentSong = 0

		loadSongs()
		sort()
	def __next__(self):
		if self.currentSong == len(self.songs):
			self.currentSong = 0
			raise StopIteration
		return self.songs[currentSong]
		self.currentSong += 1
	
	def loadSongs(self):
		self.songs = []
		try:
			files = os.listdir(self.directory)
			for file in files:
				if file[-4:] == ".mp3":
					self.songs.append(Song(songsDirectory + file))
		except FileNotFoundError:
			print("No such file or directory: \"%s\"" % songsDirectory)
		if len(self.songs) == 0:
			raise ValueError
	def writeSettings(self):
		settingsFile = open(self.directory + SETTINGS_FILENAME, "w")
		if self.playOrder == Order.random:
			settingsFile.write("%s\n%s" % (playOrder, 0))
		else:
			settingsFile.write("%s\n%s" % (playOrder, startSong))
	def sort(self, playOrder = None):
		if playOrder = None:
			playOrder = self.playOrder
		if	 playOrder == Order.alphabetical	self.songs = sorted(self.songs, key = lambda song: song.path)
		elif playOrder == Order.title:			self.songs = sorted(self.songs, key = lambda song: song.title())
		elif playOrder == Order.artist:			self.songs = sorted(self.songs, key = lambda song: song.artist())
		elif playOrder == Order.trackNumber:	self.songs = sorted(self.songs, key = lambda song: song.trackNumber())
		elif playOrder == Order.random:			random.shuffle(self.songs)
	def goBack(self):
		self.currentSong -= 2
		while self.currentSong < 0:
			self.currentSong += len(songs)


def play(playlists):
	while 1:
		for playlist in playlists:
			for song in playlist:
				player = vlc.MediaPlayer(song.path)
				player.play()
				print("Now playing: \"%s\" by \"%s\"" % (song.title(), song.artist()))
				paused = False

				while player.get_state() != vlc.State.Ended:
					sleep(0.1)

					nextAction = Keyboard.getAction()
					if nextAction == Action.abort:
						print("Aborting...")
						return False
					elif nextAction == Action.save:
						print("Saving...")
						return True
					elif nextAction == Action.pause:
						player.pause()
						paused = not paused
						if paused: print("Pause")
						else: print("Resume")
					elif nextAction == Action.nextSong:
						player.stop()
						break
					elif nextAction == Action.prevSong:
						player.stop()
						playlist.goBack()
						break
					elif nextAction == Action.restart:
						player.stop()
						currentSong = -1
						print("Restart")
						break


def main(arguments):
	songsDirectory, playOrder, startSong = readSettings(arguments)
	print(songsDirectory, playOrder, startSong)
	
	songs = getSongs(songsDirectory)

	if   playOrder == Order.title:			songs = sorted(songs, key = lambda song: song.title())
	elif playOrder == Order.artist:			songs = sorted(songs, key = lambda song: song.artist())
	elif playOrder == Order.trackNumber:	songs = sorted(songs, key = lambda song: song.trackNumber())
	elif playOrder == Order.random:			random.shuffle(songs)
	
	print(*songs, sep="   ")
	playSongs(songs, songsDirectory, playOrder, startSong)


if __name__ == '__main__':
	print("\n%s\nSTART %s\n%s\n" % ("-" * (6 + len(sys.argv[0])), sys.argv[0], "-" * (6 + len(sys.argv[0]))))
	main(sys.argv)
	print("\n%s\n END %s \n%s\n" % ("-" * (6 + len(sys.argv[0])), sys.argv[0], "-" * (6 + len(sys.argv[0]))))