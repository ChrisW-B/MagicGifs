#!/usr/bin/env python

import urllib
import re
import sys
import time
import threading
import random
import os
import logging
import config
import tweepy
from textblob import TextBlob
from wordfilter import Wordfilter
from giphypop import translate


class MagicGif(object):

    def __init__(self):
        super(MagicGif, self).__init__()
        #authorize tweepy
        self.auth = tweepy.OAuthHandler(
            config.consumer_key,
            config.consumer_secret)
        self.auth.set_access_token(
            config.access_token,
            config.access_token_secret)
        self.api = tweepy.API(self.auth)

    def limit_handled(self, cursor):
        """
        handles twitter limiting and tries to find people who follow
        """
        while True:
            try:
                yield cursor.next()
            except tweepy.RateLimitError:
                time.sleep(15*60)

    def already_following(self, user):
        friendship = self.api.show_friendship(target_id=user.id)
        return friendship[0].following

    def follow_back(self):
        #teamfollowback!
        while True:
            for follower in self.limit_handled(
                    tweepy.Cursor(self.api.followers).items()):
                # don't repeatedly follow, and maybe keep out the spammers
                if (not self.already_following(follower)
                    and (
                        follower.friends_count/follower.followers_count < 3 or
                        follower.friends_count < 200
                        )):
                    try:
                        follower.follow()
                        logging.info("following " + follower.screen_name)
                    except Exception as e:
                        logging.warning("Couldn't follow " + follower.screen_name+ " continuing")
                        pass      
            time.sleep(15*60)

    def user_listener(self):
        """
        Listens for userstream events
        """
        while True:
            try:
                # For accounts bot is following
                logging.info("starting user")
                magicGifsListener = MagicGifsListener(self.api)
                magicGifsStream = tweepy.Stream(
                    auth=self.api.auth,
                    listener=magicGifsListener)
                magicGifsStream.userstream(async=False)
            except Exception as e:
                logging.error(e)
                continue

    def setup_threads(self):
        """ 
        set up streams
        """
        logging.info("starting threads")
        posted = False
        while not posted:
            try:
                self.api.update_status("@ChrisW_B I'm ready!")
                posted = True
            except:
                logging.warning("Looks like its a duplicate update")
                time.sleep(30)
                continue
        stream = threading.Thread(target=self.user_listener)
        follow = threading.Thread(target=self.follow_back)
        stream.start()
        follow.start()


class MagicGifsListener(tweepy.StreamListener):

    def __init__(self, api):
        self.api = api
        self.botHandle = "@magicgifsbot"

    def on_status(self, tweet):
        logging.info("Got tweet: {}".format(tweet.text))
        if self.ok_to_tweet(tweet):
            logging.info("Replying")
            pic_loc = self.get_image(tweet.text)
            if pic_loc is None:
                if self.botHandle in tweet.text.lower():
                    other_handles = self.extract_handles(tweet.text)
                    self.api.update_status(
                        "@{} {}Sorry, I couldn't find anything for that"
                        .format(tweet.author.screen_name, other_handles),
                        in_reply_to_status_id=tweet.id)
                return
            media_id = self.get_media_id(pic_loc)
            self.delete_file(pic_loc)
            other_handles = self.extract_handles(tweet.text)
            self.api.update_status(
                "@{} {}".format(tweet.author.screen_name, other_handles),
                in_reply_to_status_id=tweet.id,
                media_ids=[media_id])

    def on_error(self, status_code):
        logging.error(status_code)

    def get_image(self, tweet):
        """
        selects an image to reply with
        """
        tweet = self.clean_tweet(tweet)
        filename = self.get_giphy(tweet)
        if filename is None:
            logging.warning("Nothing from the full tweet, picking a word")
            word = self.select_word(tweet)
            if word is None:
                return None
            filename = self.get_giphy(word)
        return filename

    def select_word(self, cleanTweet):
        """
        select a single word to search
        """
        if len(cleanTweet) == 0:
            return None
        blob = TextBlob(cleanTweet)
        posTags = blob.tags
        is_vb = lambda pos: pos[:2] == 'VB'
        is_noun = lambda pos: pos[:2] == 'NN'
        posWords = [word for (word, pos) in posTags
                    if (is_vb(pos) or is_noun(pos)) and len(word) > 3]
        if len(posWords) > 0:
            word = posWords[int(self.rand_num(0, len(posWords)))]
            while(wordfilter.blacklisted(word)):
                posWords.remove(word)
                word = posWords[int(self.rand_num(0, len(posWords)))]
            return word
        return None

    def clean_tweet(self, tweet):
        """
        strip out non keywords from tweet
        """
        stripUrl = re.sub(r"http\S+", "", tweet)
        stripMentions = re.sub(r"@\S+", "", stripUrl)
        stripTags = re.sub(r"#\S+", "", stripMentions)
        stripNums = re.sub(r'\w*\d\w*', '', stripTags).strip()
        stripAbbrev = re.sub(r"(([A-Z])\.)", '', stripNums)
        stripRTs = stripAbbrev.replace("RT", "")
        return stripRTs

    def rand_num(self, min=0.0, max=100.0):
        """
        generate a random number between 0 and 100
        """
        random.seed()
        return random.uniform(min, max)

    def extract_handles(self, tweet):
        handleArray = re.findall(r"@\S+", tweet)
        handleString = ""
        for handle in handleArray:
            if self.botHandle in handle.lower():
                continue
            else:
                handleString += handle + " "
        return handleString

    def ok_to_tweet(self, tweet):
        """
        Generate Random Number and determine if we should tweet
        """
        if str(tweet.author.screen_name).lower() in self.botHandle:
            logging.warning("Bot tweet!")
            return False
        num = self.rand_num()
        if num > 98 or self.botHandle in tweet.text.lower():
            return True
        logging.warning("Not high enough")
        return False

    def get_media_id(self, picLoc):
        """
        upload photo to twitter and return media id for attachment
        """
        logging.info("uploading")
        uploadData = self.api.media_upload(picLoc)
        return uploadData.media_id_string

    def get_giphy(self, text):
        """
        gets a gif from giphy
        """
        giphyLoc = translate(phrase=text, rating='pg-13')
        if giphyLoc is not None:
            logging.info("Search for " + text + " returned " + giphyLoc.url)
            return self.download_file(giphyLoc.downsized.url)
        return None

    def download_file(self, url):
        filename = "giphy.gif"
        urllib.urlretrieve(
            url, filename)
        return filename

    def delete_file(self, loc):
        os.remove(loc)

reload(sys)
#twitter doesn't get along with ascii
sys.setdefaultencoding('utf8')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, filename="log.txt", filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)
magicgif = MagicGif()
wordfilter = Wordfilter()
wordfilter.add_words(config.badwords)
magicgif.setup_threads()

while True:
    #Keep the main thread alive so threads stay up
    time.sleep(1)
