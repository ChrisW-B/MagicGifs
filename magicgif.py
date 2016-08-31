#!/usr/bin/env python

from imp import reload
from giphypop import translate
import urllib
import tweepy
import config
import re
import sys
import time
import threading
import random
import os
import logging

reload(sys)
#twitter doesn't get along with ascii
sys.setdefaultencoding('utf8')


class MagicGif(object):
    """docstring for MagicGif"""

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
        self.wordlist = "wordlist.txt"

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
        """
        teamfollowback!
        """
        while True:
            logging.info("starting follow")
            for follower in self.limit_handled(
                    tweepy.Cursor(self.api.followers).items()):
                # don't repeatedly follow, and maybe keep out the spammers
                if (not self.already_following(follower)
                    and (
                        follower.friends_count/follower.followers_count < 3 or
                        follower.friends_count < 200
                        )):
                    follower.follow()
                    logging.info("following " + follower.screen_name)
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
        # set up streams
        logging.info("starting threads")
        self.api.update_status("@ChrisW_B I'm ready!")
        stream = threading.Thread(target=self.user_listener)
        follow = threading.Thread(target=self.follow_back)
        stream.start()
        follow.start()


class MagicGifsListener(tweepy.StreamListener):

    def __init__(self, api):
        self.api = api
        self.botHandle = "@magicgifsbot"

    def on_status(self, tweet):
        logging.info("Got tweet: \n{}".format(tweet.text))
        if(self.ok_to_tweet(tweet.text)):
            logging.info("Replying")
            picLoc = self.get_image(tweet.text)
            if picLoc is None:
                return
            mediaId = self.get_media_id(picLoc)
            self.delete_file(picLoc)
            otherHandles = self.extract_handles(tweet.text)
            self.api.update_status(
                "@{} {}".format(tweet.author.screen_name, otherHandles),
                in_reply_to_status_id=tweet.id,
                media_ids=[mediaId])

    def on_error(self, status_code):
        logging.error(status_code)

    def get_image(self, tweet):
        """
        selects an image to reply with
        """
        word = self.select_word(tweet)
        if word is None:
            return None
        filename = self.get_giphy(word)
        return filename

    def select_word(self, tweet):
        """
        select a single word to search
        """
        tweetArray = self.clean_tweet(tweet)
        optionsArray = []
        for word in tweetArray:
            if len(word) > 3:
                optionsArray.append([word, self.rand_num()])
        if len(optionsArray) == 0:
            return None
        wordLoc = 0
        maxVal = optionsArray[0][1]
        for i in range(1, len(optionsArray)):
            if optionsArray[i][1] > maxVal:
                wordLoc = i
        return optionsArray[wordLoc][0]

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
        return re.findall(r"[\w']+", stripRTs)

    def rand_num(self):
        """
        generate a random number between 0 and 100
        """
        random.seed()
        return random.random() * 100.00

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
        num = self.rand_num()
        if ((num > 80) or (self.botHandle in tweet.lower())):
            return True
        logging.info("Not high enough")
        return False

    def get_media_id(self, picLoc):
        """
        upload photo to twitter and return media id for attachment
        """
        logging.info("uploading")
        uploadData = self.api.media_upload(picLoc)
        logging.info("got mediaid")
        return uploadData.media_id_string

    def get_giphy(self, word):
        """
        gets a gif from giphy
        """
        giphyLoc = translate(word)
        if giphyLoc is not None:
            return self.downloadFile(giphyLoc.fixed_height.url)
        return None

    def downloadFile(self, url):
        filename = "giphy.gif"
        urllib.urlretrieve(
            url, filename)
        return filename

    def delete_file(self, loc):
        os.remove(loc)

    def find_word(self, word):
        """
        searches for word in dictionary file
        """
        word = word.lower()
        with open(self.wordlist) as myFile:
            for num, line in enumerate(myFile):
                if word in line:
                    if word == line.lower():
                        return num
        return -1

logging.basicConfig(level=logging.INFO, filename="log.txt", filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")
magicgif = MagicGif()
magicgif.setup_threads()

while True:
    #Keep the main thread alive so threads stay up
    time.sleep(1)