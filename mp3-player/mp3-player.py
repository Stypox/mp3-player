#!/usr/bin/env python3

#os
import platform
OS_NAME = platform.system()
OS_WINDOWS = "Windows"
OS_LINUX = "Linux"

#music playing
import vlc

#file handling
import os
import fileinput
from mutagen.easyid3 import EasyID3

#misc
import random
from time import sleep
import sys
from enum import Enum, Flag
import argparse


SETTINGS_FILENAME = "mp3-player-settings.txt"
DIRECTORIES_FILENAME = "mp3-player-directories.txt"
FAVOURITES_FILENAME = "mp3-player-favourites.txt"

PATH_ORDER_CODES = ["0", "p", "path"]
TITLE_ORDER_CODES = ["1", "t", "title", "name"]
ARTIST_ORDER_CODES = ["2", "a", "artist", "author"]
TRACK_NUMBER_ORDER_CODES = ["3", "n", "number", "tracknumber"]
RANDOM_ORDER_CODES = ["4", "r", "random"]
MODIFIED_ORDER_CODES = ["m", "modified"]
class Order(Flag):
	path = 1
	title = 2
	artist = 4
	trackNumber = 8
	random = 16
	modified = 32
	
	none = 0
	default = trackNumber
	
	@staticmethod
	def cast(playOrder):
		if type(playOrder) is Order:
			return playOrder
		elif type(playOrder) is str:
			isModified, order = None, None
			if '-' in playOrder:
				isModified, order = playOrder.split('-', 1)
				if isModified in MODIFIED_ORDER_CODES:
					isModified = Order.modified
				else:
					return None
			else:
				isModified = Order.none
				order = playOrder

			if   order in PATH_ORDER_CODES:			return Order.alphabetical | isModified
			elif order in TITLE_ORDER_CODES:		return Order.title | isModified
			elif order in ARTIST_ORDER_CODES:		return Order.artist | isModified
			elif order in TRACK_NUMBER_ORDER_CODES:	return Order.trackNumber | isModified
			elif order in RANDOM_ORDER_CODES:		return Order.random | isModified
			else:
				try:
					return Order(int(playOrder))
				except:
					return None
		return None
	@staticmethod
	def toString(playOrder):
		if playOrder & Order.modified:
			return str(playOrder)[15:].replace('N', " n") + " with variations"
		else:
			return str(playOrder)[6:].replace('N', " n")

ABORT_KEYS = ['a', 'e']
SAVE_KEYS = ['s']
PAUSE_KEYS = ['p', '\n']
RESTART_KEYS = ['r', '[H']
NEXT_SONG_KEYS = ['[B', '[C']
PREV_SONG_KEYS = ['[A', '[D']
NEXT_PLAYLIST_KEYS = ['[6']
PREV_PLAYLIST_KEYS = ['[5']

