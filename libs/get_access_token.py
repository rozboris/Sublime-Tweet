#!/usr/bin/python2.4
#
# Copyright 2007 The Python-Twitter Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
try:
  from urlparse import parse_qsl
except:
  from cgi import parse_qsl

import oauth2 as oauth
import httplib2
import socks

class TwitterAccessTokenRequester:
  def __init__(self, consumer_key, consumer_secret, proxy_host=None, proxy_port=None):
    (self.consumer_key, self.consumer_secret) = (consumer_key, consumer_secret)
    if proxy_host and proxy_port:
      self.proxy = httplib2.ProxyInfo(proxy_type=socks.PROXY_TYPE_HTTP, proxy_host=proxy_host, proxy_port=proxy_port) 
    else:
      self.proxy = None

  def getTokenFirstStep(self):
    self.REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
    self.ACCESS_TOKEN_URL  = 'https://api.twitter.com/oauth/access_token'
    self.AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
    self.SIGNIN_URL        = 'https://api.twitter.com/oauth/authenticate'

    self.oauth_consumer = oauth.Consumer(key=self.consumer_key, secret=self.consumer_secret)
    self.oauth_client = oauth.Client(consumer=self.oauth_consumer, proxy_info=self.proxy)

    print 'Requesting temp token from Twitter'

    self.resp, self.content = self.oauth_client.request(self.REQUEST_TOKEN_URL, 'GET')

    if self.resp['status'] != '200':
      print 'Invalid response from Twitter requesting temp token: %s' % self.resp['status']
      raise
    else:
      self.request_token = dict(parse_qsl(self.content))
      print 'Opening page %s?oauth_token=%s' % (self.AUTHORIZATION_URL, self.request_token['oauth_token'])
      return '%s?oauth_token=%s' % (self.AUTHORIZATION_URL, self.request_token['oauth_token'])
      
  def getTokenSecondStep(self, pin):
    token = oauth.Token(self.request_token['oauth_token'], self.request_token['oauth_token_secret'])
    token.set_verifier(pin)

    print 'Generating and signing request for an access token and pin=%s' % pin
    self.oauth_client  = oauth.Client(self.oauth_consumer, token=token, proxy_info=self.proxy)
    resp, content = self.oauth_client.request(self.ACCESS_TOKEN_URL, method='POST', body='oauth_verifier=%s' % pin)
    access_token  = dict(parse_qsl(content))

    print self.request_token['oauth_token']
    if resp['status'] != '200':
      print 'The request for a Token did not succeed: %s' % resp['status']
      raise
    else:
      print 'Your Twitter Access Token key: %s' % access_token['oauth_token']
      return (access_token['oauth_token'], access_token['oauth_token_secret'])