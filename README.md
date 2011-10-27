# Sublime Tweet #

Sublime Tweet is an open source twitter plugin for [Sublime Text 2][sublime] editor. 

It allows you to read and post tweets right from our favorite Sublime Text 2!

## Updates ##

* (22 Oct 2011) Sublime Tweet now can `favorite`, `retweet`, `reply` and `open URLs` from tweets!

* (23 Oct 2011) Added `Related tweets` and `Mark new tweets` features

* (25 Oct 2011) Added proxy support

* (27 Oct 2011) Added proxy support to authorization

## Installation ##

### With Package Control ###

If you have the [Package Control][package_control] installed, you can install Sublime Tweet from inside Sublime Text itself. Open the Command Palette and select "Package Control: Install Package", then search for Sublime Tweet and you’re done!

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

You’ll see a list of latest tweets in your timeline. Just hit Enter on a tweet to favorite, retweet, reply, get related tweets or open an URL from the tweet.

## How to set proxy to use ##

Note: *You currently can't sign in to Twitter through proxy, you can only use it, if you were authorised without proxy, sorry*

Go to your Sublime Text 2 Packages directory, locate `/User/SublimeTweet.settings` file and replace

    "twitter_proxy_config": null

with

	"twitter_proxy_config": {
	    "http": "hostname:port", 
	    "https": "hostname:port"
	}


## First run ##

On the first run of Sublime Tweet you will be prompted to authorize it, don’t be surprised. You should do it only once.

## Donate ##

If you like Sublime Tweet you can [donate][donate] to the author (via PayPal).

---------

[sublime]: http://www.sublimetext.com/2
[package_control]: http://wbond.net/sublime_packages/package_control
[donate]: https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=TVLQ2XQGFDS6Y&lc=US&item_name=Sublime%20Tweet&item_number=SublimeTweet&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted