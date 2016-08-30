#!/usr/bin/env python

from imp import reload
from giphypop import translate
import tweepy
import config
import re
import sys
import time
import thread
import random
import os
import urllib.request


wordlist = "wordlist.txt"
reload(sys)
#twitter doesn't get along with ascii
sys.setdefaultencoding('utf8')


class MagicPicsListener(tweepy.StreamListener):
    def on_status(self, status):
        if(ok_to_tweet()):
            picLoc = get_image(status.text)
            if picLoc is None:
                return
            mediaId = get_media_id(picLoc)
            delete_file(picLoc)
            api.update_status(
                "@" + status.author.screen_name,
                in_reply_to_status_id=status.id,
                media_ids=[mediaId])

    def on_error(self, status_code):
        print(status_code)


def get_image(tweet):
    """
    selects an image to reply with
    """
    word = select_word(tweet)
    if word is None:
        return None
    filename = get_giphy(word)
    return filename


def select_word(tweet):
    """
    select a single word to search
    """
    tweetArray = clean_tweet(tweet)
    optionsArray = []
    for word in tweetArray:
        if len(word) > 3:
            optionsArray.append([word, rand_num()])
    if len(optionsArray) == 0:
        return None
    wordLoc = 0
    maxVal = optionsArray[0][1]
    for i in range(1, len(optionsArray)):
        if optionsArray[i][1] > maxVal:
            wordLoc = i
    return optionsArray[wordLoc][0]


def clean_tweet(tweet):
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


def rand_num():
    """
    generate a random number between 0 and 100
    """
    random.seed()
    return random.range(0, 100)


def ok_to_tweet():
    """
    Generate Random Number and determine if we should tweet
    """
    if(rand_num() > 80):
        return True
    return False


def get_media_id(picLoc):
    """
    upload photo to twitter and return media id for attachment
    """
    uploadData = api.media_upload(picLoc)
    return uploadData.media_id_string


def get_giphy(word):
    """
    gets a gif from giphy
    """
    giphyLoc = translate(word).fixed_height.url
    return downloadFile(giphyLoc)


def downloadFile(url):
    filename = "giphy.gif"
    urllib.urlretrieve(
        url, filename)
    return filename


def delete_file(loc):
    os.remove(loc)


def find_word(word):
    """
    searches for word in dictionary file
    """
    word = word.lower()
    with open(wordlist) as myFile:
        for num, line in enumerate(myFile):
            if word in line:
                if word == line.lower():
                    return num
    return -1


def limit_handled(cursor):
    """
    handles twitter limiting and tries to find people who follow
    """
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            time.sleep(15*60)


def already_following(user):
    friendship = api.show_friendship(target_id=user.id)
    return friendship[0].following


def follow_back():
    """
    teamfollowback!
    """
    while True:
        print("starting follow")
        for follower in limit_handled(tweepy.Cursor(api.followers).items()):
            # don't repeatedly follow, and maybe keep out the spammers
            if (not already_following(follower)
                and (
                    follower.friends_count/follower.followers_count < 3 or
                    follower.friends_count < 200
                    )):
                follower.follow()
                print("following " + follower.screen_name)
        time.sleep(15*60)


def user_listener():
    """
    Listens for userstream events
    """
    while True:
        try:
            # For accounts bot is following
            print("starting user")
            magicPicsListener = MagicPicsListener()
            magicPicsStream = tweepy.Stream(
                auth=api.auth,
                listener=magicPicsListener)
            magicPicsStream.userstream(async=False)
        except:
            continue


def setup_threads():
    # set up streams
    thread.start_new_thread(user_listener, ())
    # start follow back
    thread.start_new_thread(follow_back, ())

#authorize tweepy
auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
api = tweepy.API(auth)
setup_threads()
api.update_status("@ChrisW_B I'm ready!")

while True:
    #Keep the main thread alive so threads stay up
    time.sleep(1)