class Options:
	verbose = False
	quiet = False
	limitToConsoleWidth = False
	consoleWidth = int(os.popen('stty size', 'r').read().split()[1])
	playlists = []

	argParser = argparse.ArgumentParser(prog="mp3-player.py")
	argParser.add_argument('-q', '--quiet', action='store_true', default=False, help="do not print anything")
	argParser.add_argument('-v', '--verbose', action='store_true', default=False, help="print more debug information")
	argParser.add_argument('-w', '--limit-to-console-width', action='store_true', default=False, help="print to the console only part of the output so that it can fit in the console width")
	argParser.add_argument('-o', '--favourites-play-order', type=str, default=None, help="favourites play order. Must match [m|modified]-(p|path|t|title|a|artist|n|number|tracknumber|r|random)")
	argParser.add_argument('-s', '--favourites-start-song', type=int, default=None, help="favourites start index")
	argParser.add_argument('playlists', nargs='*', metavar='DIRECTORIES', help="playlists to play (DIRECTORY) starting from INDEX (defaults to 0). FORMAT must match [m|modified]-(p|path|t|title|a|artist|n|number|tracknumber|r|random) (defaults to random). Formatted this way: DIRECTORY [FORMAT] [INDEX] - ... - DIRECTORY [FORMAT] [INDEX]")

	@staticmethod
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
			log(LogLevel.warning, e.what())
			return None

	@staticmethod
	def parse(arguments):
		arguments = arguments[1:]
		opts = vars(Options.argParser.parse_args(arguments))
		Options.quiet = opts['quiet']
		Options.verbose = opts['verbose']
		Options.limitToConsoleWidth = opts['limit_to_console_width']

		favouritesPlayOrder = opts['favourites_play_order']
		favouritesStartSong = opts['favourites_start_song']

		Favourites.setup(favouritesPlayOrder, favouritesStartSong)

		playlistArgs = opts['playlists']
		if len(playlistArgs) == 0:
			try:
				with open(DIRECTORIES_FILENAME) as directoriesFile:
					for line in directoriesFile:
						playlist = Options.parseArgsList(line, DIRECTORIES_FILENAME)
						if type(playlist) is Playlist:
							Options.playlists.append(playlist)
					if len(playlist) == 0:
						log(LogLevel.warning, "Empty file \"%s\"" % DIRECTORIES_FILENAME)
			except:
				log(LogLevel.warning, "No command line arguments and no \"%s\" file found: using current directory" % DIRECTORIES_FILENAME)
				try: Options.playlists.append(Playlist("./"))
				except Playlist.EmptyDirectory as e: log(LogLevel.warning, e.what())
		else:
			tmpArgs = []
			for arg in playlistArgs:
				if arg == "-":
					playlist = Options.parseArgsList(tmpArgs, playlistArgs)
					if type(playlist) is Playlist:
						Options.playlists.append(playlist)
					tmpArgs = []
				else:
					tmpArgs.append(arg)
			playlist = Options.parseArgsList(tmpArgs, playlistArgs)
			if type(playlist) is Playlist:
				Options.playlists.append(playlist)

class LogLevel(Enum):
	debug = 0,
	info = 1,
	warning = 2,
	error = 3
def log(level, *args, **kwargs):
	if not Options.quiet:
		if level == LogLevel.error:
			print("[error]", *args, **kwargs)
		else:
			if Options.limitToConsoleWidth:
				separator = kwargs.get('sep', " ")
				end = kwargs.get('end', "\n")
				newKwargs = {}
				for key, value in kwargs.items():
					if key != 'sep' and key != 'end':
						newKwargs[key] = value

				toPrint = ""
				if level == LogLevel.debug and Options.verbose:
					toPrint = "[debug] "
				elif level == LogLevel.info:
					toPrint = ""
				elif level == LogLevel.warning:
					toPrint = "[warning] "
				else:
					return
					
				firstTime = True
				for arg in args:
					if firstTime:
						toPrint += arg.__str__()
					else:
						toPrint += separator + arg.__str__()
					firstTime = False
				toPrint += end

				lines = toPrint.split("\n")
				toPrint = ""
				for line in lines:
					if len(line) > Options.consoleWidth:
						toPrint += line[:Options.consoleWidth]
					else:
						toPrint += line + "\n"
				if toPrint[-1] == "\n":
					toPrint = toPrint[:-1]

				print(toPrint, sep="", end="", **newKwargs)
			else:
				if level == LogLevel.debug and Options.verbose:
					print("[debug]", *args, **kwargs)
				elif level == LogLevel.info:
					print(*args, **kwargs)
				elif level == LogLevel.warning:
					print("[warning]", *args, **kwargs)

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
		log(LogLevel.error, "The operating system \"%s\" may not be supported" % OS_NAME)
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
	invalidArtist = invalidTitle = chr(0x10ffff)
	invalidTrackNumber = 0xffffffff

	def __init__(self, path):
		self.path = path
		try: self.songID3 = EasyID3(path)
		except: log(LogLevel.debug, "Unable to read ID3 tags for song at \"%s\"" % path)
	def __repr__(self):
		try:
			return self.songID3["title"][0]
		except:
			return self.path
	
	def title(self):
		try:
			return self.songID3["title"][0]
		except:
			return Song.invalidTitle
	def artist(self):
		try:
			return self.songID3["artist"][0]
		except:
			return Song.invalidArtist
	def trackNumber(self):
		try:
			return int(self.songID3["tracknumber"][0])
		except:
			return Song.invalidTrackNumber

