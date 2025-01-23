import os
from dotenv import load_dotenv
from pymongo import MongoClient
import math
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
import time
import aiohttp


from utility import utility_commands
utility = utility_commands.utilityOperations()

load_dotenv()

PATH = os.getenv('path')
WAR_INFO = os.getenv('WAR_INFO')

class DatabaseConnection:
    def __init__(self):
        self.connection_string = os.getenv("Alex_mongoDB_url")
        self.client = MongoClient(self.connection_string)
        self.db = self.client["Galactic-Swamp"]

    def list_databases(self):
        return self.client.list_database_names()

    def get_table(self):
        return self.db.list_collection_names()
    
    def get_colonies(self, id):
        id = int(id)
        collection = self.db['colonies']
        data = collection.find({"id_gl": id})
        return list(collection.find({"id_gl": id}))
    
    def get_rebuild_time_unix(self, id):
        id = int(id)
        collection = self.db['colonies']
        data = collection.find_one({"id_gl": id})
        print(int(data['colo_refresh_time'].timestamp()))
    
    def found_colonies(self, id):
        id = int(id)
        collection = self.db['foundcolonies']
        return list(collection.find({"gl_id": id}))
    
    def get_player(self, id):
        id = int(id)
        collection = self.db['players']
        return collection.find_one({"id_gl": id})

    def get_cooldown(self, alliance):
        alliance = alliance.upper()
        collection = self.db['wars']
        return collection.find_one({"alliance_name": alliance, "status": "InProgress"})
    
    def get_shield(self, alliance_name):
        alliance_name = alliance_name.lower()
        collection = self.db['matchmaking']
        return collection.find_one({"name": alliance_name})
