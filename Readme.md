#Twitter Magic Gifs Bot

Just a simple Tweepy based bot that replies to people it follows with relevant gifs from Giphy

"Inspired" by boredom and the old @MagicPixx bot

Make sure to install Tweepy and my updated version of Giphypop before running!

```sh
pip install tweepy requests git+git://github.com/ChrisW-B/giphypop 
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
- NLP for more exact terms: search giphy for increasingly shorter phrases