class Favourites:
	@staticmethod
	def setup(playOrder, startSong):
		songFilenames, filePlayOrder, fileStartSong = Favourites.loadFromFile()

		Favourites.songs = [Song(songFilename) for songFilename in songFilenames]
		if len(Favourites.songs) == 0:
			log(LogLevel.warning, "Favourites playlist is empty")
		
		if playOrder is None:
			if filePlayOrder is None:
				Favourites.playOrder = Order.default
			else:
				Favourites.playOrder = filePlayOrder
		else:
			Favourites.playOrder = Order.cast(playOrder)
			if playOrder is not None and Favourites.playOrder is None:
				raise RuntimeError("Invalid play order \"%s\" for favourites of type \"%s\"" % (playOrder, type(playOrder)))
		
		if startSong is None:
			if fileStartSong is None:
				Favourites.currentSong = 0
			else:
				Favourites.currentSong = fileStartSong
		else:
			Favourites.playOrder = startSong
		#this is done since __next__ does += 1 even the first time
		Favourites.currentSong -= 1
	def __iter__(self):
		return self
	def __next__(self):
		Favourites.currentSong += 1
		Favourites.currentSong %= len(Favourites.songs)
		return Favourites.songs[Favourites.currentSong]

	@staticmethod
	def loadFromFile():
		try:
			with open(FAVOURITES_FILENAME) as favouritesFile:
				playOrder = favouritesFile.readline().strip()
				startSong = favouritesFile.readline().strip()

				playOrder = Order.cast(playOrder)
				try: startSong = int(startSong)
				except ValueError: startSong = None

				songFilenames = [line.strip() for line in favouritesFile]

				return (songFilenames, playOrder, startSong)
		except FileNotFoundError:
			return ([], None, None)
	@staticmethod
	def writeSettings():
		with open(FAVOURITES_FILENAME, "w") as favouritesFile:
			if Favourites.playOrder == Order.random:
				favouritesFile.write("%s\n%s\n" % (Favourites.playOrder.value, 0))
			else:
				favouritesFile.write("%s\n%s\n" % (Favourites.playOrder.value, Favourites.currentSong))
			favouritesFile.write("\n".join([song.path for song in Favourites.songs]))
	@staticmethod
	def add(song):
		Favourites.songs.append(song)

class Playlist:
	class EmptyDirectory(BaseException):
		def __init__(self, directory):
			self.directory = directory
		def what(self):
			return "Provided directory %s is empty" % self.directory

	def __init__(self, directoryOrFilenames, playOrder = None, startSong = None):
		if type(directoryOrFilenames) is str:
			if len(directoryOrFilenames) > 0 and directoryOrFilenames[-1] != "/":
				directoryOrFilenames += "/"
			self.directory = directoryOrFilenames
			
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
					with open(self.directory + SETTINGS_FILENAME) as settingsFile:
						filePlayOrder = settingsFile.readline().strip()
						fileStartSong = settingsFile.readline().strip()

						if self.playOrder is None:
							self.playOrder = Order.cast(filePlayOrder)
						if self.currentSong is None:
							try: self.currentSong = int(fileStartSong)
							except ValueError: pass
				except FileNotFoundError: pass
					
				if self.playOrder is None:
					self.playOrder = Order.default
				if self.currentSong is None or self.playOrder is Order.random:
					self.currentSong = 0

			self.name = self.directory.split("/")[-1]

			self.loadSongs()
		elif type(directoryOrFilenames) is list:
			self.playOrder = Order.cast(playOrder)
			if playOrder is not None and self.playOrder is None:
				raise RuntimeError("Invalid play order \"%s\" for favourites of type \"%s\"" % (playOrder, type(playOrder)))

			self.currentSong = startSong

			self.songs = []
			for filename in directoryOrFilenames:
				self.songs.append(Song(filename))			
		else:
			raise TypeError()

		self.sort()
		#this is done since __next__ does += 1 even the first time
		self.currentSong -= 1
	def __iter__(self):
		return self
	def __next__(self):
		self.currentSong += 1
		self.currentSong %= len(self.songs)
		return self.songs[self.currentSong]
	
	def loadSongs(self):
		self.songs = []
		files = os.listdir(self.directory)
		for file in files:
			if file[-4:] == ".mp3":
				self.songs.append(Song(self.directory + file))
		if len(self.songs) == 0:
			raise Playlist.EmptyDirectory(self.directory)
	def writeSettings(self):
		with open(self.directory + SETTINGS_FILENAME, "w") as settingsFile:
			if self.playOrder == Order.random:
				settingsFile.write("%s\n%s" % (self.playOrder.value, 0))
			else:
				settingsFile.write("%s\n%s" % (self.playOrder.value, self.currentSong))
	def sort(self, playOrder = None):
		if playOrder is None:
			playOrder = self.playOrder
		elif type(playOrder) is not Order:
			raise TypeError("Inappropiate type (%s) for play order, requires an Order value." % type(playOrder))

		if playOrder & Order.random:
			random.shuffle(self.songs)
		else:
			if	 playOrder & Order.path:		self.songs = sorted(self.songs, key = lambda song: song.path)
			elif playOrder & Order.title:		self.songs = sorted(self.songs, key = lambda song: song.title())
			elif playOrder & Order.artist:		self.songs = sorted(self.songs, key = lambda song: song.artist())
			elif playOrder & Order.trackNumber:	self.songs = sorted(self.songs, key = lambda song: song.trackNumber())
			
			if playOrder & Order.modified:
				if len(self.songs) < 5:
					random.shuffle(self.songs)				
				for i in range(0, len(self.songs) - 5, 4):
					self.songs[i:i+5] = sorted(self.songs[i:i+5], key=lambda s: random.random())

