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
url_that_always_online = 'http://twitter.com'
timeout = 5
tweetsCount = 50
tweet_actions = [['Favorite', ''], ['Retweet', ''], ['Reply', '']]

class ReadTweetsCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.internetStatus = None
        sublime.status_message('Checking your internet connection...')
        thread.start_new_thread(checkInternetConnection, (self.setInternetStatus, timeout))

    def setInternetStatus(self, status):
        self.internetStatus = status
        sublime.set_timeout(self.loadTweetsFromTimeline, 0)

    def loadTweetsFromTimeline(self):
        if (self.internetStatus == False):
            print 'No internet connection, sorry!'
            sublime.status_message('Please check your internet connection!')
            return
                
        sublime.status_message('')      
        self.settingsController = SublimeTweetSettingsController()
        if (not self.settingsController.s['twitter_have_token']):
            TwitterUserRegistration(self.window).register()
            return
 
        self.tweet_texts = []
        api = libs.twitter.Api(consumer_key=consumer_key, 
                consumer_secret=consumer_secret, 
                access_token_key=self.settingsController.s['twitter_access_token_key'], 
                access_token_secret=self.settingsController.s['twitter_access_token_secret'], 
                input_encoding='utf8')
        try:
            self.tweets = api.GetFriendsTimeline(count=tweetsCount, retweets=True, include_entities=True)
        except libs.twitter.TwitterError as error:
            if ('authenticate' in error.message):
                self.settingsController.s['twitter_have_token'] = False
                self.settingsController.saveSettings()
            sublime.status_message('Sorry, we have some problems. Please, try again.')
            print 'Problems with tweeting:%s' % error.message
            return
        for s in self.tweets:
            firstLine  = s.text
            secondLine = '@%s (%s)' % (s.user.screen_name, s.relative_created_at)
            #if (s.retweet_count > 0): secondLine = secondLine + ' - %s times retweeted' % (s.retweet_count)
            self.tweet_texts.append([firstLine, secondLine])
        sublime.set_timeout(self.showTweetsOnPanel, 0)
    
    def showTweetsOnPanel(self):
        if self.tweet_texts and len(self.tweet_texts) > 0:
            self.window.show_quick_panel(self.tweet_texts, self.onTweetSelected)
        
    def onTweetSelected(self, number):
        if number != -1:
            self.selectedTweet = self.tweets.pop(number)
            self.currentTweetActions = []
            self.currentTweetActions = tweet_actions
            for url in self.selectedTweet.urls: 
                self.currentTweetActions.append([url.expanded_url, 'Open URL in external browser'])
            self.window.show_quick_panel(self.currentTweetActions, self.onTweetActionSelected)
    
    def onTweetActionSelected(self, number):
        if number == -1:
            return
        elif number == 0:
            self.doFavorite(self.selectedTweet)
        elif number == 1:
            self.doRetweet(self.selectedTweet)
        elif number == 2:
            self.window.run_command('tweet', {'replyToName':self.selectedTweet.user.screen_name, 'replyToId':self.selectedTweet.id})
            return
        else:
            url = self.currentTweetActions.pop(number).pop(0)
            import webbrowser
            webbrowser.open(url)
    
    def doRetweet(self, tweet):
        api = libs.twitter.Api(consumer_key=consumer_key, 
            consumer_secret=consumer_secret, 
            access_token_key=self.settingsController.s['twitter_access_token_key'], 
            access_token_secret=self.settingsController.s['twitter_access_token_secret'], 
            input_encoding='utf8')
        try:
            api.RetweetPost(id=tweet.id)
        except libs.twitter.TwitterError as error:
            if ('authenticate' in error.message):
                self.settingsController.s['twitter_have_token'] = False
                self.settingsController.saveSettings()
            sublime.status_message('Sorry, we have some problems. Please, try again.')
            print 'Problems with tweeting:%s' % error.message
            return
        sublime.status_message('Tweet was retweeted')

    def doFavorite(self, tweet):
        api = libs.twitter.Api(consumer_key=consumer_key, 
            consumer_secret=consumer_secret, 
            access_token_key=self.settingsController.s['twitter_access_token_key'], 
            access_token_secret=self.settingsController.s['twitter_access_token_secret'], 
            input_encoding='utf8')
        try:
            api.CreateFavorite(status=tweet)
        except libs.twitter.TwitterError as error:
            if ('authenticate' in error.message):
                self.settingsController.s['twitter_have_token'] = False
                self.settingsController.saveSettings()
            sublime.status_message('Sorry, we have some problems. Please, try again.')
            print 'Problems with tweeting:%s' % error.message
            return
        sublime.status_message('Tweet was favorited')        

