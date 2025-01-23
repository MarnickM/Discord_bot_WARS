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


# Assuming db_operations and API_URL are already defined elsewhere in your code

@tasks.loop(hours=6)
async def check_players_top_alliances():
    try:
        total_players_checked = 0  # Counter to track total players checked
        counter = 0
        errorList = []  # List to track alliances with errors

        # Load the alliances from the JSON file
        json_file_path = os.getenv("path")
        if not json_file_path:
            raise ValueError("Environment variable 'ALLIANCES_JSON_PATH' is not set.")

        # Construct the full path to the JSON file
        full_json_path = os.path.join(json_file_path, "alliances_all1.json")

        # Read the JSON file
        try:
            with open(full_json_path, "r") as f:
                alliances = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find the file at {full_json_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Error decoding JSON in the file {full_json_path}")

        # Fetch detailed info for each alliance from the JSON
        async with aiohttp.ClientSession() as session:
            alliance_names = list(alliances.keys())
            batch_size = 10  # Number of alliances to process per batch
            delay_between_batches = 60  # Delay (in seconds) between batches
            delay_between_requests = 2  # Delay (in seconds) between each request

            # Split alliances into batches
            for i in range(0, len(alliance_names), batch_size):
                batch = alliance_names[i:i + batch_size]
                print(f"|afks_checking  | Processing batch {i // batch_size + 1} with {len(batch)} alliances")

                for alliance_name in batch:
                    # print(f"|afks_checking  | Checking alliance: {alliance_name}")
                    try:
                        async with session.get(f"{API_URL}{alliance_name}") as alliance_response:
                            if alliance_response.status == 200:
                                try:
                                    # Log the response content before parsing
                                    response_text = await alliance_response.text()
                                    if not response_text.strip():  # Handle empty responses
                                        # print(f"|afks_checking  | Skipping empty response for alliance: {alliance_name}")
                                        continue

                                    # Attempt to parse JSON
                                    alliance_info = json.loads(response_text)
                                except json.JSONDecodeError:
                                    # print(f"|afks_checking  | Failed to parse JSON for alliance: {alliance_name}")
                                    errorList.append(alliance_name)  # Add to error list
                                    continue

                                # Process alliance_info as needed
                                members = alliance_info.get("Members", [])
                                print(f"|afks_checking  | Members count for {alliance_name}: {len(members)}")
                                total_players_checked += len(members)  # Add member count to total counter
                                for member in members:
                                    member_name = member['Name']
                                    # print(f"|afks_checking  | checking member: {member_name}")
                                    counter += 1
                                    player_info = db_operations.get_afk(name=member_name)
                                    if player_info:
                                        if player_info['warpoints'] != member['TotalWarPoints']:
                                            db_operations.update_afk(member_name, member['TotalWarPoints'])
                                            # print(f"|afks_checking  | Updated warpoints for {member_name}")
                                    else:
                                        db_operations.create_afk(member_name, member['TotalWarPoints'])
                                        # print(f"|afks_checking  | Created new entry for {member_name}")
                            elif alliance_response.status == 404:
                                # Skip non-existent alliances
                                print(f"|afks_checking  | Alliance {alliance_name} does not exist. Skipping.")
                            elif alliance_response.status in [503, 502]:
                                # Backoff and retry on server errors
                                # print(f"|afks_checking  | Server error ({alliance_response.status}) for {alliance_name}. Retrying later.")
                                 errorList.append(alliance_name)  # Add to error list
                            else:
                                # print(f"|afks_checking  | Failed to fetch details for alliance: {alliance_name}, Status: {alliance_response.status}")
                                errorList.append(alliance_name)  # Add to error list

                        await asyncio.sleep(delay_between_requests)  # Delay between requests

                    except Exception as request_error:
                        # print(f"|afks_checking  | Exception occurred for alliance {alliance_name}: {request_error}")
                        errorList.append(alliance_name)  # Add to error list

                # print(f"|afks_checking  | Completed batch {i // batch_size + 1}. Sleeping before next batch.")
                await asyncio.sleep(delay_between_batches)  # Delay between batches

            # Retry fetching alliances in the error list
            print(f"|afks_checking  | Retrying {len(errorList)} alliances that encountered errors.")
            for alliance_name in errorList:
                try:
                    await asyncio.sleep(45)  # Delay before retrying
                    async with session.get(f"{API_URL}{alliance_name}") as alliance_response:
                        if alliance_response.status == 200:
                            try: 
                                response_text = await alliance_response.text()
                                if not response_text.strip():
                                    # print(f"|afks_checking  | Skipping empty response for alliance: {alliance_name}")
                                    continue

                                alliance_info = json.loads(response_text)
                                members = alliance_info.get("Members", [])
                                # print(f"|afks_checking  | Retried members count for {alliance_name}: {len(members)}")
                                total_players_checked += len(members)
                                for member in members:
                                    member_name = member['Name']
                                    # print(f"|afks_checking  | Retrying check for member: {member_name}")
                                    player_info = db_operations.get_afk(name=member_name)
                                    if player_info:
                                        if player_info['warpoints'] != member['TotalWarPoints']:
                                            db_operations.update_afk(member_name, member['TotalWarPoints'])
                                            # print(f"|afks_checking  | Updated warpoints for {member_name}")
                                    else:
                                        db_operations.create_afk(member_name, member['TotalWarPoints'])
                                        print(f"|afks_checking  | Created new entry for {member_name}")
                            except json.JSONDecodeError:
                                print(f"|afks_checking  | Failed to parse JSON for retried alliance: {alliance_name}")
                        else:
                            print(f"|afks_checking  | Failed to fetch retried alliance: {alliance_name}, Status: {alliance_response.status}")

                except Exception as retry_error:
                    print(f"|afks_checking  | Exception occurred while retrying alliance {alliance_name}: {retry_error}")

        print(f"|afks_checking  | Total players checked in this cycle: {total_players_checked}")

    except Exception as e:
        print(counter)
        print(f"|afks_checking  | Error checking top alliances and players: {e}")


# @tasks.loop(minutes=1)
# async def check_players_top_alliances():
#     try:
#         # Fetch top alliances
#         async with aiohttp.ClientSession() as session:
#             async with session.get(API_LB) as response:
#                 if response.status == 200:
#                     alliances = await response.json(content_type="text/plain")

                    
#                     for alliance in alliances:
#                         alliance_name = alliance['Name']
                        
#                         # Fetch detailed info for each alliance
#                         async with session.get(f"{API_URL}{alliance_name}") as alliance_response:
#                             if alliance_response.status == 200:
#                                 alliance_info = await alliance_response.json(content_type="text/plain")
#                                 # Process alliance_info as needed
#                                 members = alliance_info.get("Members", [])
#                                 for member in members:
#                                     member_name = member['Name']
#                                     print(member_name)
#                                     player_info = db_operations.get_afk(name=member_name)
#                                     if player_info:
#                                         if player_info['warpoints'] != member['TotalWarPoints']:
#                                             db_operations.update_afk(member_name, member['TotalWarPoints'])
#                                     else:
#                                         db_operations.create_afk(member_name, member['TotalWarPoints'])

#                             else:
#                                 print(f"Failed to fetch details for alliance: {alliance_name}")

#     except Exception as e:
#         print(f"Error checking top alliances and players: {e}")


async def main():
    check_players_top_alliances.start()
    print("running")
    while True:
        await asyncio.sleep(3600)  # Keep the script running

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())