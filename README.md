# Sublime Tweet #

Sublime Tweet is an open source twitter plugin for [Sublime Text 2][sublime] editor. 

It allows you to read and post tweets right from our favorite Sublime Text 2!

## Updates ##

* (22 Oct 2011) Sublime Tweet now can `favorite`, `retweet`, `reply` and `open URLs` from tweets!

## Installation ##

### With Package Control (not yet available) ###

If you have the [Package Control][package_control] installed, you can install Sublime Tweet from inside Sublime Text itself. Open the Command Palette and select "Package Control: Install Package", then search for Sublime Tweet and you're done!

### Without Package Control ###

Go to your Sublime Text 2 Packages directory:

	Windows: %USERPROFILE%\AppData\Roaming\Sublime Text 2\Packages\

	Mac: ~/Library/Application Support/Sublime Text 2/Packages/	

and clone the repository there
	
	git clone git://github.com/rozboris/Sublime-Tweet.git "Sublime Tweet"


## How to tweet ##

* `Tools → Tweet`

* `Tweet` in Command Palette

* `{ "keys": ["ctrl+shift+t"], "command": "tweet" }`

## How to read your public timeline, `favorite`, `retweet`, `reply` or `open URLs` ##

* `Tools → Read twitter timeline`

* `Twitter` in Command Palette

* `{ "keys": ["ctrl+shift+c"], "command": "read_tweets" }`

You'll see a list of letest tweets in your timeline. Just hit Enter on a tweet to favorite, retweet, reply or open an URL from the tweet.

##First run##

On the first run of Sublime Tweet you will be prompted to authorize it, don't be surprised. You should do it only once.

---------

It's an early beta now, please submit all bugs found.

[sublime]: http://www.sublimetext.com/2
[package_control]: http://wbond.net/sublime_packages/package_control