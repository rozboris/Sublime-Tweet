# Sublime Tweet #

Sublime Tweet is an open source twitter plugin for [Sublime Text 2][sublime] editor. It allows you to tweet right from our favorite Sublime Text 2!

## Installation ##

### With Package Control ###

If you have the [Package Control][package_control] package installed, you can install Sublime Tweet from inside Sublime Text itself. Open the Command Palette and select "Package Control: Install Package", then search for Sublime Tweet and you're done!

### Without Package Control ###

Clone the repository
	
	git clone https://github.com/rozboris/Sublime-Tweet.git "Sublime Tweet"

to your Sublime Text 2 Packages directory:

	Windows: %USERPROFILE%\AppData\Roaming\Sublime Text 2\Packages\

	Mac: ~/Library/Application Support/Sublime Text 2/Packages/	

## How to tweet ##

### Via Sublime Text 2 menu ###

Just select `Tools → Tweet`

### Via Command Palette ###

Just type Tweet

### Via keyboard shortcut ###

* Open Sublime keyboard config (`Preferences → Key Bindings — User`) and add your preferred shortcut like this

	{ "keys": ["ctrl+shift+t"], "command": "tweet" }

* Save the config.
* Hit your selected shortcut.
* ...
* PROFIT!

##First run##

Run Sublime Tweet as explained above and you will be prompted to authorize Sublime Tweet.

After the authorization you can run Tweet command again and start tweeting.

---------

It's an early beta now, please submit all bugs found.
Now you only can only send tweets, but not read them, sorry. 

[sublime]: http://www.sublimetext.com/2
[package_control]: http://wbond.net/sublime_packages/package_control