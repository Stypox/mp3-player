# Mp3 player
Plays playlists of MP3s **sorted** by **track number**, by title, **randomly**... **Remembers the song being played** and the sorting settings before exiting. Can be controlled by pressing **keyboard keys**.
##### Useful in combination with my youtube [playlist-downloader](https://gitlab.com/Stypox/playlist-downloader) that saves song metadata.

# Keyboard controls
The script uses **keyboard input**, instead of console input, since it's **simpler** and more **convenient**. Note that the console window must be focused for this to work. For example by pressing ``p`` the music pauses. This is the complete list of **keybindings** (**\|** means or):

	Abort without saving:                              a | e
	Save current song and sorting settings, then exit: s
	Pause and resume:                                  p | Enter
	Restart: ......................................... r | Home (*)
	Next song:                                         Arrow down | Arrow right
	Previous song: ................................... Arrow up | Arrow left
	Next playlist:                                     Page up
	Previous playlist: ............................... Page down

In case the used console doesn't support direct keyboard input, **press Enter** after pressing a key, just like it was a normal console input.  
(*) ``Home`` is also known as ``Start`` or ``Beginning``, depending on the keyboard.

# Sorting
The script provides several ways to **sort songs** and uses [ID3 metadata](https://en.wikipedia.org/wiki/ID3) to get informations about MP3s. The **default** sort order is by **track number** and all sort orders have a **corresponding code** that the script uses to understand them (see [Usage](https://gitlab.com/Stypox/mp3-player#usage)):
* **Path**: sorts the songs based on their path in alphabetical order a-z 
(codes: "p" or "path")
* **Title**: sorts the songs based on their title in alphabetical order a-z 
(codes: "t" or "title")
* **Artist**: sorts the songs based on their artist in alphabetical order a-z 
(codes: "a" or "artist")
* **Track number**: sorts the songs based on their track number from bottom up 
(codes: "n" or "number" or "tracknumber")
* **Random**: randomly shuffles all the songs 
(codes: "r" or "random")
* **Modified** (prefix): after sorting the songs as requested, this modifier introduces some variability
(prefix codes: "m-" or "modified-")

For example: "p" -> sorted by path; "m-number" -> sorted by track number with some variability;


# Usage
Choose some **directories full of MP3**. Every directory is considered a **playlist** and processed separately from others. Inside every directory a file named ``mp3-player-settings.txt`` will be created containing the **settings for that directory** (for example the song to start with the next time that directory is played). These setting, if existing, will be **overwritten by manually provided parameters**. The directories I choose are "C:/path/to/songs/" and "./Music/".  

Then there are two ways to provide the script with those directories: using a **file** or using **command line arguments** (all parameters between **\[square brackets\]** are to be considered optional):

## Saving directories in file
In the directory the script is executed in create a file named ``mp3-player-directories.txt``. In that file you can insert the **directories to be played** this way:

	DIRECTORY [SORT_ORDER] [START_SONG]
	DIRECTORY [SORT_ORDER] [START_SONG]
	...

Here "DIRECTORY" represents the directory in which to **look for songs**; "SORT_ORDER" is **optional**, must be a **sorting code** (see [Sorting](https://gitlab.com/Stypox/mp3-player#sorting)), represents the **sort order** and defaults to track number order; "START_SONG" is **optional**, must be an **integer** (negative integers mean "count from the right"), represents the index of the **song to start with** and defaults to ``0``. **Save the file and run** the script. In this case the file could be:

	C:/path/to/songs/ random
	./Music/ modified-artist 15


## Passing directories as command line arguments
**Open a terminal** and navigate to the "DIRECTORY" the python script is in (run ``cd DIRECTORY``). Then run ``python3 FILENAME ARGUMENTS`` (*) replacing "FILENAME" with the name of the script. "ARGUMENTS" is the list of **directories to be played** and must be formatted this way:

	DIRECTORY [SORT_ORDER] [START_SONG] - ... - DIRECTORY [SORT_ORDER] [START_SONG]

Here "DIRECTORY" represents the directory in which to **look for songs**; "SORT_ORDER" is **optional**, must be a **sorting code** (see [Sorting](https://gitlab.com/Stypox/mp3-player#sorting)), represents the **sort order** and defaults to track number order; "START_SONG" is **optional**, must be an **integer** (a negative integer means "count from the right"), represents the index of the **song to start with** and defaults to ``0``. For example (command line commands):

	> cd C:/mp3-player/
	> python3 mp3-player.py C:/path/to/songs/ random - ./Music/ modified-artist 15

(*) Note that the command used for Python is **not always** ``python3``: it could be ``py``, ``python``, ``python3.6`` or others too.

## Result
The music should start playing! Now you can use keys to navigate through songs and playlist, see [Keyboard controls](https://gitlab.com/Stypox/mp3-player#keyboard-controls).
# Requirements
* Requires either **[Python 3.6.x](https://www.python.org/downloads/)** or **[Python 3.7.x](https://www.python.org/downloads/)** (I didn't test older versions, but newer ones may work).
* Requires the following **modules** installed: [python-vlc](https://pypi.org/project/python-vlc/); [mutagen](https://pypi.org/project/mutagen/).  
  [Install them using ``pip``](https://packaging.python.org/tutorials/installing-packages/).
# Notes
* When using random sort order the order of songs is **different every time** the script is executed.
* Start song argument is **useless** when the sort order is random, so it's **not saved** in ``mp3-player-settings.txt``.
* When out-of-range indices are provided as "START_SONG" they will be **normalized** using modulus.