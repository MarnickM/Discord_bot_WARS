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


from utility.utility_commands import utilityOperations as utility

load_dotenv()

PATH = os.getenv('path')
WAR_INFO = os.getenv('WAR_INFO')

class DatabaseConnection:
    def __init__(self):
        self.connection_string = os.getenv("mongoDB_url")
        self.client = MongoClient(self.connection_string)
        self.db = self.client['Galaxy_Life']

    def get_database_stats(self):
        alliances_count = self.db['alliances'].count_documents({})
        players_count = self.db['players'].count_documents({})
        
        coordinates_collection = self.db['coordinates']
        coordinates_count = 0
        for doc in coordinates_collection.find({}):
            for field_name, field_value in doc.items():
                if field_name.startswith("C") and isinstance(field_value, list) and len(field_value) > 0:
                    coordinates_count += 1
        stats = {"alliances": alliances_count, "players": players_count, "coordinates": coordinates_count}
        return stats

    def list_databases(self):
        return self.client.list_database_names()

    def list_collections(self):
        return self.db.list_collection_names()

    def find_player(self, name):
        collection = self.db['coordinates']
        # collection = self.db['testing']
        return collection.find_one({"Name": name})

    def update_colony(self, name, colony_num, colony_data):
        # collection = self.db['testing']
        collection = self.db['coordinates']
        update_result = collection.update_one(
            {"Name": name},
            {"$set": {f"{colony_num}": colony_data}}
        )
        return update_result.modified_count

    def add_player(self, player_data):
        collection = self.db['coordinates']
        # collection = self.db['testing']
        return collection.insert_one(player_data)
    
    async def get_players_from_json(self, search_string: str):
        results = []
        count = 0
        war_info = await utility.loadJson(PATH + WAR_INFO)
        for name, details in war_info['members'].items():
            if search_string.lower() in name.lower():
                results.append(name)
                count += 1
                if count >= 25:
                    break
        return results
    
    def get_players(self, search_string: str):
        collection = self.db['players']
        query = {"Name": {"$regex": search_string, "$options": "i"}}
        return [player['Name'] for player in collection.find(query).limit(25)]
    
    def get_alliances(self, search_string: str):
        collection = self.db['alliances']
        query = {"Name": {"$regex": search_string, "$options": "i"}}
        return [alliance['Name'] for alliance in collection.find(query).limit(25)]
    
    def get_all_alliances(self):
        collection = self.db['alliances'].find()
        return collection
    
    def return_collection(self, collection_name):
        return self.db[collection_name]
    
    async def get_score(self, name: str):
        collection = self.db['alliances']
        alliance = collection.find_one({"Name": name})
        if alliance:
            score = alliance.get("pointsGained", 0)  # Adjust "WarPoints" to the actual field name in your database
            return score
        else:
            # await DatabaseConnection.add_alliance(self=DatabaseConnection(), alliance_name=name)
            return 0  # Return a default score if alliance not found or if score field is not present
        
    def get_remaining_time(self, name: str):
        collection = self.db['alliances']
        alliance = collection.find_one({"Name": name})
        return alliance.get("remainingTime", 0)

    def calculate_remaining_time(self, our_score: int, their_score: int, war_start_time: datetime) -> int:
        war_start_timestamp = time.mktime(war_start_time.timetuple())
        if not (our_score == 0 or their_score == 0):
            winner = max(our_score, their_score)
            loser = min(our_score, their_score)
            x = abs(winner / (winner + loser))
        else:
            x = 1

        result = pow(-(19*(x-1)), 2.2)+14
        if result > 72:
            result = 72
        elif result < 15:
            result = 15
        elapsed = time.time() - war_start_timestamp
        remaining = result*3600 - elapsed
        return int(time.time() + remaining)
    
    def get_coordinates(self, name: str):
        collection = self.db['alliances']
        alliance = collection.find_one

    async def add_alliance(self, alliance_name):
      collection = self.db['alliances']
      try:
          alliance_search = alliance_name.replace(" ", "%20")
          async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.galaxylifegame.net/Alliances/get?name={alliance_search}") as response:
                if response.status == 200:
                    alliance_data = await response.json(content_type="text/plain")
        
                    # Calculate the average player level
                    total_levels = sum(member['Level'] for member in alliance_data.get('Members', []))
                    players_count = len(alliance_data.get('Members', []))
                    avg_player_level = total_levels / players_count if players_count > 0 else 0
        
                    # Calculate the average HQ level
                    total_hq_levels = 0
                    for member in alliance_data.get('Members', []):
                        player_name = member['Name']
                        async with aiohttp.ClientSession() as session:
                            player_name = player_name.replace(" ", "%20")
                            async with session.get(f"https://api.galaxylifegame.net/Users/name?name={player_name}") as player_response:
                                 if player_response.status == 200:
                                     player_data = await player_response.json(content_type="text/plain")
                                     if player_data.get('Planets'):
                                         total_hq_levels += player_data['Planets'][0]['HQLevel']
        
                    avg_hq_level = total_hq_levels / players_count if players_count > 0 else 0
        
                    # Prepare the document with fetched data
                    alliance_document = {
                        "Name": alliance_data.get("Name", alliance_name),
                        "avgPlayerLevel": avg_player_level,
                        "warpoints": alliance_data.get("WarPoints", 0),
                        "avgHQLevel": avg_hq_level,
                        "varHQLevel": 0,  # Placeholder, needs specific logic to determine this value
                        "PlayersCount": players_count,
                        "warPointsAvailable": 0,  # Placeholder, needs specific logic to determine this value
                        "InWar": alliance_data.get("InWar", False),
                        "LastUpdate": datetime.now(),
                        "WarsWon": alliance_data.get("WarsWon", 0),
                        "WarsLost": alliance_data.get("WarsLost", 0),
                        "OpponentAllianceId": alliance_data.get("OpponentAllianceId", ""),
                        "pointsGained": 0,
                        "remainingTime":0,
                        "initialWarPoints":alliance_data.get("WarPoints", 0),
                        "warStartTime":datetime.now()
                    }
        
                    # Insert the document into the collection
                    collection.insert_one(alliance_document)
                    print(f"Inserted data for alliance: {alliance_name}")
                else:
                    print(f"Failed to fetch data for alliance: {alliance_name} - Status Code: {response.status}")
      except Exception as e:
          print(f"Error processing alliance: {alliance_name} - Error: {e}")


        # Default player template
    def default_player_template(self, player_name, initial_warpoints):
        data = {
            "Name": player_name,
            "initial_warpoints": initial_warpoints,
            "last_update": datetime.now(),
            "points_gained": 0,
            "total_warpoints": initial_warpoints
        }
        collection = self.db['Alliance_players']
        collection.insert_one(data)
    
    def get_all_members_GE2(self):
        collection = self.db['Alliance_players']
        return collection.find()
    
    def find_player_GE2(self, name):
        collection = self.db['Alliance_players']
        return collection.find_one({"Name": name})
    
    def update_player_GE2(self, player_name: str, player_data: dict):
        collection = self.db["Alliance_players"]
        result = collection.update_one(
            {"Name": player_name},
            {"$set": player_data})

    def remove_player_GE2(self, player_name: str):
        collection = self.db["Alliance_players"]
        collection.delete_one({"Name": player_name})

    async def initiate_enemy_players(self, alliance_name: str):
        collection = self.db['Enemy_players']
        # clear the table
        collection.delete_many({})

        alliance_search = alliance_name.replace(" ", "%20")

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.galaxylifegame.net/Alliances/get?name={alliance_search}") as response:
                    if response.status == 200:
                        player_data = await response.json(content_type="text/plain")
                        members = player_data.get('Members', [])
                        for member in members:
                            time_calc = datetime.now() - timedelta(hours=1)
                            time = time_calc.strftime("%Y-%m-%d %H:%M:%S")
                            data = {
                                "Name": member['Name'], 
                                "initial_warpoints": member["TotalWarPoints"],
                                "total_warpoints": member["TotalWarPoints"],
                                "last_update": time,
                            }
                            collection.insert_one(data)

    def get_enemy_players(self):
        collection = self.db['Enemy_players']
        return collection.find({})
    
    def find_enemy_player(self, name):
        collection = self.db['Enemy_players']
        return collection.find_one({"Name": name})
    
    def update_enemy_player(self, player_name: str, warpoints: int):
        collection = self.db["Enemy_players"]
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        collection.update_one(
            {"Name": player_name},
            {"$set": {"total_warpoints": warpoints, "last_update": time}})
        
    def get_war_start_time(self, alliance_name: str):
        collection = self.db['alliances']
        alliance = collection.find_one({"Name": alliance_name})
        if alliance is not None:
            return alliance.get("warStartTime", 0)
        else:
            return "*not tracked*"
        
        
    def create_afk(self, name: str, warpoints: int):
        collection = self.db['Top_alliances_players']
        now = datetime.now()
        data = {
            "Name": name,
            "warpoints": warpoints,
            "last_update": now
        }
        print('inserted')
        collection.insert_one(data)
        
    def update_afk(self, name: str, warpoints: int):
        collection = self.db['Top_alliances_players']
        now = datetime.now()
        collection.update_one(
            {"Name": name},
            {"$set": {"warpoints": warpoints, "last_update": now}})
        
    def get_afk(self, name: str):
        collection = self.db['Top_alliances_players']
        return collection.find_one({"Name": name})
    
    def find_opponent_GE2(self):
        collection = self.db['alliances']
        return collection.find_one({"Name": "Galactic Empire II"})
    
    def find_alliance(self, alliance_name):
        collection = self.db['alliances']
        return collection.find_one({"Name": alliance_name})

    


