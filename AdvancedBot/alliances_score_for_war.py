import os, json, time, threading
import discord
from discord import channel
from discord import app_commands
from discord.ui import Button
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from itertools import islice
import typing
from discord.ext import tasks
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# class files imports
from database import database
from utility import utility_commands
from dropdown import dropdown
from button import button
from database_Alex import database_Alex

# define class variables
db_operations = database.DatabaseConnection()
utility_operations = utility_commands.utilityOperations()
db_Alex = database_Alex.DatabaseConnection()

# #########################
# ####### VARIABLES #######
# #########################

# global variables
ALLIANCE_NAME = os.getenv('ALLIANCE_NAME')
GUILD_ID = int(os.getenv('GUILD_ID'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
CHANNEL_ID_COORDS = int(os.getenv('CHANNEL_ID_COORDS'))
CHANNEL_ID_WAR_CHAT = int(os.getenv('CHANNEL_ID_WAR_CHAT'))
CHANNEL_ID_ATTACKLOG = int(os.getenv('CHANNEL_ID_ATTACKLOG'))
global regentime
regentime = 3
global points
points = 0
global sum_for_war
sum_for_war = 0
global sum_against_war
sum_against_war = 0
global top_5_least_downtime
top_5_least_downtime = {}
global info_data
info_data = 0
global split_needed
split_needed = True
global number_of_splits
number_of_splits = 1
global warpoints
warpoints = {
      1: 100,
      2: 200,
      3: 300,
      4: 400,
      5: 600,
      6: 1000,
      7: 1500,
      8: 2000,
      9: 2500
  }
API_URL = os.getenv('API_URL')
PATH = os.getenv('path')
WAR_INFO = os.getenv('WAR_INFO')
API_ID = os.getenv('API_ID')
API_NAME = os.getenv('API_NAME')
API_ATTACKLOG = os.getenv('API_ATTACKLOG')
API_STATS = os.getenv('API_STATS')
API_LB = os.getenv('API_LB')
General_role_id = int(os.getenv('General_role_id'))
Captain_role_id = int(os.getenv('Captain_role_id'))
online_players = {}
global war_ready
war_ready = False

# ID's
garyID = int(os.getenv('garyID'))
evoID = int(os.getenv('evoID'))
juiceID = int(os.getenv('juiceID'))







def process_alliance_data(alliance, alliance_data):
    # alliance = collection.find()
    # alliance_data = API response
    alliance_name = alliance["Name"]
    in_war = alliance_data.get("InWar", False)
    opponent = alliance_data.get("OpponentAllianceId", "")
    current_war_points = alliance_data.get("WarPoints", 0)
    now = datetime.now()

    alliances_collection = db_operations.return_collection("alliances")

    war_duration = timedelta(days=3)

    # Check if a new war has started
    if in_war and not alliance["InWar"]:
        # War started, store initial war points and timestamp
        alliances_collection.update_one(
            {"Name": alliance_name},
            {"$set": {"OpponentAllianceId":opponent,"InWar": True, "initialWarPoints": current_war_points, "warStartTime": now}}
        )
    elif in_war:
        # Calculate war points gained since the war started
        initial_war_points = alliance.get("initialWarPoints", 0)
        points_gained = current_war_points - initial_war_points

        # Check if the war has ended
        war_start_time = alliance.get("warStartTime")
        if war_start_time:
            if isinstance(war_start_time, str):
                war_start_time = datetime.strptime(war_start_time, "%Y-%m-%dT%H:%M:%S.%fZ")

            time_elapsed = now - war_start_time
            remaining_time = war_duration - time_elapsed

            if remaining_time <= timedelta(0):
                # War ended, reset InWar status, points gained, and remaining time
                alliances_collection.update_one(
                    {"Name": alliance_name},
                    {"$set": {"InWar": False, "warStartTime": None, "initialWarPoints": None, "pointsGained": 0, "remainingTime": None}}
                )
            else:
                # Update war points gained and remaining time (in seconds)
                alliances_collection.update_one(
                    {"Name": alliance_name},
                    {"$set": {"OpponentAllianceId":opponent,"pointsGained": points_gained, "remainingTime": int(remaining_time.total_seconds())}}
                )
    else:
        # War has ended, reset pointsGained to 0 and remainingTime to None
        # Update LastUpdate time and current war points if not in war
        alliances_collection.update_one(
            {"Name": alliance_name},
            {"$set": {"OpponentAllianceId":"","pointsGained": 0, "remainingTime": None, "LastUpdate": now, "warpoints": current_war_points, "InWar": False}}
        )

@tasks.loop(minutes=1)
async def check_alliances():
    try:
        alliances = db_operations.get_all_alliances()

        async with aiohttp.ClientSession() as session:
            for alliance in alliances:
                alliance_name = alliance["Name"]
                async with session.get(API_URL + utility_operations.replace_spaces(alliance_name)) as response:
                    if response.status == 200:
                        try:
                            alliance_data = await response.json(content_type='text/plain')

                            process_alliance_data(alliance, alliance_data)

                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON response for alliance: {alliance_name} - {e}")
                            continue

                    else:
                        print(f"Failed to fetch data for alliance: {alliance_name} - Status Code: {response.status}")

    except Exception as e:
        print(f"Error checking alliances: {e}")



async def main():
    check_alliances.start()
    print("running")
    while True:
        await asyncio.sleep(3600)  # Keep the script running

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())