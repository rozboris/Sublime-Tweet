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
from .libs.twitter import *
from .libs.reltime import *
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
    if not self.internetStatus:
      print('No internet connection, sorry!')
      sublime.error_message('Sublime Tweet: Please check your internet connection! It looks like it is down (or just twitter.com is down).')
      return
    else:
      sublime.set_timeout(self.prepareTweetsFromTimeline, 0)

  def prepareTweetsFromTimeline(self):
    sublime.status_message('')
    if not self.settingsController.checkIfEverythingIsReady():
      TwitterUserRegistration(self.window).register(self.run)
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
    except TwitterError as e:
      sublime.status_message('We encountered an error: ' + str(e))
      self.settingsController.s['twitter_has_token'] = False
      self.settingsController.saveSettings()
      TwitterUserRegistration(self.window).register(self.run)
      return
    except Exception as e:
      print('We have some connection issues', e)
      self.tweets = None

  def onTweetsFromTimelineLoaded(self):
    if self.tweets:
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
    except TwitterError as e:
      sublime.status_message('We encountered an error: ' + str(e))
      self.settingsController.s['twitter_has_token'] = False
      self.settingsController.saveSettings()
      TwitterUserRegistration(self.window).register(self.run)
      return
    except Exception as error:
      self.handleError(error)

  def doFavorite(self, tweet):
    try:
      self.api.favorites.create(_id = tweet['id'])
      sublime.status_message('Tweet was favorited')
      tweet['favorited'] = True
      self.showTweetsOnPanel()
    except TwitterError as e:
      sublime.status_message('We encountered an error: ' + str(e))
      self.settingsController.s['twitter_has_token'] = False
      self.settingsController.saveSettings()
      TwitterUserRegistration(self.window).register(self.run)
      return
    except Exception as error:
      self.handleError(error)

  def doUnFavorite(self, tweet):
    try:
      self.api.favorites.destroy(_id = tweet['id'])
      sublime.status_message('Tweet was UNFavorited')
      tweet['favorited'] = False
      self.showTweetsOnPanel()
    except TwitterError as e:
      sublime.status_message('We encountered an error: ' + str(e))
      self.settingsController.s['twitter_has_token'] = False
      self.settingsController.saveSettings()
      TwitterUserRegistration(self.window).register(self.run)
      return
    except Exception as error:
      self.handleError(error)

  def handleError(self, error):
    print('handleError: ', error)
    sublime.status_message('Sorry, we have some problems. Please, try again.')
    self.settingsController.s['twitter_has_token'] = False
    self.settingsController.saveSettings()
    TwitterUserRegistration(self.window).register(self.run)
    return


class TweetCommand(sublime_plugin.WindowCommand):
  def run(self, replyToName=None, replyToId=None):
    self.maxlength = 140
    self.replyToId = replyToId
    if replyToId:
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
    if not self.internetStatus:
      print('No internet connection, sorry!')
      sublime.status_message('Please check your internet connection!')
      return

    sublime.status_message('')

    if not self.settingsController.checkIfEverythingIsReady():
      TwitterUserRegistration(self.window).register(self.run)
      return

    if self.replyToId:
      message = 'Reply to %s:' % self.prefix.strip()
    else:
      message = 'Tweet:'
    self.window.show_input_panel(message, '', self.on_entered_tweet, self.update_character_counter_on_entering_tweet, None)

  def update_character_counter_on_entering_tweet(self, text):
    remaining = self.maxlength - len(self.prefix + text)
    if remaining >= 0:
      m = 'Charaters remain: %d' % remaining
    else:
      m = '★ ★ ★ YOUR MESSAGE IS %d CHARACTERS LONG! ★ ★ ★ ' % (-remaining, )
    sublime.status_message(m)

  def on_entered_tweet(self, text):
    if not len(text):
      return
    sublime.status_message('Sending tweet...')
    text = self.prefix + text
    api = Twitter(auth=OAuth(
      self.settingsController.s['twitter_access_token_key'], 
      self.settingsController.s['twitter_access_token_secret'], 
      consumer_key, 
      consumer_secret))
    if len(text) > self.maxlength:
      after = '... cont.'
      text = text[:self.maxlength - len(after)] + after
      sublime.message_dialog('Your tweet is longer than %d symbols, so it was truncated to %d and posted anyway.' % (self.maxlength, ))
    text = text.encode('utf8')
    try:
      if self.replyToId:
        api.statuses.update(status = text, in_reply_to_status_id = self.replyToId)
      else:
        api.statuses.update(status = text)
    except TwitterError as e:
      sublime.status_message('We encountered an error: ' + str(e))
      self.settingsController.s['twitter_has_token'] = False
      self.settingsController.saveSettings()
      TwitterUserRegistration(self.window).register(self.run)
      return
    except Exception as e:
      sublime.status_message('Sorry, we have some problems. Please, try again.')
      self.settingsController.s['twitter_has_token'] = False
      self.settingsController.saveSettings()
      TwitterUserRegistration(self.window).register(self.run)
      return
    sublime.status_message('Your tweet was posted!')
    print('Tweet was posted!')


