# coding=utf-8
#author: Rozboris (rozboris.com)
#version: 0.9
import sublime
import sublime_plugin
import json
import threading
import os
import urllib.request as req
from datetime import datetime
from Sublime_Tweet.libs.twitter import *
from Sublime_Tweet.libs.reltime import *
import webbrowser

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
    threading.Thread(target=checkInternetConnection, args=(self.setInternetStatus, timeout, self.settingsController)).start()

  def setInternetStatus(self, status):
    self.internetStatus = status
    if (self.internetStatus == False):
      print('No internet connection, sorry!')
      sublime.status_message('Please check your internet connection!')
      return
    else:
      sublime.set_timeout(self.prepareTweetsFromTimeline, 0)

  def prepareTweetsFromTimeline(self):
    sublime.status_message('')
    if (not self.settingsController.s['twitter_have_token']):
      MY_TWITTER_CREDS = ''
      oauth_dance("Sublime Tweet", consumer_key, consumer_secret, MY_TWITTER_CREDS)
      oauth_token, oauth_secret = read_token_file(MY_TWITTER_CREDS)
      print(oauth_token, oauth_secret)
      Sublime_Tweet.libs.twitter.TwitterUserRegistration(self.window).register()
      return

    self.api = Twitter(auth=OAuth(
      self.settingsController.s['twitter_access_token_key'],
      self.settingsController.s['twitter_access_token_secret'],
      consumer_key,
      consumer_secret,
    ))
    sublime.status_message('Loading tweets from timeline...')
    threading.Thread(target=self.loadTweetsFromTimelineInBackground).start()

  def loadTweetsFromTimelineInBackground(self):
    try:
      self.tweets = self.api.statuses.home_timeline(count = tweetsCount, include_entities = True)
      sublime.set_timeout(self.onTweetsFromTimelineLoaded, 0)
    except:
      print('We have some connection issues')
      self.tweets = None

  def onTweetsFromTimelineLoaded(self):
    if(self.tweets):
      previouslyShownTweets = self.settingsController.s.get('previously_shown_tweets', None)
      self.settingsController.s['previously_shown_tweets'] = [s['id'] for s in self.tweets]
      self.settingsController.saveSettings()
      for t in self.tweets:
        t['new'] = False
        if not previouslyShownTweets or not len(previouslyShownTweets) or t['id'] not in previouslyShownTweets:
          t['new'] = True

      sublime.set_timeout(self.showTweetsOnPanel, 0)

  def showTweetsOnPanel(self):
    self.tweet_texts = []
    if self.tweets and len(self.tweets) > 0:
      for s in self.tweets:
        firstLine  = s['text']
        created_at = datetime.strptime(s['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        created_at_relative = reltime(created_at)
        secondLine = '@%s (%s)' % (s['user']['screen_name'], created_at_relative)
        if 'new' in s and s['new']: 
          secondLine = '☀ ' + secondLine
        if 'favorited' in s and s['favorited']:
          secondLine = '★ ' + secondLine
        if 'retweeted' in s and s['retweeted']:
          secondLine = '↺ ' + secondLine

        self.tweet_texts.append([firstLine, secondLine])
    else:
      self.tweet_texts.append(['No tweets to show', 'If you think it\'s an error - please contact an author'])
    self.showTweets()

  def showTweets(self, number = None):
    sublime.set_timeout(lambda: self.window.show_quick_panel(self.tweet_texts, self.onTweetSelected), 10)

  def onTweetSelected(self, number):
    if number > -1 and self.tweets and len(self.tweets) > 0:
      self.selectedTweet = self.tweets[number]
      sublime.status_message(self.selectedTweet['text'])
      self.currentTweetActions = list([
        [['← Back', ''], ReadTweetsCommand.showTweets],
      ])
      if self.selectedTweet['favorited']:
        self.currentTweetActions.append([['★ Remove Favorite', ''], ReadTweetsCommand.doUnFavorite])
      else:
        self.currentTweetActions.append([['★ Favorite', ''], ReadTweetsCommand.doFavorite])

      if not self.selectedTweet['retweeted']:
        self.currentTweetActions.append([['↺ Retweet', ''], ReadTweetsCommand.doRetweet])

      self.currentTweetActions.append([['@ Reply', ''], ReadTweetsCommand.doReply])

      if 'urls' in self.selectedTweet['entities']:
        for url in self.selectedTweet['entities']['urls']:
          self.currentTweetActions.append([[url['expanded_url'], 'Open URL in external browser'], None])
      if 'media' in self.selectedTweet['entities']:
        for m in self.selectedTweet['entities']['media']:
          self.currentTweetActions.append([[m['expanded_url'], 'Open image in external browser'], None])
      actionPresentation = [strings for strings, function in self.currentTweetActions]
      sublime.set_timeout(lambda: self.window.show_quick_panel(actionPresentation, self.onTweetActionSelected), 10)

  def onTweetActionSelected(self, number):
    if number < 0:
      return
    try:
      [presentation, func] = self.currentTweetActions[number]
      if func:
        func(self, self.selectedTweet)
      else:
        url = presentation[0]
        webbrowser.open(url)
    except Exception as error:
      self.handleError(error)

  def doReply(self, tweet):
    self.window.run_command('tweet', {
      'replyToName': tweet['user']['screen_name'],
      'replyToId': tweet['id']
    })

  def doRetweet(self, tweet):
    print(tweet)
    try:
      self.api.statuses.retweet(id = tweet['id'])
      sublime.status_message('Tweet was retweeted')
      tweet['retweeted'] = True
      self.showTweetsOnPanel()
    except TwitterHTTPError as e:
      sublime.status_message('Error occured: ' + e.message)
    except Exception as error:
      self.handleError(error)
    finally:
      self.showTweetsOnPanel()

  def doFavorite(self, tweet):
    try:
      self.api.favorites.create(_id = tweet['id'])
      sublime.status_message('Tweet was favorited')
      tweet['favorited'] = True
    except TwitterHTTPError as e:
      sublime.status_message('Error occured: ' + e.message)
    except Exception as error:
      self.handleError(error)
    finally:
      self.showTweetsOnPanel()

  def doUnFavorite(self, tweet):
    try:
      self.api.favorites.destroy(_id = tweet['id'])
      sublime.status_message('Tweet was UNFavorited')
      tweet['favorited'] = False
    except TwitterHTTPError as e:
      sublime.status_message('Error occured: ' + e.message)
    except Exception as error:
      self.handleError(error)
    finally:
      self.showTweetsOnPanel()

  def handleError(self, error):
    if ('authenticate' in error.message):
      self.settingsController.s['twitter_have_token'] = False
      self.settingsController.saveSettings()
    sublime.status_message('Sorry, we have some problems. Please, try again.')
    print('Problems with tweeting: %s' % error.message)


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
    threading.Thread(target = checkInternetConnection, args = (self.setInternetStatus, timeout, self.settingsController)).start()

  def setInternetStatus(self, status):
    self.internetStatus = status
    sublime.set_timeout(self.runIfInternetIsUp, 0)

  def runIfInternetIsUp(self):
    if (self.internetStatus == False):
      print('No internet connection, sorry!')
      sublime.status_message('Please check your internet connection!')
      return

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
      api = Twitter(auth=OAuth(
        self.settingsController.s['twitter_access_token_key'], 
        self.settingsController.s['twitter_access_token_secret'], 
        consumer_key, 
        consumer_secret))
      if (len(text) > self.maxlength):
        after = '... cont.'
        text = text[:self.maxlength - len(after)] + after
        sublime.status_message('Your tweet is longer than {0} symbols, so it was truncated to {0} and posted anyway.'.format(self.maxlength))
      text = text.encode('utf8')
      try:
        if self.replyToId:
          api.statuses.update(status = text, in_reply_to_status_id = self.replyToId)
        else:
          api.statuses.update(status = text)
      except Exception as error:
        if ('authenticate' in error.message):
          self.settingsController.s['twitter_have_token'] = False
          self.settingsController.saveSettings()
        sublime.status_message('Sorry, we have some problems. Please, try again.')
        print('Problems with tweeting: %s' % error.message)
        return
      sublime.status_message('Your tweet was posted!')
      print('Tweet was posted!')


class SublimeTweetSettingsController:
  def __init__(self, filename='SublimeTweet.settings'):
    self.defaultSettings = {
      'twitter_have_token': False,
      'twitter_access_token_key': None,
      'twitter_access_token_secret': None,
      'previously_shown_tweets': []
    }
    self.filename = os.path.join(sublime.packages_path(), 'User', filename)
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
      print('Can\'t save settings and can\'t fix it, sorry :(')
      pass  # TODO


def checkInternetConnection(callback, timeout, settings):
  try:
    req.urlopen(url_that_always_online, timeout=timeout)
    settings.saveSettings()
    callback(True)
  except:
    callback(False)

class TwitterUserRegistration(sublime_plugin.WindowCommand):
  def __init__(self, window):
    self.window = window

  def register(self):
    self.settingsController = SublimeTweetSettingsController()
    self.oauth_token = ''
    self.oauth_token_secret = ''

    if (not self.settingsController.s['twitter_have_token']):
      try:
        (url, self.oauth_token, self.oauth_token_secret) = oauth_dance("Sublime Tweet", consumer_key, consumer_secret)
      except e:
        print('Problems with the first step. Try again.\n')
        print('Exception: %s' % e.message)
        sublime.status_message('Please, try calling me again. We have some problems with auth')
        return

      if (url):
        message = 'I\'ve opened a browser for you. Please authorize me and enter the pin:'
        self.window.show_input_panel(message, '', self.on_entered_pin, None, None)
        webbrowser.open(url)
      else:
        print('Please try again later')

  def on_entered_pin(self, text):
    try:
      pin = int(text)
      keys = oauth_dance_verify(consumer_key, consumer_secret, self.oauth_token, self.oauth_token_secret, pin)
    except ValueError:
      print('We have some problems with pin. Please, try again.')
      return
    except e:
      print('We have some problems with the second auth step. Please, try again. %s' % e.message)
      sublime.status_message('We have some problems with the second auth step. Please, try again.')
      return

    self.access_token_key, self.access_token_secret = keys
    sublime.status_message('You are authorized me, thanks! Now you can tweet from Sublime Text 2.')
    self.settingsController.s['twitter_have_token'] = True
    self.settingsController.s['twitter_access_token_key'] = self.access_token_key
    self.settingsController.s['twitter_access_token_secret'] = self.access_token_secret
    self.settingsController.saveSettings()