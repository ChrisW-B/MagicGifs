#Twitter Magic Gifs Bot

Just a simple Tweepy based bot that replies to people it follows with relevant gifs from Giphy

"Inspired" by boredom and the old @MagicPixx bot

Make sure to install Tweepy, TextBlob and my updated version of Giphypop before running!

```sh
pip install tweepy textblob requests git+git://github.com/ChrisW-B/giphypop 
python -m textblob.download_corpora
```

After that, its as simple as setting up a config.py file like so
```python
consumer_key = "XXXXXXXX"
consumer_secret = "XXXXXXXX"
access_token = "XXXXXXXX-XXXXXXXX"
access_token_secret = "XXXXXXXX"
```

and then running `python magicgif.py`


Things I might try to add
- Improving NLP to search for key phrases instead of just nouns/verbs
