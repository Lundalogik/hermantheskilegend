#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import redis
import os

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)

#Variables that contains the user credentials to access Twitter API

access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')


#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):

    def on_data(self, data):
        d = json.loads(data)
        print("The twitter gods gave us new data from", d["user"]["screen_name"])
        point = 0
        for potential_point in d["entities"]["hashtags"]:
                p = potential_point["text"].lower()
                if p == "1hp":
                    point = 1
                elif p == "2hp":
                    point = 2
                elif p == "5hp":
                    point = 5
                elif p == "10hp":
                    point = 10
                elif p == "25hp":
                    point = 25
                elif p == "50hp":
                    point = 50
        if point > 0:
            user = d["user"]["screen_name"]
            userdata = {"name": d["user"]["screen_name"],"fullname":d["user"]["name"], "pic": d["user"]["profile_image_url"], "src":"twitter"}
            print("Adding new score by", userdata)
            redis.sadd(user, json.dumps(userdata))
            redis.zincrby("leaderboard", user, point)
        return True

    def on_error(self, status):
        print(status)


if __name__ == '__main__':

    #This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, l)

    #This line filter Twitter Streams to capture data by the keywords: 'python', 'javascript', 'ruby'
    stream.filter(track=['#iifutmaningen'])