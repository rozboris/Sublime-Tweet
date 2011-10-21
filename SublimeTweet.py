# coding=utf-8
#author: Rozboris (rozboris.com)
#version: 0.5b
import sublime, sublime_plugin
import libs.twitter
import json
from libs.get_access_token import TwitterAccessTokenRequester
import urllib2
import threading, thread
import time

consumer_key    = '8m6wYJ3w8J7PxaZxTMkzw'
consumer_secret = 'XnbfrGRC0n93b37PaN7tZa53RuNbExeHRV1gToh4'
timeout = 1
tweetsCount = 50

class ReadTweetsCommand(sublime_plugin.WindowCommand):
    def setInternetStatus(self, status):
        self.internetStatus = status
        sublime.set_timeout(self.loadTweetsFromTimeline, 0)

    def run(self):
        self.settingsController = SublimeTweetSettingsController()
        if (not self.settingsController.s['twitter_have_token']):
            self.window.run_command('tweet')
            self.window.run_command('read_tweets')
            return
        self.internetStatus = None
        sublime.status_message('Checking your internet connection...')
        thread.start_new_thread(checkInternetConnection, (self.setInternetStatus, timeout))

    def loadTweetsFromTimeline(self):
        if (self.internetStatus == False):
            print 'No internet connection, sorry!'
            sublime.status_message('Please check your internet connection!')
            return
                
        sublime.status_message('')       
        self.tweets = []
        api = libs.twitter.Api(consumer_key=consumer_key, 
                consumer_secret=consumer_secret, 
                access_token_key=self.settingsController.s['twitter_access_token_key'], 
                access_token_secret=self.settingsController.s['twitter_access_token_secret'], 
                input_encoding='utf8')
        statuses = api.GetFriendsTimeline(count=tweetsCount, retweets=True)
        for s in statuses:
            #self.tweets.append('%s:\t%s' % (s.user.screen_name, s.text))
            self.tweets.append([s.text, s.user.screen_name])
        sublime.set_timeout(self.showTweetsOnPanel, 0)
    
    def showTweetsOnPanel(self):
        if self.tweets and len(self.tweets) > 0:
            self.window.show_quick_panel(self.tweets, self.onTweetSelected)
        
    def onTweetSelected(self, number):
        #self.currentTweetActions = []
        #self.currentTweetActions.append
        pass

class TweetCommand(sublime_plugin.WindowCommand):
    def setInternetStatus(self, status):
        self.internetStatus = status
        sublime.set_timeout(self.runIfInternetIsUp, 0)
    
    def run(self):
        self.internetStatus = None
        sublime.status_message('Checking your internet connection...')
        thread.start_new_thread(checkInternetConnection, (self.setInternetStatus, timeout))

    def runIfInternetIsUp(self):
        assert(self.internetStatus != None)
        if (self.internetStatus == False):
            print 'No internet connection, sorry!'
            sublime.status_message('Please check your internet connection!')
            return
                
        sublime.status_message('')
        
        self.settingsController = SublimeTweetSettingsController()

        if (not self.settingsController.s['twitter_have_token']):
            print 'Not registered\n'
            self.TwitterAccessTokenRequester = TwitterAccessTokenRequester(consumer_key, consumer_secret)
            try:
                url = self.TwitterAccessTokenRequester.getTokenFirstStep()
            except:
                print 'Problems with the first step. Try again.\n'
                sublime.status_message('Please, try calling me again. We have some problems with auth')
                return

            if (url):
                message = 'I\'ve opened a browser for you. Please authorize me and enter the pin:';
                self.window.show_input_panel(message, '', self.on_entered_pin, None, None)
                import webbrowser
                webbrowser.open(url)
            else:
                print 'Please try again later'
        else:
            print 'Already registered\n'
            message = 'Tweet:'
            self.window.show_input_panel(message, '', self.on_entered_tweet, self.update_character_counter_on_entering_tweet, None)
    
    def on_entered_pin(self, text):
        try:
            pin = int(text)
            keys = self.TwitterAccessTokenRequester.getTokenSecondStep(pin)
        except ValueError:
            print 'We have some problems with pin. Please, try again.'
            return
        except:
            print 'We have some problems with the second auth step. Please, try again.'
            sublime.status_message('We have some problems with the second auth step. Please, try again.')
            return

        self.access_token_key, self.access_token_secret = keys
        sublime.status_message('You are authorized me, thanks! Now you can tweet from Sublime Text 2.')
        self.settingsController.s['twitter_have_token'] = True
        self.settingsController.s['twitter_access_token_key'] = self.access_token_key
        self.settingsController.s['twitter_access_token_secret'] = self.access_token_secret
        self.settingsController.saveSettings()
        #print 'Your Twitter Access Token key: %s secret: %s' % (self.access_token_key, self.access_token_secret)
    
    def update_character_counter_on_entering_tweet(self, text):
        m = 'Charaters remain: %s' % (140 - len(text))
        sublime.status_message(m) 

    def on_entered_tweet(self, text):
        if (text != ''):
            api = libs.twitter.Api(consumer_key=consumer_key, 
                consumer_secret=consumer_secret, 
                access_token_key=self.settingsController.s['twitter_access_token_key'], 
                access_token_secret=self.settingsController.s['twitter_access_token_secret'], 
                input_encoding='utf8'
                )
            try:
                if (len(text) > 140):
                    text = text[:131] + '... cont.'
                    sublime.status_message('Your tweet is longer than 140 symbols, so it was truncated to 140 and posted anyway.')    
                text = text.encode('utf8')
                status = api.PostUpdate(text)
                sublime.status_message('Your tweet was posted!')
                print 'Tweet was posted!'
            except libs.twitter.TwitterError as error:
                #self.settingsController.s['twitter_have_token'] = False
                #self.settingsController.saveSettings()
                sublime.status_message('Sorry, we have some problems. Please, try again.')
                print 'Problems with tweeting:'
                print error.message

class SublimeTweetSettingsController:
    def __init__(self, filename = 'SublimeTweet.settings'):
        self.defaultSettings = {'twitter_have_token': False, 'twitter_access_token_key': None, 'twitter_access_token_secret': None}
        self.filename = sublime.packages_path() + '\\User\\' + filename
        print self.filename
        self.s = self.loadSettings()

    def loadSettings(self, forceRewriteFile = False):
        import os.path
        if(not forceRewriteFile and os.path.exists(self.filename)):
            print 'Reading settings from existing file'
            with open(self.filename) as f:
                return json.load(f)
        else:
            print 'Creating new settings file'
            with open(self.filename, 'w') as f:
               f.write(json.dumps(self.defaultSettings, sort_keys=True, indent=4))
            return self.defaultSettings
    
    def saveSettings(self):
        with open(self.filename, 'w') as f:
           f.write(json.dumps(self.s, sort_keys=True, indent=4))

def checkInternetConnection(func, timeout):
    try:
        response=urllib2.urlopen('http://twitter.com',timeout=timeout)
        func(True)
        return
    except urllib2.URLError as err: pass
    func(False)