class PlaylistsPlayer:
	class Event(Enum):
		next = 0
		prev = 1
		save = 2
		abort = 3

	def __init__(self, playlists):
		self.playlists = playlists
		self.currentPlaylist = 0
	
	@staticmethod
	def playPlaylist(playlist):
		for song in playlist:
			player = vlc.MediaPlayer(song.path)
			player.play()
			if song.artist() is Song.invalidArtist:
				log(LogLevel.info, "Playing %d/%d: \"%s\"" % (playlist.currentSong + 1, len(playlist.songs), song.title()))
			else:
				log(LogLevel.info, "Playing %d/%d: \"%s\" by \"%s\"" % (playlist.currentSong + 1, len(playlist.songs), song.title(), song.artist()))
			paused = False

			while player.get_state() != vlc.State.Ended:
				sleep(0.1)

				nextAction = Keyboard.getEvent()
				if nextAction == Keyboard.Event.abort:
					log(LogLevel.info, "Aborting...")
					return PlaylistsPlayer.Event.abort
				elif nextAction == Keyboard.Event.save:
					log(LogLevel.info, "Saving...")
					return PlaylistsPlayer.Event.save
				elif nextAction == Keyboard.Event.pause:
					player.pause()
					paused = not paused
					if paused: log(LogLevel.info, "Pause")
					else: log(LogLevel.info, "Resume")
				elif nextAction == Keyboard.Event.restart:
					player.stop()
					#this is done instead of = 0 since __next__ does += 1
					playlist.currentSong = -1
					log(LogLevel.info, "Restart")
					break
				elif nextAction == Keyboard.Event.nextSong:
					player.stop()
					break
				elif nextAction == Keyboard.Event.prevSong:
					player.stop()
					#this is done instead of -= 1 since __next__ does += 1
					playlist.currentSong -= 2
					break
				elif nextAction == Keyboard.Event.nextPlaylist:
					player.stop()
					#this is done since __next__ does += 1 even the first time
					playlist.currentSong -= 1
					return PlaylistsPlayer.Event.next
				elif nextAction == Keyboard.Event.prevPlaylist:
					player.stop()
					#this is done since __next__ does += 1 even the first time
					playlist.currentSong -= 1
					return PlaylistsPlayer.Event.prev
		return PlaylistsPlayer.Event.next

	def play(self):
		nrPlaylists = len(self.playlists)
		if nrPlaylists == 0:
			return
		
		while 1:
			if type(self.playlists[self.currentPlaylist]) is Playlist:
				log(LogLevel.info, 'Now playing playlist at "%s", sorted by %s' % (
					self.playlists[self.currentPlaylist].directory,
					Order.toString(self.playlists[self.currentPlaylist].playOrder)))
			else:
				log(LogLevel.info, 'Now playing favourites, sorted by %s' % (
					Order.toString(self.playlists[self.currentPlaylist].playOrder)))
			event = PlaylistsPlayer.playPlaylist(self.playlists[self.currentPlaylist])
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


def main(arguments):
	#arguments parsing
	Options.parse(arguments)

	#playing songs
	player = PlaylistsPlayer(Options.playlists)
	player.play()


if __name__ == '__main__':
	main(sys.argv)