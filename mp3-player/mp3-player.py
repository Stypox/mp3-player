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


#keyboard input
if OS_NAME == OS_WINDOWS:
	import msvcrt
	class Keyboard:
		class Event(Enum):
			none = -1
			abort = 0
			save = 1
			pause = 2
			restart = 3
			nextSong = 4
			prevSong = 5
			nextPlaylist = 6
			prevPlaylist = 7
		
		@staticmethod
		def init():
			pass
		@staticmethod
		def hit():
			return msvcrt.kbhit()
		@staticmethod
		def getEvent():
			if Keyboard.hit():
				readChar = sys.stdin.read(1)
			else:
				return Keyboard.Event.none

			while Keyboard.hit():
				readChar = sys.stdin.read(1)
			if readChar == '\x1B':				#TODO not sure if this works on windows
				readChar = sys.stdin.read(1)
				if readChar == '[':
					readChar += sys.stdin.read(1)
					
			if readChar in ABORT_KEYS:
				return Keyboard.Event.abort
			elif readChar in SAVE_KEYS:
				return Keyboard.Event.save
			elif readChar in PAUSE_KEYS:
				return Keyboard.Event.pause
			elif readChar in NEXT_SONG_KEYS:
				return Keyboard.Event.nextSong
			elif readChar in PREV_SONG_KEYS:
				return Keyboard.Event.prevSong
			else:
				return Keyboard.Event.none
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
		class Event(Enum):
			none = -1
			abort = 0
			save = 1
			pause = 2
			restart = 3
			nextSong = 4
			prevSong = 5
			nextPlaylist = 6
			prevPlaylist = 7
		@staticmethod
		def init():
			atexit.register(TerminalSettings.setOld)
			TerminalSettings.setNew()
		@staticmethod
		def hit():
			return select.select([sys.stdin,],[],[],0.0)[0] != []
		@staticmethod
		def getEvent():
			if Keyboard.hit():
				readChar = sys.stdin.read(1)
			else:
				return Keyboard.Event.none

			while Keyboard.hit():
				readChar = sys.stdin.read(1)
			if readChar == '\x1B':
				readChar = sys.stdin.read(1)
				if readChar == '[':
					readChar += sys.stdin.read(1)
					
			if readChar in ABORT_KEYS:
				return Keyboard.Event.abort
			elif readChar in SAVE_KEYS:
				return Keyboard.Event.save
			elif readChar in PAUSE_KEYS:
				return Keyboard.Event.pause
			elif readChar in RESTART_KEYS:
				return Keyboard.Event.restart
			elif readChar in NEXT_SONG_KEYS:
				return Keyboard.Event.nextSong
			elif readChar in PREV_SONG_KEYS:
				return Keyboard.Event.prevSong
			elif readChar in NEXT_PLAYLIST_KEYS:
				return Keyboard.Event.nextPlaylist
			elif readChar in PREV_PLAYLIST_KEYS:
				return Keyboard.Event.prevPlaylist
			else:
				return Keyboard.Event.none
	Keyboard.init()


class Song:
	def __init__(self, path):
		self.path = path
		try: self.songID3 = EasyID3(path)
		except: pass
	def __repr__(self):
		try:
			return self.songID3["title"][0]
		except KeyError:
			return self.path
	
	def title(self):
		try:
			return self.songID3["title"][0]
		except KeyError:
			return chr(0x10ffff)
	def artist(self):
		try:
			return self.songID3["artist"][0]
		except KeyError:
			return chr(0x10ffff)
	def trackNumber(self):
		try:
			return int(self.songID3["tracknumber"][0])
		except:
			return 0xffffffff
class Playlist:
	class EmptyDirectory(BaseException):
		def __init__(self, directory):
			self.directory = directory
		def what(self):
			return "Provided directory %s is empty" % self.directory

	def __init__(self, directory = None, playOrder = None, startSong = None):
		if directory is None:
			directory = "./"
		elif len(directory) > 0 and directory[-1] != "/":
			directory += "/"
		self.directory = directory
		
		self.playOrder = Order.cast(playOrder)
		if playOrder is not None and self.playOrder is None:
			raise RuntimeError("Invalid play order \"%s\" at playlist \"%s\" of type \"%s\"" % (playOrder, self.directory, type(playOrder)))

		try:
			self.currentSong = int(startSong)
		except TypeError:
			self.currentSong = None
		if startSong is not None and self.currentSong is None:
			raise RuntimeError("Invalid start song \"%s\" at playlist \"%s\" of type \"%s\"" % (startSong, self.directory, type(playOrder)))

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

		self.name = self.directory.split("/")[-1]

		self.loadSongs()
		self.sort()
		self.goBack(0)
	def __iter__(self):
		return self
	def __next__(self):
		if self.currentSong >= len(self.songs):
			self.currentSong = 0
		self.currentSong += 1
		return self.songs[self.currentSong - 1]
	
	def loadSongs(self):
		self.songs = []
		files = os.listdir(self.directory)
		for file in files:
			if file[-4:] == ".mp3":
				self.songs.append(Song(self.directory + file))
		if len(self.songs) == 0:
			raise Playlist.EmptyDirectory(self.directory)
	def writeSettings(self):
		settingsFile = open(self.directory + SETTINGS_FILENAME, "w")
		if self.playOrder == Order.random:
			settingsFile.write("%s\n%s" % (self.playOrder, 0))
		else:
			settingsFile.write("%s\n%s" % (self.playOrder, self.currentSong - 1))
	def sort(self, playOrder = None):
		if playOrder is None:
			playOrder = self.playOrder
		elif type(playOrder) is not Order:
			raise TypeError("Inappropiate type (%s) for play order, requires an Order value." % type(playOrder))
		if	 playOrder == Order.path:			self.songs = sorted(self.songs, key = lambda song: song.path)
		elif playOrder == Order.title:			self.songs = sorted(self.songs, key = lambda song: song.title())
		elif playOrder == Order.artist:			self.songs = sorted(self.songs, key = lambda song: song.artist())
		elif playOrder == Order.trackNumber:	self.songs = sorted(self.songs, key = lambda song: song.trackNumber())
		elif playOrder == Order.random:			random.shuffle(self.songs)
	def goBack(self, count = 2):
		if count < 0:
			raise ValueError
		self.currentSong -= count
		while self.currentSong < 0:
			self.currentSong += len(self.songs)
	def play(self):
		for song in self:
			player = vlc.MediaPlayer(song.path)
			player.play()
			print("Now playing: \"%s\" by \"%s\"" % (song.title(), song.artist()))
			paused = False

			while player.get_state() != vlc.State.Ended:
				sleep(0.1)

				nextAction = Keyboard.getEvent()
				if nextAction == Keyboard.Event.abort:
					print("Aborting...")
					return PlaylistsPlayer.Event.abort
				elif nextAction == Keyboard.Event.save:
					print("Saving...")
					return PlaylistsPlayer.Event.save
				elif nextAction == Keyboard.Event.pause:
					player.pause()
					paused = not paused
					if paused: print("Pause")
					else: print("Resume")
				elif nextAction == Keyboard.Event.restart:
					player.stop()
					self.currentSong = 0
					print("Restart")
					break
				elif nextAction == Keyboard.Event.nextSong:
					player.stop()
					break
				elif nextAction == Keyboard.Event.prevSong:
					player.stop()
					self.goBack()
					break
				elif nextAction == Keyboard.Event.nextPlaylist:
					player.stop()
					self.goBack(1)
					return PlaylistsPlayer.Event.next
				elif nextAction == Keyboard.Event.prevPlaylist:
					player.stop()
					self.goBack(1)
					return PlaylistsPlayer.Event.prev
		return PlaylistsPlayer.Event.next
class PlaylistsPlayer:
	class Event(Enum):
		next = 0
		prev = 1
		save = 2
		abort = 3

	def __init__(self, playlists):
		self.playlists = playlists
		self.currentPlaylist = 0
	
	def play(self):
		nrPlaylists = len(self.playlists)
		if nrPlaylists == 0:
			return
		
		while 1:
			print("Now playing playlist at \"%s\"" % self.playlists[self.currentPlaylist].directory)
			event = self.playlists[self.currentPlaylist].play()
			if event == PlaylistsPlayer.Event.next:
				self.currentPlaylist += 1
			elif event == PlaylistsPlayer.Event.prev:
				self.currentPlaylist -= 1
			elif event == PlaylistsPlayer.Event.save:
				self.save()
				return
			elif event == PlaylistsPlayer.Event.abort:
				return
			
			while self.currentPlaylist >= nrPlaylists:
				self.currentPlaylist -= nrPlaylists
			while self.currentPlaylist < 0:
				self.currentPlaylist += nrPlaylists
	def save(self):
		for playlist in self.playlists:
			playlist.writeSettings()


def parseArgsList(args, allArgs):
	try:
		if len(args) == 0:
			return None
		elif len(args) == 1:
			return Playlist(args[0])
		elif len(args) == 2:
			return Playlist(args[0], args[1])
		elif len(args) == 3:
			return Playlist(args[0], args[1], args[2])
		else:
			raise RuntimeError("Invalid arguments (list of arguments \"%s\" too long): \"%s\"" % (args, allArgs))
	except Playlist.EmptyDirectory as e:
		print(e.what())
		return None
def main(arguments):
	#arguments parsing
	playlists = []
	args = arguments[1:]
	if len(args) == 0:
		playlists.append(Playlist())
	else:
		tmpArgs = []
		for arg in args:
			if arg == "-":
				playlist = parseArgsList(tmpArgs, args)
				if type(playlist) is Playlist:
					playlists.append(playlist)
				tmpArgs = []
			tmpArgs.append(arg)
	playlist = parseArgsList(tmpArgs, args)
	if type(playlist) is Playlist:
		playlists.append(playlist)
	
	#playing songs
	if len(playlists) == 0:
		print("Nothing to play")
	player = PlaylistsPlayer(playlists)
	player.play()


if __name__ == '__main__':
	print("\n%s\nSTART %s\n%s\n" % ("-" * (6 + len(sys.argv[0])), sys.argv[0], "-" * (6 + len(sys.argv[0]))))
	main(sys.argv)
	print("\n%s\n END %s \n%s\n" % ("-" * (6 + len(sys.argv[0])), sys.argv[0], "-" * (6 + len(sys.argv[0]))))