# Sublime Tweet #

Sublime Tweet is an open source Twitter plugin for [Sublime Text 3][sublime] editor.

It allows you to read and post tweets right from our favorite Sublime Text 3!

**After 2 years of silence, I'm finally updating it to support ST3 and Python 3.3!**

## Updates ##

* (11 Feb 2014) Ported to Sublime Text 3, replaced underlying Twitter library, removed proxy support.

* (29 Feb 2012) Applied some patches, added `Back` button.

* (28 Oct 2011) Added proxy availability detection (now if you're using proxy at work you shouldn't turn it off at home, Sublime Tweet will handle it). Timeline now downloads in background and Sublime Text never freezes.

* (27 Oct 2011) Added proxy support to authorization

* (25 Oct 2011) Added proxy support

* (23 Oct 2011) Added `Related tweets` and `Mark new tweets` features

* (22 Oct 2011) Sublime Tweet now can `favorite`, `retweet`, `reply` and `open URLs` from tweets!

## Installation ##

### With Package Control ###

If you have the [Package Control][package_control] installed, you can install Sublime Tweet from inside Sublime Text. Open the Command Palette and select "Package Control: Install Package", then search for Sublime Tweet and you're done!

### Without Package Control ###

Install [Package Control][package_control] first. Then install Sublime Tweet.

## How to tweet ##

* `Tools → Tweet`

* `Tweet` in Command Palette

* `{ "keys": ["ctrl+alt+shift+t"], "command": "tweet" }`

## How to read your public timeline, `favorite`, `retweet`, `reply` or `open URLs` ##

* `Tools → Read twitter timeline`

* `Twitter timeline` in Command Palette

* `{ "keys": ["ctrl+shift+c"], "command": "read_tweets" }`

You'll see a list of latest tweets in your timeline. Just hit Enter on a tweet to favorite, retweet, reply, or open an URL from the tweet.

## First run ##

On the first run of Sublime Tweet you will be prompted to authorize it, don't be surprised. Default browser will be opened automatically, copy code from the page and paste it to text prompt in Sublime Text (on the bottom of the screen).

You should only do it once.

## Donate ##

If you like Sublime Tweet you can [donate][donate] to the author (via PayPal).

---------

[sublime]: http://www.sublimetext.com/3
[package_control]: https://sublime.wbond.net/installation
[donate]: https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=TVLQ2XQGFDS6Y&lc=US&item_name=Sublime%20Tweet&item_number=SublimeTweet&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted