# coding=utf-8
#author: Rozboris (rozboris.com)
#version: 0.5b
import sublime
import sublime_plugin
import libs.twitter
import json
from libs.get_access_token import TwitterAccessTokenRequester
import thread

consumer_key = '8m6wYJ3w8J7PxaZxTMkzw'
consumer_secret = 'XnbfrGRC0n93b37PaN7tZa53RuNbExeHRV1gToh4'
url_that_always_online = 'http://twitter.com'
timeout = 2
tweetsCount = 40


class ReadTweetsCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.internetStatus = None
        self.settingsController = SublimeTweetSettingsController()
        sublime.status_message('Checking your internet connection...')
        thread.start_new_thread(checkInternetConnection, (self.setInternetStatus, timeout, self.settingsController))

    def setInternetStatus(self, status):
        self.internetStatus = status
        if (self.internetStatus == False):
            print 'No internet connection, sorry!'
            sublime.status_message('Please check your internet connection!')
            return
        else:
            sublime.set_timeout(self.prepareTweetsFromTimeline, 0)

    def prepareTweetsFromTimeline(self):
        if(self.settingsController.s['use_proxy']):
            self.proxy_config = self.settingsController.s['twitter_proxy_config']
        else:
            self.proxy_config = None

        sublime.status_message('')
        if (not self.settingsController.s['twitter_have_token']):
            TwitterUserRegistration(self.window).register()
            return

        self.api = libs.twitter.Api(consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token_key=self.settingsController.s['twitter_access_token_key'],
                access_token_secret=self.settingsController.s['twitter_access_token_secret'],
                input_encoding='utf8',
                proxy=self.proxy_config)
        sublime.status_message('Loading tweets from timeline...')
        thread.start_new_thread(self.loadTweetsFromTimelineInBackground, ())

    def loadTweetsFromTimelineInBackground(self):
        try:
            self.tweets = self.api.GetFriendsTimeline(count=tweetsCount, retweets=True, include_entities=True)
            sublime.set_timeout(self.onTweetsFromTimelineLoaded, 0)
        except libs.twitter.TwitterError as error:
            self.handleError(error)
            self.tweets = None
        except:
            print 'We have some connection issues'
            self.tweets = None

    def onTweetsFromTimelineLoaded(self):
        if(self.tweets):
            previouslyShownTweets = self.settingsController.s.get('previously_shown_tweets', None)
            self.settingsController.s['previously_shown_tweets'] = [s.id for s in self.tweets]
            self.settingsController.saveSettings()
            for t in self.tweets:
                t.new = False
                if not previouslyShownTweets or len(previouslyShownTweets) <= 0 or not (t.id in previouslyShownTweets):
                    t.new = True

            sublime.set_timeout(self.showTweetsOnPanel, 0)

    def showTweetsOnPanel(self):
        self.tweet_texts = []
        if self.tweets and len(self.tweets) > 0:
            for s in self.tweets:
                firstLine  = s.text
                secondLine = '@%s (%s)' % (s.user.screen_name, s.relative_created_at)
                if hasattr(s, 'new') and s.new: 
                    secondLine = '*NEW* ' + secondLine

                self.tweet_texts.append([firstLine, secondLine])
        else:
            self.tweet_texts.append(['No tweets to show', 'If you think it\'s an error - please contact an author'])
        self.showTweets(0)

    def showTweets(self, number):
        self.window.show_quick_panel(self.tweet_texts, self.onTweetSelected)

    def onTweetSelected(self, number):
        if number > -1 and self.tweets and len(self.tweets) > 0:
            self.selectedTweet = self.tweets[number]
            sublime.status_message(self.selectedTweet.text)
            self.currentTweetActions = list(my_tweet_actions)
            if (self.selectedTweet.urls):
                for url in self.selectedTweet.urls:
                    self.currentTweetActions.append([[url.expanded_url, 'Open URL in external browser'], None])
            if (self.selectedTweet.media):
                for m in self.selectedTweet.media:
                        self.currentTweetActions.append([[m.expanded_url, 'Open image in external browser'], None])
            actionPresentation = [strings for strings, function in self.currentTweetActions]

            self.window.show_quick_panel(actionPresentation, self.onTweetActionSelected)

    def onTweetActionSelected(self, number):
        if number < 0:
            return
        try:
            [presentation, function] = self.currentTweetActions[number]
            if function:
                function(self, self.selectedTweet)
            else:
                url = presentation[0]
                import webbrowser
                webbrowser.open(url)
        except:
            print 'Unbelievable!'

    def doReply(self, tweet):
        self.window.run_command('tweet', {
            'replyToName': tweet.user.screen_name,
            'replyToId': tweet.id
        })

    def doRetweet(self, tweet):
        try:
            self.api.RetweetPost(id=int(tweet.id))
            sublime.status_message('Tweet was retweeted')
        except libs.twitter.TwitterError as error:
            self.handleError(error)

    def showRelatedTweets(self, tweet):
        try:
            self.tweets = self.api.GetRelatedTweets(parent_id=int(tweet.id))
            sublime.set_timeout(self.showTweetsOnPanel, 0)
        except libs.twitter.TwitterError as error:
            self.handleError(error)

    def doFavorite(self, tweet):
        try:
            self.api.CreateFavorite(status=tweet)
            sublime.status_message('Tweet was favorited')
        except libs.twitter.TwitterError as error:
            self.handleError(error)

    def handleError(self, error):
        if ('authenticate' in error.message):
            self.settingsController.s['twitter_have_token'] = False
            self.settingsController.saveSettings()
        sublime.status_message('Sorry, we have some problems. Please, try again.')
        print 'Problems with tweeting:%s' % error.message


class TweetCommand(sublime_plugin.WindowCommand):
    def run(self, replyToName=None, replyToId=None):
        self.maxlength = 140
        self.replyToId = replyToId
        if (replyToId):
            self.prefix = '@%s ' % replyToName
        else:
            self.prefix = ''
        self.internetStatus = None
        self.settingsController = SublimeTweetSettingsController()
        sublime.status_message('Checking your internet connection...')
        thread.start_new_thread(checkInternetConnection, (self.setInternetStatus, timeout, self.settingsController))

    def setInternetStatus(self, status):
        self.internetStatus = status
        sublime.set_timeout(self.runIfInternetIsUp, 0)

    def runIfInternetIsUp(self):
        if (self.internetStatus == False):
            print 'No internet connection, sorry!'
            sublime.status_message('Please check your internet connection!')
            return
        if(self.settingsController.s['use_proxy']):
            self.proxy_config = self.settingsController.s['twitter_proxy_config']
        else:
            self.proxy_config = None

        sublime.status_message('')

        self.settingsController = SublimeTweetSettingsController()
        if (not self.settingsController.s['twitter_have_token']):
            TwitterUserRegistration(self.window).register()
            return

        if(self.replyToId):
            message = 'Reply to %s:' % self.prefix.strip()
        else:
            message = 'Tweet:'
        self.window.show_input_panel(message, '', self.on_entered_tweet, self.update_character_counter_on_entering_tweet, None)

    def update_character_counter_on_entering_tweet(self, text):
        m = 'Charaters remain: %d' % (self.maxlength - len(self.prefix + text))
        sublime.status_message(m)

    def on_entered_tweet(self, text):
        if (text != ''):
            sublime.status_message('Sending tweet...')
            text = self.prefix + text
            api = libs.twitter.Api(consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token_key=self.settingsController.s['twitter_access_token_key'],
                access_token_secret=self.settingsController.s['twitter_access_token_secret'],
                input_encoding='utf8',
                proxy=self.proxy_config)
            if (len(text) > self.maxlength):
                after = '... cont.'
                text = text[:self.maxlength - len(after)] + after
                sublime.status_message('Your tweet is longer than {0} symbols, so it was truncated to {0} and posted anyway.'.format(self.maxlength))
            text = text.encode('utf8')
            try:
                if self.replyToId:
                    api.PostUpdate(text, int(self.replyToId))
                else:
                    api.PostUpdate(text)
            except libs.twitter.TwitterError as error:
                if ('authenticate' in error.message):
                    self.settingsController.s['twitter_have_token'] = False
                    self.settingsController.saveSettings()
                sublime.status_message('Sorry, we have some problems. Please, try again.')
                print 'Problems with tweeting: %s' % error.message
                return
            sublime.status_message('Your tweet was posted!')
            print 'Tweet was posted!'


class SublimeTweetSettingsController:
    def __init__(self, filename='SublimeTweet.settings'):
        self.defaultSettings = {'twitter_have_token': False,
                                'twitter_access_token_key': None,
                                'twitter_access_token_secret': None,
                                'previously_shown_tweets': [],
                                'use_proxy': False,
                                'twitter_proxy_config': None}
        self.filename = sublime.packages_path() + '/User/' + filename
        #TODO path.join
        self.s = self.loadSettings()

    def loadSettings(self):
        try:
            contents = open(self.filename).read()
            return json.loads(contents)
        except:
            self.s = self.defaultSettings
            self.saveSettings()
            return self.s

    def saveSettings(self):
        try:
            with open(self.filename, 'w') as f:
                f.write(json.dumps(self.s, sort_keys=True, indent=4))
        except:
            print 'Can\'t save settings and can\'t fix it, sorry :('
            pass  # TODO


def checkInternetConnection(callback, timeout, settings):
    import urllib2
    if (settings.s.get('use_proxy', None) and settings.s.get('twitter_proxy_config', None)):
        proxy = urllib2.ProxyHandler(settings.s['twitter_proxy_config'])
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)
        try:
            urllib2.urlopen(url_that_always_online, timeout=timeout)
            settings.s['use_proxy'] = True
            settings.saveSettings()
            callback(True)
        except:
            opener = urllib2.build_opener()
            urllib2.install_opener(opener)
            try:
                urllib2.urlopen(url_that_always_online, timeout=timeout)
                settings.s['use_proxy'] = False
                settings.saveSettings()
                callback(True)
            except:
                callback(False)
    else:
        try:
            urllib2.urlopen(url_that_always_online, timeout=timeout)
            settings.s['use_proxy'] = False
            settings.saveSettings()
            callback(True)
        except:
            if(settings.s.get('twitter_proxy_config', None)):
                proxy = urllib2.ProxyHandler(settings.s['twitter_proxy_config'])
                opener = urllib2.build_opener(proxy)
                urllib2.install_opener(opener)
                try:
                    urllib2.urlopen(url_that_always_online, timeout=timeout)
                    settings.s['use_proxy'] = True
                    settings.saveSettings()
                    callback(True)
                except:
                    callback(False)
            else:
                callback(False)


class TwitterUserRegistration(sublime_plugin.WindowCommand):
    def __init__(self, window):
        self.window = window

    def register(self):
        self.settingsController = SublimeTweetSettingsController()
        self.proxy_host, self.proxy_port = None, None
        if (self.settingsController.s['use_proxy']):
            (self.proxy_host, self.proxy_port) = self.settingsController.s['twitter_proxy_config']['http'].split(':')
            try:
                self.proxy_host, self.proxy_port = str(self.proxy_host), int(self.proxy_port)
            except:
                print 'Can\'t parse your proxy settings, sorry'
                sublime.status_message('Can\'t parse your proxy settings, sorry')
                return

        if (not self.settingsController.s['twitter_have_token']):
            self.TwitterAccessTokenRequester = TwitterAccessTokenRequester(consumer_key, consumer_secret, self.proxy_host, self.proxy_port)
            try:
                url = self.TwitterAccessTokenRequester.getTokenFirstStep()
            except:
                print 'Problems with the first step. Try again.\n'
                sublime.status_message('Please, try calling me again. We have some problems with auth')
                return

            if (url):
                message = 'I\'ve opened a browser for you. Please authorize me and enter the pin:'
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

my_tweet_actions = [
    [['Back', ''], ReadTweetsCommand.showTweets],
    [['Favorite', ''], ReadTweetsCommand.doFavorite],
    [['Retweet', ''], ReadTweetsCommand.doRetweet],
    [['Reply', ''], ReadTweetsCommand.doReply],
    [['Show related tweets', ''], ReadTweetsCommand.showRelatedTweets]
]