class TweetCommand(sublime_plugin.WindowCommand):
    def run(self, replyToName=None, replyToId=None):
        self.replyToName = replyToName
        self.replyToId = replyToId
        if (replyToId):
            self.maxlength = 140 - len(replyToName) - 2
        else:
            self.maxlength = 140
        self.internetStatus = None
        sublime.status_message('Checking your internet connection...')
        thread.start_new_thread(checkInternetConnection, (self.setInternetStatus, timeout))

    def setInternetStatus(self, status):
        self.internetStatus = status
        sublime.set_timeout(self.runIfInternetIsUp, 0)

    def runIfInternetIsUp(self):
        assert(self.internetStatus != None)
        if (self.internetStatus == False):
            print 'No internet connection, sorry!'
            sublime.status_message('Please check your internet connection!')
            return
                
        sublime.status_message('')
     
        self.settingsController = SublimeTweetSettingsController()
        if (not self.settingsController.s['twitter_have_token']):
            TwitterUserRegistration(self.window).register()
            return
        
        if(self.replyToId):
            message = 'Reply to @%s:' % self.replyToName
        else:
            message = 'Tweet:'
        self.window.show_input_panel(message, '', self.on_entered_tweet, self.update_character_counter_on_entering_tweet, None)
    
    def update_character_counter_on_entering_tweet(self, text):
        m = 'Charaters remain: %s' % (self.maxlength - len(text))
        sublime.status_message(m) 

    def on_entered_tweet(self, text):
        if (text != ''):
            if (self.replyToId):
                text = '@%s %s' % (self.replyToName, text)
            api = libs.twitter.Api(consumer_key=consumer_key, 
                consumer_secret=consumer_secret, 
                access_token_key=self.settingsController.s['twitter_access_token_key'], 
                access_token_secret=self.settingsController.s['twitter_access_token_secret'], 
                input_encoding='utf8'
                )
            if (len(text) > 140):
                text = text[:131] + '... cont.'
                sublime.status_message('Your tweet is longer than 140 symbols, so it was truncated to 140 and posted anyway.')    
            text = text.encode('utf8')
            try:
                status = api.PostUpdate(text, in_reply_to_status_id=self.replyToId)
            except libs.twitter.TwitterError as error:
                if ('authenticate' in error.message):
                    self.settingsController.s['twitter_have_token'] = False
                    self.settingsController.saveSettings()
                sublime.status_message('Sorry, we have some problems. Please, try again.')
                print 'Problems with tweeting:%s' % error.message
                return
            sublime.status_message('Your tweet was posted!')
            print 'Tweet was posted!'


class SublimeTweetSettingsController:
    def __init__(self, filename = 'SublimeTweet.settings'):
        self.defaultSettings = {'twitter_have_token': False, 'twitter_access_token_key': None, 'twitter_access_token_secret': None}
        self.filename = sublime.packages_path() + '\\User\\' + filename
        print self.filename
        self.s = self.loadSettings()

    def loadSettings(self, forceRewriteFile = False):
        import os.path
        if(not forceRewriteFile and os.path.exists(self.filename)):
            #Reading settings from existing file
            with open(self.filename) as f:
                return json.load(f)
        else:
            #Creating new settings file
            with open(self.filename, 'w') as f:
               f.write(json.dumps(self.defaultSettings, sort_keys=True, indent=4))
            return self.defaultSettings
    
    def saveSettings(self):
        with open(self.filename, 'w') as f:
           f.write(json.dumps(self.s, sort_keys=True, indent=4))

def checkInternetConnection(func, timeout):
    try:
        response=urllib2.urlopen(url_that_always_online,timeout=timeout)
        func(True)
        return
    except urllib2.URLError as err: pass
    func(False)

class TwitterUserRegistration(sublime_plugin.WindowCommand):
    def __init__(self, window):
        self.window = window

    def register(self):
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
