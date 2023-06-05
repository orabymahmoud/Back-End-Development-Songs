from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health")
def health():
    return {"status":"OK"}, 200

@app.route("/count")
def count():
    count = db.songs.count_documents({})

    return {"count": count}, 200

@app.route("/song")
def get_songs():
    songs = db.songs.find({})

    return {"songs": parse_json(songs)}, 200



@app.route("/song/<int:id>")
def get_song(id):
    song = db.songs.find_one({"id":id})

    # check if the song was found
    if song is None:
        # do something with the song
        return {"message": "song with id not found"}, 404 
    else:
       return parse_json(song), 200

@app.route("/song" , methods = ["POST"])
def create_song():
    
    data = request.get_json()

    # check if the song was found
    if db.songs.find_one({"id":data["id"]}) is None:
        result = db.songs.insert_one(data)
        # do something with the song
        return {"inserted id":{"$oid":"{}".format(result.inserted_id)}}, 200 
    else:
       return {"Message":"song with id {} already present".format(data["id"])}, 302 

@app.route("/song/<int:id>" , methods = ["PUT"])
def update_song(id):
    
    data = request.get_json()

    # check if the song was found
    if db.songs.find_one({"id": id}) is not None:
        result = db.songs.update_one({"id":id}, {'$set': data})
        # do something with the song
        if result.matched_count > 0 and result.modified_count > 0 :
            song = db.songs.find_one({"id":id})
            return parse_json(song), 200
        else:
            return {"message":"song found, but nothing updated"}
    else:
       return {"message": "song not found"}, 404 

@app.route("/song/<int:id>" , methods = ["DELETE"])
def delete_song(id):
    
    # check if the song was found
    if db.songs.find_one({"id": id}) is not None:
        result = db.songs.delete_one({"id":id})

        return {"message":"song deleted"} ,200
    else:
       return {"message": "song not found"}, 404 
