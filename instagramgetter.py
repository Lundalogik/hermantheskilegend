from instagram.client import InstagramAPI
import redis
import os
import json
from apscheduler.schedulers.blocking import BlockingScheduler
import requests

print("Started insta getter")
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)

def parse_result(resp):
    for insta in resp['data']:
        if redis.sismember("insta", insta.id):
            print("Mr T says: No new fun for you!")
            break
        else:
            print("We found ourselfs new data from", insta.user.username)
            point = 0
            for potential_point in insta.tags:
                p = potential_point.name.lower()
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
                user = insta.user.username
                userdata = {"name":insta.user.username,"fullname":insta.user.full_name, "pic": insta.user.profile_picture, "src":"insta"}
                print("Adding new score by", userdata)
                redis.sadd(user, json.dumps(userdata))
                redis.zincrby("leaderboard", user, point)
            redis.sadd("insta", insta.id)



sched = BlockingScheduler()

def get_insta_data():
    access_token = redis.get("insta_access_token").decode("utf-8")
    r = requests.get(
        "https://api.instagram.com/v1/tags/lundalogik/media/recent?access_token="+access_token + "&COUNT=5")
    if r.ok:
        parse_result(r.json())

get_insta_data()

@sched.scheduled_job('interval', minutes=2)
def timed_job():
    print("Get new data from da insta")
    access_token = redis.get("insta_access_token")

    api = InstagramAPI(access_token=access_token, client_secret=os.environ.get('INSTA_SECRET'))
    parse_result(api.tag_recent_media(tag_name="fitness"))



#sched.start()