class SublimeTweetSettingsController:
  def __init__(self, filename='SublimeTweet.settings'):
    self.settingsThatShouldBeTrue = ['twitter_has_token', 'twitter_access_token_key', 'twitter_access_token_secret']
    self.defaultSettings = {
      'previously_shown_tweets': []
    }
    for setting in self.settingsThatShouldBeTrue:
      self.defaultSettings[setting] = False

    self.filename = os.path.join(sublime.packages_path(), 'User', filename)
    self.s = self.loadSettings()

  def loadSettings(self):
    try:
      contents = open(self.filename).read()
      decoded = json.loads(contents)
      if 'twitter_have_token' in decoded:
        decoded['twitter_has_token'] = decoded['twitter_have_token']
        del decoded['twitter_have_token']
      return decoded
    except:
      self.s = self.defaultSettings
      self.saveSettings()
      return self.s

  def saveSettings(self):
    try:
      with open(self.filename, 'w') as f:
        f.write(json.dumps(self.s, sort_keys=True, indent=2))
    except Exception as e:
      print(e.message)
      sublime.error_message('Sublime Tweet: Can\'t save settings and can\'t fix it either, sorry :(')
      pass  # TODO

  def checkIfEverythingIsReady(self):
    everythingsgood = True
    for setting in self.settingsThatShouldBeTrue:
      if setting not in self.s or not self.s[setting]:
        everythingsgood = False
    return everythingsgood


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
    self.action_when_done = None

  def register(self, action_when_done = None):
    self.settingsController = SublimeTweetSettingsController()
    self.oauth_token = ''
    self.oauth_token_secret = ''
    self.action_when_done = action_when_done

    if not self.settingsController.checkIfEverythingIsReady():
      try:
        ready = sublime.ok_cancel_dialog(
'You are starting Sublime Tweet for the first time, \
please authorize it to use your account. Now I will open your default browser. \n\n\
Please log in, click "Authorize" and then copy a PIN code. Then go back to Sublime Text and enter PIN at the bottom of your screen.\n\
You should only do it once.\n\nAre you ready?', 'I am ready!'
        )
        if not ready:
          return

        (url, self.oauth_token, self.oauth_token_secret) = oauth_dance("Sublime Tweet", consumer_key, consumer_secret)
      except e:
        sublime.error_message('Problems with the first step. Try again.\n')
        print('Exception: ', e)
        sublime.status_message('Please, try calling me again. We have some problems with auth')
        return

      if url:
        message = 'I\'ve opened a browser for you. Please authorize me and enter the pin:'
        self.window.show_input_panel(message, '', self.on_entered_pin, None, None)
        webbrowser.open(url)
      else:
        print('Please try again later')

  def on_entered_pin(self, text):
    try:
      pin = str(text)
      keys = oauth_dance_verify(consumer_key, consumer_secret, self.oauth_token, self.oauth_token_secret, pin)
    except ValueError:
      sublime.error_message('We have some problems with pin. Please, try again.')
      self.register()
      return
    except e:
      sublime.error_message('We have some problems with the second auth step. Please, try again. ', e)
      self.register()
      sublime.status_message('We have some problems with the second auth step. Please, try again.')
      return

    self.access_token_key, self.access_token_secret = keys
    sublime.status_message('You are authorized me, thanks! Now you can tweet from Sublime Text 2.')
    self.settingsController.s['twitter_has_token'] = True
    self.settingsController.s['twitter_access_token_key'] = self.access_token_key
    self.settingsController.s['twitter_access_token_secret'] = self.access_token_secret
    self.settingsController.saveSettings()
    if self.action_when_done:
      self.action_when_done()