import bottle
from bottle import route, redirect, post, run, request, hook, static_file
import os
from instagram.client import InstagramAPI
import redis
import json


redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)

bottle.debug(True)
app = bottle.app()

api = InstagramAPI(client_id=os.environ.get('INSTA_ID'), client_secret=os.environ.get('INSTA_SECRET'),redirect_uri="http://localhost:5000/oauth_callback")

@route('/')
def send_static():
    return static_file("index.html", root='./')

@route('/<filename:path>')
def send_static(filename):
    return static_file(filename, root='./')

@route('/get_result')
def test():
    top_users = redis.zrevrange("leaderboard", 0, 9, withscores=True)
    a = [
        {
            "user": json.loads(
                redis.smembers(user).pop().decode('utf-8')
            ),
            "score": score
        }
        for user, score in top_users
    ]
    return json.dumps(a)

@post('/kill_all')
def die():
    redis.flushdb()
    return "All is dead!"

@post('/kill/<user>')
def die(user):
    redis.zrem("leaderboard", user)
    return user + " is dead!"

@post('/reset_insta')
def die():
    redis.delete("insta")
    return "Insta is reset!"

@post('/reset_score')
def die():
    redis.delete("leaderboard")
    return "Score is reset!"

@post('/add_point/<user>/<point>')
def die(user, point):
    redis.zincrby("leaderboard", user, int(point))
    return user + " got " + point + " new point"

@post('/add_user/<user>')
def add(user):
    u = {"name": user, "fullname": user, "pic": "/assets/img/user.png",
     "src": "own"}
    redis.sadd(user, json.dumps(u))
    return "added user: " + user

@route('/init_insta')
def home():
    try:
        url = api.get_authorize_url(scope=["public_content"])
        return '<a href="%s">Connect with Instagram</a>' % url
    except Exception as e:
        print(e)

@route('/oauth_callback')
def on_callback():
    code = request.GET.get("code")
    if not code:
        return 'Missing code'
    try:
        access_token, user_info = api.exchange_code_for_access_token(code)
        if not access_token:
            return 'Could not get access token'
        redis.set("insta_access_token", access_token.encode('utf-8'))
    except Exception as e:
        print(e)
    return "YES"

bottle.run(app=app, host="0.0.0.0", port=os.environ.get('PORT', 5000))