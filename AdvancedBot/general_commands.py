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


# set up the bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print('Bot is ready')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
        # check_war_status.start()
        # refresh_main_wp.start()
        # check_alliances.start()
        # update_war_info_from_database.start()
        # update_players_our_alliance.start()
        # get_online_status.start()
        # check_enemy_attacks.start()
        # find_top_5_least_downtime.start()
        # check_players_top_alliances.start()
        info.start()
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    # await reset_message_id()
        await reset_message_id_coords()
        await reset_message_id_coords_groups()

# sync commands
@bot.command()
async def sync(ctx) -> None:
  guild = bot.get_guild(1072190344835387392)
  synced = await bot.tree.sync(guild=guild)
  print(f"Synced {len(synced)} commands.")



async def reset_message_id():
    message = await utility_operations.loadJson(PATH + "message_id_overview.json")
    guild = bot.get_guild(GUILD_ID)
    if guild:
        channel = guild.get_channel(CHANNEL_ID)
        if channel:
            message_id = message["id"]
            if message_id:
                try:
                    message_in_channel = await channel.fetch_message(message_id)
                    if message_in_channel:
                        await message_in_channel.delete()
                    message["id"] = 0
                except Exception as e:
                    message["id"] = 0
            else:
                print("Message ID not found in JSON file")
    await utility_operations.saveJson(PATH + "message_id_overview.json", message)



async def reset_message_id_coords():
    message = await utility_operations.loadJson(PATH + "coords_message.json")
    guild = bot.get_guild(GUILD_ID)
    if guild:
        channel = guild.get_channel(CHANNEL_ID_COORDS)
        if channel:
            message_id = message["id"]
            if message_id:
                try:
                    message_in_channel = await channel.fetch_message(message_id)
                    if message_in_channel:
                        await message_in_channel.delete()
                        print('deleted main message')
                    message["id"] = 0
                except Exception as e:
                    message["id"] = 0
                    print('main message error but id is 0')
    await utility_operations.saveJson(PATH + "coords_message.json", message)





async def reset_message_id_coords_groups():
    for i in range(1,14):
        message = await utility_operations.loadJson(f"{PATH}coords_message_group_{i}.json")
        guild = bot.get_guild(GUILD_ID)
        if guild:
            channel = guild.get_channel(CHANNEL_ID_COORDS)
            if channel:
                message_id = message["id"]
                if message_id:
                    try:
                        message_in_channel = await channel.fetch_message(message_id)
                        if message_in_channel:
                            await message_in_channel.delete()
                            print(f'deleted group {i}')
                        message["id"] = 0
                    except Exception as e:
                        message["id"] = 0
                        print(f'exception but group {i} is 0')
        await utility_operations.saveJson(f"{PATH}coords_message_group_{i}.json", message)



@tasks.loop(seconds=10)
async def check_enemy_attacks():
    global online_players
    global war_ready
    if war_ready == True:
        war = await utility_operations.loadJson(PATH + WAR_INFO)
        alliance_name = war["name"]
        alliance_search = utility_operations.replace_spaces(alliance_name)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL + alliance_search) as response:
                        if response.status == 200:
                            alliance_data = await response.json(content_type='text/plain')
                            members = alliance_data.get("Members", [])

                            try:
                                current_members = db_operations.get_enemy_players()
                            except Exception as e:
                                print(f"Error getting enemy players: {e}")
                            current_member_names = [doc['Name'] for doc in current_members]
                            # Remove players from online_players if they are no longer in the enemy alliance
                            for name in list(online_players.keys()):
                                if name not in current_member_names:
                                    online_players.pop(name, None)

                            for member in members:
                                member_name = member.get("Name", "")
                                try:
                                    player_data = db_operations.find_enemy_player(member_name)
                                except Exception as e:
                                    print(f"Error finding enemy player: {e}")
                                
                                if player_data:
                                    # Check if the player has more war points than the last time we checked
                                    # print(f"Player data: {member_name} - {player_data['total_warpoints']} - {member['TotalWarPoints']}")
                                    if player_data['total_warpoints'] != 0 and member['TotalWarPoints'] != 0:
                                        # print("We got here")
                                        
                                        if player_data['total_warpoints'] < member['TotalWarPoints']:
                                            # print(f"case 1 for {member_name}")
                                            online_players[member_name] = datetime.now()
                                        # If the player has 0 war points and has gained some
                                        elif player_data['total_warpoints'] == 0 and member['TotalWarPoints'] > player_data['initial_warpoints']:
                                            # print(f"case 2 for {member_name}")
                                            online_players[member_name] = datetime.now()
                                        # If the player has the same war points as the last time we checked
                                        elif player_data['total_warpoints'] == member['TotalWarPoints'] and player_data['initial_warpoints'] == player_data['total_warpoints']:
                                            if member_name in online_players:
                                                # Check if the player has been online for more than 15 minutes, if so he is now offline and must be removed
                                                if (datetime.now() - online_players[member_name]) > timedelta(minutes=15):
                                                    # print(f"case 3 for {member_name}")
                                                    online_players.pop(member_name, None)
                                             # Update the player's war points in the database
                                db_operations.update_enemy_player(member_name, member['TotalWarPoints'])

                            # print(online_players)
        except Exception as e:
            print(f"Error checking enemy attacks: {e}")

@tasks.loop(seconds=30)
async def get_online_status():
    global online_players
    global war_ready
    if war_ready == True:
         war = await utility_operations.loadJson(PATH + WAR_INFO)
         for player in war["members"]:
             status = await utility_operations.get_online_status(player)
             if status == 2:
                 online_players[player] = datetime.now()   













# async def time_suggestion(interaction: discord.Interaction, time: int) -> typing.List[app_commands.Choice[int]]:
#     suggestions = [app_commands.Choice(name=str(i), value=i) for i in range(3, 8)]
#     return suggestions

# @bot.tree.command(name="set_time", description="set a custom rebuild time for the war")
# @app_commands.autocomplete(time=time_suggestion)
# @app_commands.describe(time="The time in hours")
# async def set_time(interaction: discord.Interaction, time: int):
#     global regentime
#     if type(time) != int:
#         await interaction.response.send_message("The time must be an integer")
#         return
#     if time < 3:
#         await interaction.response.send_message("The rebuild time cannot be less than 3 hours")
#         return
#     if time > 7:
#         await interaction.response.send_message("The rebuild time cannot be more than 7 hours")
#         return
#     regentime = time
#     await interaction.response.send_message(f"Rebuild time set to {time} hours")





















@tasks.loop(seconds=30)
async def find_top_5_least_downtime():
    try:
        war = await utility_operations.loadJson(PATH + WAR_INFO)
        
        # List to store all planets with their downtimes
        planets = []
        
        for player, player_data in war["members"].items():
            for planet, planet_data in player_data.items():
                downtime_str = planet_data[0]
                downtime = datetime.strptime(downtime_str, "%Y-%m-%d %H:%M:%S")
                planets.append((player, planet, downtime))
        
        # Sort planets by downtime (closest to now)
        planets.sort(key=lambda x: x[2])
        
        # Select the top 5 planets
        top_5 = planets[:5]
        
        # Update the global variable
        global top_5_least_downtime
        top_5_least_downtime = {player: [planet, downtime.strftime("%Y-%m-%d %H:%M:%S")] for player, planet, downtime in top_5}
    
    except FileNotFoundError:
        print(f"Error: The file {PATH + WAR_INFO} was not found.")
    except json.JSONDecodeError:
        print("Error: JSON decoding error.")
    except Exception as e:
        print(f"Error finding top 5 least downtime: {e}")


async def format_top_5_least_downtime():
        global points
        global top_5_least_downtime
        currentTime = datetime.now()
        global info_data
        war = await utility_operations.loadJson(PATH + WAR_INFO)

        if points != 0:
            Enemy_SB_sum = 0
            for player, player_data in war["members"].items():
              if "C0" in player_data:
                sb_value = int(player_data["C0"][2][2:])
                Enemy_SB_sum += sb_value
    
            rebuildTime = utility_operations.get_regenTime(us=points, enemy=Enemy_SB_sum)
    
            timeDifference = 0
            timeLeft = 0
            hoursLeft = 0
            minutesLeft = 0
            formatted_data = ""
            if top_5_least_downtime != {}:
                for player, (colony, downtime) in top_5_least_downtime.items():
                    # Convert downtime string back to a datetime object
                    downtime = datetime.strptime(downtime, "%Y-%m-%d %H:%M:%S")
    
                    timeDifference = currentTime - downtime
                    timeLeft = timedelta(hours=rebuildTime) - timeDifference
                    hoursLeft = timeLeft.seconds // 3600
                    minutesLeft = (timeLeft.seconds % 3600) // 60
                    if minutesLeft > 0:
                        if colony == "C0":
                            formatted_data += f":octagonal_sign: {player}: main - {hoursLeft}h:{minutesLeft}m\n"
                        else:
                            formatted_data += f":octagonal_sign: {player}: {colony} - {hoursLeft}h:{minutesLeft}m\n"
                    else:
                        if colony == "C0":
                            formatted_data += f":white_check_mark: {player}: main - UP\n"
                        else:
                            formatted_data += f":white_check_mark: {player}: {colony} - UP\n"
            return formatted_data
        else:
            return "Booting up...."















async def alliance_suggestion(interaction: discord.Interaction, alliance_name: str) -> typing.List[app_commands.Choice[str]]:
    players = db_operations.get_alliances(alliance_name)
    suggestions = [app_commands.Choice(name=name, value=name) for name in players]
    return suggestions
    

# async def add_new_alliance(alliance_name):
#     async with aiohttp.ClientSession() as session:
#             async with session.get(API_URL + utility_operations.replace_spaces(alliance_name)) as response:
#                 if response.status == 200:
#                     await db_operations.add_alliance(alliance_name)
    
# @bot.tree.command(name="createwar", description="Create a new war")
# @app_commands.autocomplete(alliance=alliance_suggestion)
# @app_commands.checks.has_any_role(General_role_id, Captain_role_id)
# @app_commands.describe(alliance="Name of the enemy alliance")
# async def createwar(interaction: discord.Interaction, alliance: str):
#     await interaction.response.defer() # Defer the response to avoid timeout
#     await asyncio.sleep(1.5)  # Sleep for 1 second to avoid
    
#     global war_ready
#     if db_operations.get_alliances(alliance) == []:
#         await add_new_alliance(alliance)
        
#     if alliance is None:
#         await interaction.followup.send("Please write the enemy alliance name!")
#         return
    
#     global regentime
#     regentime = 0

#     war = await utility_operations.loadJson(PATH + WAR_INFO)
#     if war["name"] == alliance:
#         await interaction.followup.send(f"War against {alliance} has already been created")
#         return

#     await db_operations.initiate_enemy_players(alliance)
#     war_ready = True
#     try:
#         # Fetch data for the enemy alliance
#         async with aiohttp.ClientSession() as session:
#             async with session.get(API_URL + utility_operations.replace_spaces(alliance)) as response:
#                 if response.status == 200:
#                     enemy_alliance_data = await response.json(content_type='text/plain')
#                     members = enemy_alliance_data.get("Members", [])
#                     members.sort(key=lambda x: x.get("Level", ""))

#                     war_members = {}
#                     for member in members:
#                         player_name = member.get("Name", "")
#                         player_id = member.get("Id", "")

#                         # Fetch player details from your database
#                         player_data = db_operations.find_player(player_name)
#                         if player_data is None:
#                             # If player_data is None, create a new player entry
#                             player_data = {"Alliance": "Alliance name", "Name": player_name, "id": player_id}
#                             player_data["C0"] = []

#                             # Fetch player info from API to get main planet's starbase level
#                             async with session.get(API_ID + player_id) as player_response:
#                                 if player_response.status == 200:
#                                     player_info = await player_response.json(content_type='text/plain')
#                                     planets = player_info.get("Planets", [])
#                                     if planets:
#                                         main_planet_hq_level = planets[0].get("HQLevel", "")
#                                         player_data["C0"].append((datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"))
#                                         player_data["C0"].append("0")
#                                         player_data["C0"].append(f"SB{main_planet_hq_level}")
#                                     else:
#                                         player_data["C0"] = []

#                                     # Add empty colonies C1-C11
#                                     for i in range(1, 12):
#                                         player_data[f"C{i}"] = []

#                                     # Add player to database
#                                     insert_result = db_operations.add_player(player_data)
#                                     if not insert_result:
#                                         raise Exception(f"Failed to add player {player_name} to the database")

#                         # Extract filled coordinates for the player
#                         player_coordinates = {}
#                         for i in range(0, 12):  # Iterate over C1 to C11
#                             colony_key = f"C{i}"
#                             if colony_key in player_data and player_data[colony_key] and len(player_data[colony_key]) == 3:
#                                 player_coordinates[colony_key] = player_data[colony_key]
                            
#                         # Add player coordinates to war_members
#                         war_members[player_name] = player_coordinates

#                     # Update war information with enemy alliance details
#                     war["name"] = alliance
#                     war["members"] = war_members

#                     # Save updated war_info.json
#                     await utility_operations.saveJson(PATH + WAR_INFO, war)
#                     # await utility_operations.get_sorted_players_by_sb_level(PATH + WAR_INFO)

#                     await interaction.followup.send(f"War has been created against {alliance}")

#                 else:
#                     await interaction.followup.send(f"Failed to fetch data for enemy alliance - Status Code: {response.status}")

#     except Exception as e:
#         await interaction.followup.send(f"Error creating war: {e}")


# @createwar.error
# async def createwar_error(interaction: discord.Interaction, error):
#     await interaction.response.send_message(f"You do not have the required permissions to create a war: {error}")










# @bot.tree.command(name="war_ready", description="(Gary only) Re-enable auto update for war info in case of bot restart")
# @app_commands.checks.has_role(General_role_id)
# async def war_ready(interaction: discord.Interaction):
#     global war_ready
#     war_ready = True
#     await interaction.response.send_message("War_ready set to True", ephemeral=True)

# @war_ready.error
# async def war_ready_error(interaction: discord.Interaction, error):
#     await interaction.response.send_message(f"You do not have the required role to use this command.", ephemeral=True)











@tasks.loop(seconds=10)
async def update_war_info_from_database():
    if war_ready == True:
         try:
             # Load current war_info.json
             war_info = await utility_operations.loadJson(PATH + WAR_INFO)
     
             # Get all members from war_info
             members = war_info.get("members", {})
             # print(f"Members: {members}")
     
             # Iterate over each member and update their colonies
             for member_name, colonies in members.items():
                 # Fetch player data from your database
                 player_data = db_operations.find_player(member_name)
     
                 if player_data:
                     # Clear existing colonies for the member
                     members[member_name] = {}
     
                     # Update colonies C0-C11
                     for i in range(0, 12):
                         colony_key = f"C{i}"
                         if colony_key in player_data and player_data[colony_key] and len(player_data[colony_key]) == 3:
                             members[member_name][colony_key] = player_data[colony_key]
     
             # Update war_info with modified members data
             war_info["members"] = members
     
             # Save updated war_info.json
             await utility_operations.saveJson(PATH + WAR_INFO, war_info)
             await utility_operations.get_sorted_players_by_sb_level(PATH + WAR_INFO)
     
         except Exception as e:
             print(f"Error updating war_info.json: {e}")

    else:
        current_time = datetime.now() - timedelta(hours=8)
        current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        war = await utility_operations.loadJson(PATH + WAR_INFO)
        try:
            
            for player, player_data in war["members"].items():
                for planet, planet_data in player_data.items():
                    if planet_data[0] == "unknown":
                        
                        # Find player data in the database
                        db_player_data = db_operations.find_player(player)
                        if db_player_data:
                            colony = planet
                            current_data = db_player_data[colony]
                            
                            # Update the downtime
                            new_data = [current_time, current_data[1], current_data[2]]
                            
                            # Update the database
                            db_operations.update_colony(player, colony, new_data)
        
        except FileNotFoundError:
            print(f"Error: The file {PATH + WAR_INFO} was not found.")
        except json.JSONDecodeError:
            print("Error: JSON decoding error.")
        except KeyError as e:
            print(f"Error: Missing key in data structure - {e}")
        except Exception as e:
            print(f"Error removing unknowns: {e}")
    










@tasks.loop(minutes=1)
async def refresh_main_wp():
    try:
        global points
        global warpoints
        # Fetch alliance data
        async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.galaxylifegame.net/Alliances/get?name=Galactic%20Empire%20II") as alliance_response:
                        alliance_data = await alliance_response.json(content_type='text/plain')
        
        if alliance_response.status == 200:
            members = alliance_data.get("Members", [])
            for member in members:
                member_id = member["Id"]
                
                # Fetch player data using member_id
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.galaxylifegame.net/Users/get?id={member_id}") as player_response:
                         if player_response.status == 200:

                             player_data = await player_response.json(content_type='text/plain')
                             planets = player_data.get("Planets", [])
                             
                             if planets:
                                 first_planet_hq_level = planets[0].get("HQLevel", 0)
                                #  wp = warpoints.get(first_planet_hq_level, 0)
                                #  points += wp
                                 points += first_planet_hq_level
                             else:
                                 print(f"No planets found for player ID {member_id}")
                         else:
                             print(f"Failed to fetch player data for ID {member_id} - Status Code: {player_response.status}")
        
        else:
            print(f"Failed to fetch alliance data - Status Code: {alliance_response.status}")
    
    except Exception as e:
        print(f"Error in refresh_main_wp function: {e}")









    
















# @bot.tree.command(name="info", description="Get all the enemy planets")
# async def info(interaction: discord.Interaction):
#   await interaction.response.defer()
#   await asyncio.sleep(5)
#   war = await utility_operations.loadJson(PATH + WAR_INFO)
  
# #   await utility_operations.get_sorted_players_by_sb_level(PATH + WAR_INFO)
  
#   EnemyAlliance_wp_sum = 0
#   Enemy_SB_sum = 0
#   EnemyAlliance_total_wp_sum = 0


#   for player, player_data in war["members"].items():
#     if "C0" in player_data:
#       sb_value = int(player_data["C0"][2][2:])
#       EnemyAlliance_wp_sum += warpoints.get(sb_value, 0)
#       Enemy_SB_sum += sb_value

#   for player, player_data in war["members"].items():
#     for planet, planet_data in player_data.items():
#         sb_value = int(planet_data[2][2:])
#         EnemyAlliance_total_wp_sum += warpoints.get(sb_value, 0)

#   actualRegenTime = utility_operations.get_regenTime(us=points, enemy=Enemy_SB_sum)
#   enemyRegenTime = utility_operations.get_regenTime(us=Enemy_SB_sum, enemy=points)
#   global regentime
#   if regentime != 0:
#     actualRegenTime = regentime
  
#   embed = discord.Embed(
#       title=war["name"],
#       description=
#       f"WP main {EnemyAlliance_wp_sum} / total WP {EnemyAlliance_total_wp_sum}",
#       color=discord.Colour.from_rgb(0,0,0))
#   currentTime = datetime.now()

# #   claim = await utility_operations.loadJson("./claim.json")

#   global info_data 
#   info_data = actualRegenTime

#   if len(war["members"]) <= 25:
#     for member in war["members"]:
#       text = ""
#       for planet in war["members"][member]:

#         # checking if time is unknown
#         if war["members"][member][planet][0] == "unknown":
#             starbaselvl = war["members"][member][planet][2]
#             if planet== "C0":
#               text += f":warning: main {starbaselvl}-> ????\n"
#               continue
#             else:
#               coords = war["members"][member][planet][1]
#               text += f":warning: {planet} {coords} {starbaselvl}-> ????\n"
#               continue

#         if war["members"][member][planet][0] == "0":
#           # get the starbase lvl from position 2
#           starbaselvl = war["members"][member][planet][2]
#           if planet == "C0":

#             # check for claims
#             # claimed = False
#             # for key,value in claim["members"].items():
#             #    if member == value[2] and value[0] == "claimed" and value[3] == "C0":
#             #       text += f":lock: main  {starbaselvl}-> UP\n"
#             #       claimed = True
#             # if claimed == False:
#             text += f":white_check_mark: main  {starbaselvl}-> UP\n"

#           else:
#             coords = war["members"][member][planet][1]
#             # for key,value in claim["members"].items():
#             #    if war["members"][member] == value[2] and value[0] == "claimed" and value[3] == planet:
#             #       text += f":lock: {planet} {coords} {starbaselvl}-> UP\n"
#             #       claimed = True

#             # if claimed == False:
#             text += f":white_check_mark: {planet} {coords} {starbaselvl}-> UP\n"
#           continue

#         tempTime = war["members"][member][planet][0]
#         tempTime = datetime.strptime(tempTime, "%Y-%m-%d %H:%M:%S")

#         timeDifference = currentTime - tempTime
#         # added the actualRegenTime instead of the hard coded 3h time
#         if timeDifference >= timedelta(hours=actualRegenTime):
#           war["members"][member][planet][0] = "0"
#           # get the starbase lvl from position 2
#           starbaselvl = war["members"][member][planet][2]

#           if planet == "C0":
#             # claimed = False
#             # for key,value in claim["members"].items():
#             #    if war["members"][member] == value[2] and value[0] == "claimed" and value[3] == "C0":
#             #       text += f":lock: main  {starbaselvl}-> UP\n"
#             #       claimed = True

#             # if claimed == False:
#             text += f":white_check_mark: main {starbaselvl}-> UP\n"
#           else:
#             starbaselvl = war["members"][member][planet][2]
#             coords = war["members"][member][planet][1]
#             # claimed = False
#             # for key,value in claim["members"].items():
#             #    if war["members"][member] == value[2] and value[0] == "claimed" and value[3] == planet:
#             #       text += f":lock: {planet} {coords} {starbaselvl}-> UP\n"
#             #       claimed = True

#             # if claimed == False:
#             text += f":white_check_mark: {planet} {coords} {starbaselvl}-> UP\n"
#         else:
#           # added the actualRegenTime instead of the hard coded 3h time
#           timeLeft = timedelta(hours=actualRegenTime) - timeDifference
#           hoursLeft = timeLeft.seconds // 3600
#           minutesLeft = (timeLeft.seconds % 3600) // 60

#           ptemp = ":octagonal_sign: " + planet
#           coords = war["members"][member][planet][1]
#           # get the starbase lvl from position 2
#           starbaselvl = war["members"][member][planet][2]


#           if planet == "C0":

#             # claimed = False
#             # for key,value in claim["members"].items():
#             #     if war["members"][member] == value[2] and value[0] == "claimed" and value[3] == "C0":
#             #       ptemp = ":lock: main"
#             #       coords = ""
#             #       claimed = True

#             # if claimed == False:
#               ptemp = ":octagonal_sign: main"
#               coords = ""
          
#         #   for key,value in claim["members"].items():
#         #       if war["members"][member] == value[2] and value[0] == "claimed" and value[3] == planet:
#         #         ptemp = ":lock:" + planet

#           # added starbaselvl in the display
#           text += f"{ptemp} {coords} {starbaselvl}-> {hoursLeft}h:{minutesLeft}m\n"

#       embed.add_field(name=member, value=text, inline=True)

#     embed.set_footer(text=f"Rebuild time: {actualRegenTime} / Enemy rebuild time: {enemyRegenTime}")
#     await utility_operations.saveJson(PATH + WAR_INFO, war)
#     await interaction.followup.send(embed=embed)

#   else:
#     max_members_per_embed = 25

#     # Calculate the total number of members
#     total_members = len(war["members"])

#     # Iterate over members in chunks of max_members_per_embed
#     for start_index in range(0, total_members, max_members_per_embed):
#       end_index = start_index + max_members_per_embed
#       current_members = list(war["members"].items())[start_index:end_index]

#       embed = discord.Embed(
#           title=war["name"],
#           description=
#           f"WP main {EnemyAlliance_wp_sum} / total WP {EnemyAlliance_total_wp_sum}",
#           color=discord.Colour.from_rgb(0,0,0))

#       for member, member_data in current_members:
#         text = ""
#         for planet in member_data:

#             # checking if time is unknown
#           if war["members"][member][planet][0] == "unknown":
#               starbaselvl = war["members"][member][planet][2]
#               if planet== "C0":
#                 text += f":warning: main {starbaselvl}-> ????\n"
#                 continue
#               else:
#                 coords = war["members"][member][planet][1]
#                 text += f":warning: {planet} {coords} {starbaselvl}-> ????\n"
#                 continue

#           if war["members"][member][planet][0] == "0":
#             # get the starbase lvl from position 2
#             starbaselvl = war["members"][member][planet][2]
#             if planet == "C0":
#               text += f":white_check_mark: main  {starbaselvl}-> UP\n"
#             else:
#               coords = war["members"][member][planet][1]
#               text += f":white_check_mark: {planet} {coords} {starbaselvl}-> UP\n"
#             continue

#           tempTime = war["members"][member][planet][0]
#           tempTime = datetime.strptime(tempTime, "%Y-%m-%d %H:%M:%S")

#           timeDifference = currentTime - tempTime
#           # added the actualRegenTime instead of the hard coded 3h time
#           if timeDifference >= timedelta(hours=actualRegenTime):
#             war["members"][member][planet][0] = "0"
#             # get the starbase lvl from position 2
#             starbaselvl = war["members"][member][planet][2]
#             if planet == "C0":
#               text += f":white_check_mark: main {starbaselvl}-> UP\n"
#             else:
#               coords = war["members"][member][planet][1]
#               # get the starbase lvl from position 2
#               starbaselvl = war["members"][member][planet][2]
#               # added the starbaselvl in the display
#               text += f":white_check_mark: {planet} {coords} {starbaselvl}-> UP\n"
#           else:
#             # added the actualRegenTime instead of the hard coded 3h time
#             timeLeft = timedelta(hours=actualRegenTime) - timeDifference
#             hoursLeft = timeLeft.seconds // 3600
#             minutesLeft = (timeLeft.seconds % 3600) // 60

#             ptemp = ":octagonal_sign: " + planet
#             coords = war["members"][member][planet][1]
#             # get the starbase lvl from position 2
#             starbaselvl = war["members"][member][planet][2]
#             if planet == "C0":
#               ptemp = ":octagonal_sign: main"
#               coords = ""

#             # added starbaselvl in the display
#             text += f"{ptemp} {coords} {starbaselvl}-> {hoursLeft}h:{minutesLeft}m\n"

#         embed.add_field(name=member, value=text, inline=True)

#       embed.set_footer(text=f"Rebuild time: {actualRegenTime} / Enemy rebuild time: {enemyRegenTime}")
#       await utility_operations.saveJson(PATH + WAR_INFO, war)
#       await interaction.followup.send(embed=embed)













    

@bot.tree.command(name="status", description="Give status of top 50 alliances")
async def status(interaction: discord.Interaction):
    await interaction.response.defer()
    await asyncio.sleep(3)
    await interaction.followup.send("Please be patient... gathering info, it can take up to 3min.")
    
    retries = 3  # Number of retries for 502 errors
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.galaxylifegame.net/Alliances/warpointLb") as response:
                    if response.status == 502 or response.status == 500 or response.status == 503 or response.status == 504:  # Check for 502 error
                        code = response.status
                        if attempt < retries - 1:
                            await interaction.followup.send(f":octagonal_sign: HTTP error encountered. **Code:{code}** Retrying... ({attempt + 1}/{retries})")
                            await asyncio.sleep(2)  # Wait before retrying
                            continue
                        else:
                            await interaction.followup.send("Failed to retrieve data after multiple attempts due to 502 errors. API server refuses to coöperate. :angry: ")
                            return
                        
                    succes = False
                    # First, try to parse as text/plain (expecting JSON)
                    try:
                        alliance_data = await response.json(content_type="text/plain")  # Default to plain text
                        succes = True
                    except Exception:
                        # If it fails, fall back to parsing as text/html
                        alliance_data = await response.json(content_type="text/html")
                        succes : True
                    
                    if succes == True:
                        await interaction.followup.send("✅ leaderbord fetched succesfully \n ⚠️ starting loop over alliances...")

                    alliance_data = alliance_data[:50]
                    total_alliances = len(alliance_data)
                    num_batches = (total_alliances + 24) // 25  # Calculate the number of batches

                    for batch in range(num_batches):
                        start_index = batch * 25
                        end_index = min(start_index + 25, total_alliances)

                        embed = discord.Embed(title=f"Status of top 50 alliances - Part {batch + 1}",
                                      color=discord.Colour.from_rgb(255, 191, 0))

                        for i in range(start_index, end_index):
                            text = ""
                            alliance = alliance_data[i]
                            alliance_search = utility_operations.replace_spaces(alliance["Name"])
                            async with aiohttp.ClientSession() as session:
                                async with session.get(f"https://api.galaxylifegame.net/Alliances/get?name={alliance_search}") as response:
                                    # First try to parse as JSON (text/plain)
                                    try:
                                        alliance_info = await response.json(content_type="text/plain")
                                    except Exception:
                                        # If the JSON parsing fails, fallback to text/html
                                        alliance_info = await response.json(content_type="text/html")

                                    wins = alliance_info['WarsWon']
                                    losses = alliance_info['WarsLost']
                                    winrate_value = ((wins / (wins + losses)) * 100) if wins + losses > 0 else None
                                    winrate = f"{winrate_value:.2f}%" if winrate_value is not None else "N/A"
                                    difficulty = "⭐️⭐️⭐️" if winrate_value is not None and winrate_value > 90 else \
                                                 "⭐️⭐️" if winrate_value is not None and winrate_value > 70 else \
                                                 "⭐️"

                                    # AFK Check
                                    afk_count = 0
                                    total_members = len(alliance_info['Members'])
                                    now = datetime.now()
                            
                                    for member in alliance_info['Members']:
                                        name = member["Name"]
                                        player_status = db_operations.get_afk(name)
                            
                                        if player_status:
                                            last_update = player_status['last_update']
                                            days_since_last_update = (now - last_update).days
                            
                                            if days_since_last_update >= 10:  # Considered AFK if not active in the last 10 days
                                                afk_count += 1
                            
                                    afk_stats = f"`{afk_count}/{total_members} AFK`"

                                    matchmaking_data = db_Alex.get_shield(alliance_info['Name'])
                                    shieldRemainingTimeStamp = "N/A"

                                    if (matchmaking_data['InWar'] == False):
                                       if (matchmaking_data['HasWon'] == True):
                                            shieldRemainingTimeStamp = matchmaking_data['LastUpdate'] + 2 * 86400
                                       if (matchmaking_data['HasWon'] == False):
                                            shieldRemainingTimeStamp = matchmaking_data['LastUpdate']  + 3 * 86400

                                    if shieldRemainingTimeStamp != "N/A":
                                        text += f"🏆 {wins} ({winrate})\n {afk_stats}\n :shield: <t:{int(shieldRemainingTimeStamp)}:R> \n"
                                    else:
                                        text += f"🏆 {wins} ({winrate})\n {afk_stats}\n"

                            if alliance_info["InWar"]:
                                alliance_search = utility_operations.replace_spaces(alliance_info["OpponentAllianceId"])
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(f"https://api.galaxylifegame.net/Alliances/get?name={alliance_search}") as opponents:
                                        try:
                                            enemy_alliance_data = await opponents.json(content_type="text/plain")
                                        except Exception:
                                            enemy_alliance_data = await opponents.json(content_type="text/html")

                                text += f"<:white_cross_mark:1264941382045536419> in war with {enemy_alliance_data['Name']}\n {difficulty}"
                            else:
                                text += f"✅ not in war\n {difficulty}"
                            embed.add_field(name=f"#{i + 1} {alliance_info['Name']}", value=text)
                            embed.set_footer(text="players are considered afk if they have not been active in the last 10 days")

                        await interaction.followup.send(embed=embed)
            break  # Exit retry loop if successful
        except Exception as e:
            if attempt < retries - 1:
                await interaction.followup.send(f"An error occurred: {e}. Retrying... ({attempt + 1}/{retries})")
                await asyncio.sleep(2)  # Wait before retrying
            else:
                await interaction.followup.send(f"Failed to retrieve data after multiple attempts. Error: {e}")
                return

















async def player_suggestion(interaction: discord.Interaction, player_name: str) -> typing.List[app_commands.Choice[str]]:
    players = db_operations.get_players(player_name)
    suggestions = [app_commands.Choice(name=name, value=name) for name in players]
    return suggestions

# @bot.tree.command(name="addcolony", description="Add a new colony")
# @app_commands.autocomplete(name=player_suggestion)
# @app_commands.describe(name="Player name", colony="Colony number", coordinates="Coordinates", sb="Starbase level")
# async def addcolony(interaction: discord.Interaction, name: str, colony: int, coordinates: str, sb: int):
#     await interaction.response.defer() # Defer the response to avoid timeout
#     await asyncio.sleep(1.5)  # Sleep for 1 second to avoid
    
#     # Get current date and time
#     current_time = datetime.now()
#     current_time -= timedelta(hours=8)
#     current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

#     # Check if the player exists
#     existing_player = db_operations.find_player(name)
#     if existing_player:
#         colony_data = [current_time, coordinates, f"SB{sb}"]
#         colony_num = f"C{colony}"
        
#         # Check if colony_num already exists in player's data
#         if colony_num in existing_player:
#             # Clear existing colony data (if needed)
#             existing_player[colony_num] = []  # Replace with empty list to clear data
        
#         # Add or update colony data
#         existing_player[colony_num] = colony_data
        
#         # Update the player's data in the database
#         update_result = db_operations.update_colony(name=name, colony_num=colony_num, colony_data=colony_data)
    
#         if update_result:
#             await interaction.followup.send(f"Updated colony data for {name}: {colony_num} - {coordinates} - SB{sb}")
#         else:
#             await interaction.followup.send(f"Failed to update colony data for {name}")
#     else:
#         # Player does not exist, create a new player entry with basic layout
#         player_data = {"Alliance": "Alliance name", "Name": name, "id": ""}
#         colony_data = [current_time, coordinates, f"SB{sb}"]
#         colony_num = f"C{colony}"
        
#         downtime = current_time
#         war_info = await utility_operations.loadJson(PATH + WAR_INFO)
#         if name in war_info["members"]:
#             downtime = war_info["members"][name]["C0"][0]
#             if downtime == "0":
#                 downtime = current_time

#         async with aiohttp.ClientSession() as session:
#             async with session.get(API_NAME + name) as response:
#                 if response.status == 200:
#                     player_info = await response.json(content_type='text/plain')
#                     planets = player_info.get("Planets", [])
#                     if planets:
#                         main_planet_hq_level = planets[0].get("HQLevel", "")
#                         player_data["C0"] = [downtime, "0", f"SB{main_planet_hq_level}"]
#                 else:
#                     await interaction.followup.send(f"Failed to fetch player data for {name} - Status Code: {response.status}")
        
#         # Add empty colonies C1-C11
#         for i in range(1, 12):
#             player_data[f"C{i}"] = []
        
#         # Add the new colony data
#         player_data[colony_num] = colony_data
        
#         insert_result = db_operations.add_player(player_data)
#         if insert_result:
#             await interaction.followup.send(f"Added new player {name} with {colony_data[1]} and {colony_data[2]}")
#         else:
#             await interaction.followup.send(f"Failed to add new player {name}")



# @addcolony.error
# async def addcolony_error(interaction: discord.Interaction, error):
#     await interaction.response.send_message(f"An error occurred: {error}")



# @bot.tree.command(name="multi_addcolony", description="Add multiple colonies for a single player (respect the order of input)")
# @app_commands.autocomplete(name=player_suggestion)
# @app_commands.describe(name="Player name", colonies="Colony numbers separated by ;", coordinates="Coordinates separated by ;", sb="Starbase levels separated by ;")
# async def multi_addcolony(interaction: discord.Interaction, name: str, colonies: str, coordinates: str, sb: str):
#     await interaction.response.defer()  # Defer the response to avoid timeout
#     await asyncio.sleep(1.5)  # Sleep for 1 second to avoid

#     multiple_colonies = ';' in colonies and ';' in coordinates and ';' in sb

#     # Parse input strings
#     if multiple_colonies:
#        colony_numbers = colonies.split(';')
#        coordinates_list = coordinates.split(';')
#        starbases = sb.split(';')
#     else:
#         await interaction.followup.send("You are missing a **;** in your input.")

#     # Ensure the lengths match
#     if not (len(colony_numbers) == len(coordinates_list) == len(starbases)):
#         await interaction.followup.send("The number of colonies, coordinates, and starbase levels must match.")
#         return

#     # Get current date and time
#     current_time = datetime.now()
#     current_time -= timedelta(hours=8)
#     current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

#     # Check if the player exists
#     existing_player = db_operations.find_player(name)
#     if not existing_player:
#         # Player does not exist, create a new player entry with basic layout
#         player_data = {"Alliance": "Alliance name", "Name": name, "id": ""}
#         # Ensure C0 is always added first
#         player_data["C0"] = []
#         # Add empty colonies C1-C11
#         for i in range(1, 12):
#             player_data[f"C{i}"] = []

#     results = []

#     # Loop through the colonies, coordinates, and starbases
#     for colony, coordinate, starbase in zip(colony_numbers, coordinates_list, starbases):
#         colony_num = f"C{colony}"
#         if int(colony) < 1 or int(colony) > 11:
#             results.append(f"Invalid colony number: {colony} for {name}")
#             continue
#         colony_data = [current_time, coordinate, f"SB{starbase}"]

#         if existing_player:
#             # Update existing player
#             if colony_num in existing_player:
#                 # Clear existing colony data (if needed)
#                 existing_player[colony_num] = []  # Replace with empty list to clear data

#             # Add or update colony data
#             existing_player[colony_num] = colony_data

#             # Update the player's data in the database
#             update_result = db_operations.update_colony(name=name, colony_num=colony_num, colony_data=colony_data)
#             if update_result:
#                 results.append(f"Updated colony {colony_num} for {name}: {coordinate} - SB{starbase}")
#             else:
#                 results.append(f"Failed to update colony {colony_num} for {name}")
#         else:
#             # Add the new colony data for the new player
#             player_data[colony_num] = colony_data

#     if not existing_player:
#         # Insert new player into the database
#         insert_result = db_operations.add_player(player_data)
#         if insert_result:
#             results.append(f"Added new player {name} with colonies: " + ", ".join([f"{player_data[col][1]} - {player_data[col][2]}" for col in player_data if col.startswith('C') and player_data[col]]))
#         else:
#             results.append(f"Failed to add new player {name}")

#     await interaction.followup.send("\n".join(results))







        










async def player_war_suggestion(interaction: discord.Interaction, player_name: str) -> typing.List[app_commands.Choice[str]]:
    players = await db_operations.get_players_from_json(player_name)
    suggestions = [app_commands.Choice(name=name, value=name) for name in players]
    return suggestions

# @bot.tree.command(name="delcolony", description="Delete a colony")
# @app_commands.autocomplete(name=player_war_suggestion)
# @app_commands.describe(name="Player name", colony="Colony number")
# async def delcolony(interaction: discord.Interaction, name: str, colony: int):
#     # Check if the player exists
#     existing_player = db_operations.find_player(name)
    
#     if existing_player:
#         colony_num = f"C{colony}"
        
#         # Check if colony_num exists in player's data
#         if colony_num in existing_player:
#             # Update the colony field to an empty array
#             existing_player[colony_num] = []
            
#             # Update the player's data in the database
#             update_result = db_operations.update_colony(name=name, colony_num=colony_num, colony_data=[])
            
#             if update_result:
#                 await interaction.response.send_message(f"Deleted {colony_num} for {name}")
#             else:
#                 await interaction.response.send_message(f"Failed to delete colony for {name}")
#         else:
#             await interaction.response.send_message(f"{colony_num} does not exist for {name}")
#     else:
#         await interaction.response.send_message(f"Player {name} does not exist")













# @bot.tree.command(name="unknown", description="Set the down time of an enemy to unknown")
# @app_commands.autocomplete(name=player_war_suggestion)
# async def unknown(interaction: discord.Interaction, name: str, colony: str = "0"):
#       await interaction.response.defer()
#       await asyncio.sleep(2)
#       war = await utility_operations.loadJson(PATH + WAR_INFO)
#       if colony != "0":
#         if int(colony) < 1 or int(colony) > 11:
#           await interaction.followup.send("There can only be colonies between 1 and 11")
#           return
    
#       ctemp = "C" + colony

#       existing_player = db_operations.find_player(name)
#       if existing_player:
#            colony_num = f"C{colony}"
#            current_data = []
#            current_time = "unknown"
           
#            # Check if colony_num already exists in player's data
#            if colony_num in existing_player:
#                # check if it is empty
#                if existing_player[colony_num] == []:
#                    await interaction.followup.send(f"{colony_num} of {name} doesn't exist")
#                    return
#                current_data = existing_player[colony_num]
#                # Clear existing colony data (if needed)
#                existing_player[colony_num] = []  # Replace with empty list to clear data
           
#            # only change the time
#            colony_data = [current_time, current_data[1], current_data[2]]
#            # Add or update colony data
#            existing_player[colony_num] = colony_data
           
#            # Update the player's data in the database
#            update_result = db_operations.update_colony(name=name, colony_num=colony_num, colony_data=colony_data)
       
#            if update_result:
#                if colony == "0":
#                    await interaction.followup.send(f"**{name}** **main** down time unkown")
#                else:
#                    await interaction.followup.send(f"**{name}** **{ctemp}** down time unknown")
#            else:
#                await interaction.followup.send(f"Failed to set {colony_num} downtime unknown for {name}")
#       elif existing_player is None:
#            await interaction.followup.send(f"Player {name} does not exist")














# @bot.tree.command(name="down", description="Mark an enemy as destroyed")
# @app_commands.autocomplete(name=player_war_suggestion)
# @app_commands.describe(name="Player name", colony="Colony number")
# async def down(interaction: discord.Interaction, name: str, colony: int = 0):
#     await interaction.response.defer() # Defer the response to avoid timeout
#     await asyncio.sleep(2)  # Sleep for 1 second to avoid

#     if (colony < 1 or colony > 11) and colony != 0:
#         await interaction.followup.send("Colony number must be between 1 and 11")
#         return
#     if type(colony) != int:
#         await interaction.followup.send("Colony number must be an integer")
#         return
    
#     # Get current date and time
#     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     # Check if the player exists
#     existing_player = db_operations.find_player(name)
#     if existing_player:

#         colony_num = f"C{colony}"
#         current_data = []
        
#         # Check if colony_num already exists in player's data
#         if colony_num in existing_player:
#             # check if it is empty
#             if existing_player[colony_num] == []:
#                 await interaction.followup.send(f"{colony_num} of {name} doesn't exist")
#                 return
#             current_data = existing_player[colony_num]
#             # Clear existing colony data (if needed)
#             existing_player[colony_num] = []  # Replace with empty list to clear data
        
#         # only change the time
#         colony_data = [current_time, current_data[1], current_data[2]]
#         # Add or update colony data
#         existing_player[colony_num] = colony_data
        
#         # Update the player's data in the database
#         update_result = db_operations.update_colony(name=name, colony_num=colony_num, colony_data=colony_data)
    
#         if update_result:
#             if colony == 0:
#                 await interaction.followup.send(f"Main down of {name}")
#             else:
#                 await interaction.followup.send(f"{colony_num} down of {name}")
#         else:
#             await interaction.followup.send(f"Failed to down {colony_num} of {name}")
#     elif existing_player is None:
#         await interaction.followup.send(f"Player {name} does not exist")













# @bot.tree.command(name="up", description="Mark an enemy as rebuild")
# @app_commands.autocomplete(name=player_war_suggestion)
# @app_commands.describe(name="Player name", colony="Colony number")
# async def up(interaction: discord.Interaction, name: str, colony: int = 0):
#     await interaction.response.defer() # Defer the response to avoid timeout
#     await asyncio.sleep(2)  # Sleep for 1 second to avoid
    
#     if (colony < 1 or colony > 11) and colony != 0:
#         await interaction.followup.send("Colony number must be between 1 and 11")
#         return
#     if type(colony) != int:
#         await interaction.followup.send("Colony number must be an integer")
#         return
    
#     # Get current date and time
#     current_time = datetime.now()
#     current_time -= timedelta(hours=8)
#     current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

#     # Check if the player exists
#     existing_player = db_operations.find_player(name)
#     if existing_player:

#         colony_num = f"C{colony}"
#         current_data = []
        
#         # Check if colony_num already exists in player's data
#         if colony_num in existing_player:
#             # check if it is empty
#             if existing_player[colony_num] == []:
#                 await interaction.followup.send(f"{colony_num} of {name} doesn't exist")
#                 return
#             current_data = existing_player[colony_num]
#             # Clear existing colony data (if needed)
#             existing_player[colony_num] = []  # Replace with empty list to clear data
        
#         # only change the time
#         colony_data = [current_time, current_data[1], current_data[2]]
#         # Add or update colony data
#         existing_player[colony_num] = colony_data
        
#         # Update the player's data in the database
#         update_result = db_operations.update_colony(name=name, colony_num=colony_num, colony_data=colony_data)
    
#         if update_result:
#             if colony == 0:
#                 await interaction.followup.send(f"Main up of {name}")
#             else:
#                 await interaction.followup.send(f"{colony_num} up of {name}")
#         else:
#             await interaction.followup.send(f"Failed to up {colony_num} of {name}")
#     elif existing_player is None:
#         await interaction.followup.send(f"Player {name} does not exist")
















@bot.tree.command(name="war", description="Get the current war status")
@app_commands.autocomplete(alliance_name=alliance_suggestion)
@app_commands.describe(alliance_name="Name of the alliance")
async def war(interaction: discord.Interaction, alliance_name: str):
    try:
        # Fetch data for the user's alliance
        alliance_search = utility_operations.replace_spaces(alliance_name)
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL + alliance_search) as response:

                 if response.status == 200:
                     alliance_data = await response.json(content_type="text/plain")
                     in_war = alliance_data.get("InWar", False)
         
                     if in_war:
                         enemy_alliance_id = alliance_data.get("OpponentAllianceId", "Unknown")
         
                         # Fetch data for the enemy alliance
                         async with aiohttp.ClientSession() as session:
                                async with session.get(API_URL + utility_operations.replace_spaces(enemy_alliance_id)) as enemy_alliance_response:
                                   if enemy_alliance_response.status == 200:
                                        enemy_alliance_data = await enemy_alliance_response.json(content_type="text/plain")
                                        enemy_alliance_name = enemy_alliance_data.get("Name", "Unknown")
                   
                                        our_score = await db_operations.get_score(alliance_name)
                                        our_score_formatted = utility_operations.format_score(our_score)
                                        their_score = await db_operations.get_score(enemy_alliance_name)
                                        their_score_formatted = utility_operations.format_score(their_score)

                                        war_start_time = db_operations.get_war_start_time(alliance_name)

                                         # get time until 3 day end mark
                                        if war_start_time != "*not tracked*":
                                           current_time = datetime.now()
                                           three_day_mark = war_start_time + timedelta(days=3)
                                           max_duration_left = three_day_mark - current_time
                                                   
                                           # Format max duration left as HH:MM:SS
                                           max_duration_hours = max_duration_left.total_seconds() // 3600
                                           max_duration_minutes = (max_duration_left.total_seconds() % 3600) // 60
                                           max_duration_seconds = max_duration_left.total_seconds() % 60
                                           max_duration_str = f"{int(max_duration_hours)}:{int(max_duration_minutes):02}:{int(max_duration_seconds):02}"
   
                      
                                           # Calculate remaining time if available
                                        #    fifteen_hour_mark = war_start_time + timedelta(hours=14) + timedelta(minutes=10)
                                                       
                                                       # Calculate remaining time based on the score
                                           remaining_time = db_operations.calculate_remaining_time(our_score, their_score, war_start_time)
                                        #    if remainingTime == "no points yet":
                                        #            # Set remainingTime to the 15-hour mark if no points yet
                                        #            remainingTime = fifteen_hour_mark.timestamp()
                                        #    else:
                                        #        # Convert remainingTime to a timedelta
                                        #        remaining_time_delta = timedelta(seconds=remainingTime)
                                        #        calculated_end_time = current_time + remaining_time_delta
                                                       
                                        #        # Determine the appropriate end time
                                        #    if current_time < fifteen_hour_mark:
                                        #            remainingTime = fifteen_hour_mark.timestamp()
                                        #    else:
                                        #        remainingTime = calculated_end_time.timestamp()
                                                       
                                        #    # Ensure remainingTime is an integer Unix timestamp
                                        #    remaining_time = int(remainingTime)
                                        else:
                                            remaining_time = 1000000000
                                            max_duration_str = "*not tracked*"
                   
                                       # Construct embed with scores, progress bar, and remaining time
                                        embed = discord.Embed(
                                           title=f"{alliance_name} vs {enemy_alliance_name}",
                                           color=discord.Color.red(),
                                        )
                   
                                        embed.add_field(name="", value=f"{our_score_formatted} <:Warpoints:1206215489349619722>    :    {their_score_formatted} <:Warpoints:1206215489349619722>", inline=False)
                                        embed.add_field(name="Earliest KO", value=f"<t:{remaining_time}:R>", inline=False)
                                        embed.add_field(name="Time left", value=max_duration_str, inline=False)
                   
                                        await interaction.response.send_message(embed=embed)
                                   else:
                                        await interaction.response.send_message(f"Failed to fetch data for enemy alliance - Status Code: {enemy_alliance_response.status}")
                     else:
                         await interaction.response.send_message(f"Alliance {alliance_name} is not currently in a war.")
                 else:
                     await interaction.response.send_message(f"Failed to fetch data for alliance {alliance_name} - Status Code: {response.status}")
         
    except json.JSONDecodeError as e:
        if "Expecting value: line 1 column 1 (char 0)" in str(e):
            await interaction.response.send_message("You mistyped the name, this alliance doesn't exist or I don't track the score of this alliance.")
            # Handle the error, for example, by setting a default value
        else:
            # Print the exception message if it's a different JSONDecodeError
            await interaction.response.send_message(f"Unexpected JSONDecodeError: {e}")
            # Re-raise the exception
            raise

    except AttributeError as e:
        if "'NoneType' object has no attribute 'get'" in str(e):
            await interaction.response.send_message("You mistyped the name, this alliance doesn't exist or I don't track the score of this alliance.")
            # Handle the error, for example, by setting a default value
        else:
            # Print the exception message if it's a different AttributeError
            await interaction.response.send_message(f"Unexpected AttributeError: {e}")
            # Re-raise the exception
            raise
























@tasks.loop(minutes=1)
async def check_war_status():
    global online_players
    global war_ready
    message_id = await utility_operations.loadJson(PATH + "message_id_overview.json")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.galaxylifegame.net/Alliances/get?name={utility_operations.replace_spaces(ALLIANCE_NAME)}") as response:

                     if response.status == 200:
                         alliance_data = await response.json(content_type="text/plain")
                         in_war = alliance_data.get("InWar", False)
             
                         guild = bot.get_guild(GUILD_ID)
                         if guild:
                             channel = guild.get_channel(CHANNEL_ID)
                             if channel:
                                 if in_war:
                                     global sum_for_war
                                     global sum_against_war
                                     sum_for_war = 0
                                     sum_against_war = 0

                                     enemy_alliance_id = alliance_data.get("OpponentAllianceId", "Unknown")  # Get the name of the enemy alliance
             
                                     # Fetch enemy alliance details using the name to get the info
                                     async with aiohttp.ClientSession() as session:
                                            async with session.get(f"https://api.galaxylifegame.net/Alliances/get?name={utility_operations.replace_spaces(enemy_alliance_id)}") as enemy_alliance_response:
                                                if enemy_alliance_response.status == 200:
                                                    try:
                                                        enemy_alliance_data = await enemy_alliance_response.json(content_type="text/plain")
                                                        enemy_alliance_name = enemy_alliance_data.get("Name", "Unknown")
                                                        wins = enemy_alliance_data.get("WarsWon", 0)
                                                        losses = enemy_alliance_data.get("WarsLost", 0)
                                                        winrate = wins / (wins + losses) if wins + losses > 0 else 0
                        
                                                    except json.JSONDecodeError as json_error:
                                                        print(f"Error decoding JSON for enemy alliance: {json_error}")
                                                        enemy_alliance_name = "Unknown"
                                                else:
                                                    print(f"Failed to fetch enemy alliance data - Status Code: {enemy_alliance_response.status}")
                                                    enemy_alliance_name = "Unknown"
                        
                                                # Load war_info.json
                                                war_info = await utility_operations.loadJson(PATH + WAR_INFO)
                                                if war_info:
                                                    # Set regenTime to the global regentime variable
                                                    regenTime = regentime
                        
                                                    total_planets_count = 0
                                                    discovered_planets_count = 0
                                                    destroyed_planets_count = 0
                        
                                                    current_time = datetime.now()
                                                    regen_delta = timedelta(hours=regenTime)
                        
                                                    for member_name, member_info in war_info["members"].items():
                                                        for colony, colony_info in member_info.items():
                                                            total_planets_count += 1  # Count every colony for the total
                                                            if colony_info[0] != "0":
                                                                colony_time = datetime.strptime(colony_info[0], "%Y-%m-%d %H:%M:%S")
                                                                if current_time - colony_time < regen_delta:
                                                                    destroyed_planets_count += 1  # Count every colony for destroyed planets
                                                            if colony != "C0":
                                                               discovered_planets_count += 1  # Only count non-C0 colonies for discovered planets
                        
                                                                                                        # Calculate scores
                                                    our_score = await db_operations.get_score(ALLIANCE_NAME)
                                                    our_score_formatted = utility_operations.format_score(our_score)
                                                    their_score = await db_operations.get_score(enemy_alliance_name)
                                                    their_score_formatted = utility_operations.format_score(their_score)

                                                    # initiate war start
                                                    war_start_time = db_operations.get_war_start_time(ALLIANCE_NAME)

                                                    if war_start_time != "*not tracked*":
                                                          # get time until 3 day end mark
                                                          three_day_mark = war_start_time + timedelta(days=3)
                                                          max_duration_left = three_day_mark - current_time
                                                      
                                                          # Format max duration left as HH:MM:SS
                                                          max_duration_hours = max_duration_left.total_seconds() // 3600
                                                          max_duration_minutes = (max_duration_left.total_seconds() % 3600) // 60
                                                          max_duration_seconds = max_duration_left.total_seconds() % 60
                                                          max_duration_str = f"{int(max_duration_hours)}:{int(max_duration_minutes):02}:{int(max_duration_seconds):02}"
      
                                                          fifteen_hour_mark = war_start_time + timedelta(hours=14) + timedelta(minutes=10)
                                                          
                                                          # Calculate remaining time based on the score
                                                          remainingTime = db_operations.calculate_remaining_time(our_score, their_score, war_start_time)
                                                        #   if remainingTime == "no points yet":
                                                        #       # Set remainingTime to the 15-hour mark if no points yet
                                                        #       remainingTime = fifteen_hour_mark.timestamp()
                                                        #   else:
                                                        #       # Convert remainingTime to a timedelta
                                                        #       remaining_time_delta = timedelta(seconds=remainingTime)
                                                        #       calculated_end_time = current_time + remaining_time_delta
                                                          
                                                        #       # Determine the appropriate end time
                                                        #       if current_time < fifteen_hour_mark:
                                                        #           remainingTime = fifteen_hour_mark.timestamp()
                                                        #       else:
                                                        #           remainingTime = calculated_end_time.timestamp()
                                                          
                                                          # Ensure remainingTime is an integer Unix timestamp
                                                        #   remaining_time = int(remainingTime)
                                                    else:
                                                        remaining_time = 1000000000
                                                        max_duration_str = "*not tracked*"
                        
                                                    # Calculate progress bar
                                                    max_length = 14
                                                    if their_score > 0:
                                                        our_progress = int((our_score / (our_score + their_score)) * max_length)
                                                    else:
                                                        our_progress = max_length  # Fill up the bar entirely if their_score is 0
                                                    their_progress = max_length - our_progress
                                                    progress_bar = "▰" * our_progress + "▱" * their_progress
                        
                                                    # Construct embed with progress bar, scores, and enemy logo
                                                    embed = discord.Embed(
                                                        title=f"{enemy_alliance_name}",
                                                        description=progress_bar,
                                                        color=discord.Color.red(),
                                                        timestamp=datetime.now(timezone.utc)
                                                    )
                        
                                                    # Fetch enemy alliance logo URL based on emblem data
                                                    emblem_data = enemy_alliance_data.get("Emblem", {})
                                                    shape = emblem_data.get("Shape", 0)
                                                    pattern = emblem_data.get("Pattern", 0)
                                                    icon = emblem_data.get("Icon", 0)
                                                    enemy_logo_url = f"https://cdn.galaxylifegame.net/content/img/alliance_flag/AllianceLogos/flag_{shape}_{pattern}_{icon}.png"
                                                    embed.set_thumbnail(url=enemy_logo_url)
                        
                                                    # Add fields to embed
                                                    # invisible character to create space between fields \u1CBC\u1CBC
                                                    embed.add_field(name="", value=f"**{str(our_score_formatted)}** <:Warpoints:1206215489349619722> VS **{str(their_score_formatted)}** <:Warpoints:1206215489349619722>", inline=True)
                                                    embed.add_field(name="", value=f":stopwatch: KO: <t:{remaining_time}:R> \n:chart_with_upwards_trend: Winrate: {winrate:.2%} \n:ringed_planet: Discovered Colonies: {discovered_planets_count} \n:boom: Destroyed Planets: {destroyed_planets_count}/{total_planets_count}", inline=False)
                                                    embed.add_field(name="", value="-----------------------------------", inline=True)
                                                    
                                                    if online_players == {}:
                                                        embed.add_field(name=":no_entry: Online players", value="Nobody is online...", inline=False)
                                                    else:
                                                        text = ""
                                                        for player, timestamp in online_players.items():
                                                            if datetime.now() - timestamp < timedelta(minutes=15):
                                                                text += f"{player}\n"
                                                        if text == "":
                                                            text = "Nobody is online..."
                                                        embed.add_field(name=":no_entry: Online players", value=text, inline=False)
                                                    
                                                    embed.add_field(name=":hourglass: Time left", value=f"{max_duration_str}", inline=False)
                                                    embed.add_field(name="", value="-----------------------------------", inline=True)

                                                    upcoming_bases = await format_top_5_least_downtime()
                                                    embed.add_field(name="Upcoming bases", value=f"{upcoming_bases}", inline=False)
                        
                                                    # Give the ScoreDropDownView the members list
                                                    members = list(db_operations.get_all_members_GE2())
                                                    dropdown_view = dropdown.ScoreDropDownView(members)
                                                    
                                                    # Update or send the embed
                                                    if message_id["id"] != 0:
                                                        message = await channel.fetch_message(message_id["id"])
                                                        await message.edit(embed=embed,view=dropdown_view)
                                                        await message.clear_reaction("✅")
                                                        await message.clear_reaction("<:red_cross:1072245059577196554>")
                                                    else:
                                                        message = await channel.send(embed=embed, view=dropdown_view)
                                                        message_id["id"] = message.id
                                                        await utility_operations.saveJson(PATH + "message_id_overview.json", message_id)
                        
                                                else:
                                                    print(f"Failed to load war_info.json")
                                 else:
                                     war_ready = False
                                     embed = discord.Embed(
                                                        title=f"We are not at war",
                                                        color=discord.Color.red(),
                                                        timestamp=datetime.now(timezone.utc)
                                                    )
                                     embed.add_field(name="Who is ready for war?", value=":white_check_mark: / <:red_cross:1072245059577196554> ")
                                 
                                     if message_id["id"] != 0:
                                         message = await channel.fetch_message(message_id["id"])
                                         await message.edit(embed=embed, view=None)
                                         await message.add_reaction("✅")
                                         await message.add_reaction("<:red_cross:1072245059577196554>")
                                     else:
                                        message = await channel.send(embed=embed, view=None)
                                        message_id["id"] = message.id
                                        await utility_operations.saveJson(PATH + "message_id_overview.json", message_id)
                     else:
                         print(f"Failed to fetch data for alliance: {ALLIANCE_NAME} - Status Code: {response.status}")
    except Exception as e:
        if e == discord.errors.NotFound:
            print("Message was deleted, regenarating it...")
        else:
            print(f"Error checking war status: {e}")

# @bot.event
# async def on_reaction_add(reaction, user):
#     guild = bot.get_guild(GUILD_ID)
#     if guild:
#         channel = guild.get_channel(CHANNEL_ID_WAR_CHAT)
#         if channel:
#             global sum_for_war
#             global sum_against_war
#             if reaction.emoji == "✅":
#                 sum_for_war += 1
#             elif reaction.emoji == "<:red_cross:1072245059577196554>":
#                 sum_against_war += 1

#             if (sum_for_war-sum_against_war) >= 4:
#                 await channel.send("<@&1072196473334280283>, the members have voted and are ready for war!")

















async def fetch_embed_coords(name, Avatar):
    # Initialize the embed
    embed_coords = discord.Embed(
        title=f"Colony Data of {name}",
        color=discord.Color.from_rgb(255, 191, 0)
    )

    try:
        # Fetch player data to get the player ID
        async with aiohttp.ClientSession() as session:
            async with session.get(API_NAME + name) as response:
                if response.status != 200:
                    return discord.Embed(
                        title=f"Error fetching data for player: {name}",
                        description="The player could not be found or the server returned an error.",
                        color=discord.Color.red()
                    )

                player_info = await response.json(content_type='text/plain')
                player_id = player_info.get("Id")

                if not player_id:
                    return discord.Embed(
                        title=f"Error fetching data for player: {name}",
                        description="Player ID could not be retrieved.",
                        color=discord.Color.red()
                    )

                # Fetch the main planet data
                main_planet = db_Alex.get_player(player_id)
                if main_planet:
                    embed_coords.add_field(
                        name="Main Planet",
                         value=f"SB{main_planet.get('MB_lvl', '???')} - {main_planet.get('MB_sys_name', '')} 🌍",
                        inline=False
                    )
                else:
                    embed_coords.add_field(name="Main Planet", value="???", inline=False)

                # Determine the number of colonies from player_info
                player_planets = player_info.get("Planets", [])
                total_colonies = min(len(player_planets), 11)  # Maximum 11 colonies

                # Fetch all colonies
                colonies = db_Alex.get_colonies(player_id)

                if colonies:
                    # Sort colonies by their `number` field
                    colonies.sort(key=lambda x: x.get("number", 0))

                    for colony in colonies:
                        colony_number = colony.get("number", "???")
                        colo_system = colony.get("colo_sys_name",'unknown system')
                        level = colony.get("colo_lvl", "???")
                        coord = colony.get("colo_coord", {})
                        coord_x = coord.get("x", "???")
                        coord_y = coord.get("y", "???")
                        
                        if (coord_x == -1 and coord_y == -1): 
                            coordinates = "???"
                        else:
                            coordinates = f"{coord_x}, {coord_y}"

                        embed_coords.add_field(
                            name=f"C{colony_number} - {colo_system}",
                            value=f"SB{level} - :ringed_planet: {coordinates}",
                            inline=False
                        )

                # Ensure placeholders for any missing colonies up to the total number of colonies
                for i in range(1, total_colonies):
                    if not any(colony.get("number") == i for colony in colonies):
                        embed_coords.add_field(
                            name=f"C{i}",
                            value="SB??? - :ringed_planet: ???",
                            inline=False
                        )

    except Exception as e:
        embed_coords = discord.Embed(
            title=f"Error fetching colony data for {name}",
            description=f"An unexpected error occurred: {str(e)}",
            color=discord.Color.red()
        )

    embed_coords.set_thumbnail(url=Avatar)
    return embed_coords







async def fetch_embed_status(name, Avatar):
          global embed_status
          # 3rd page
          embed_status = discord.Embed(title=f"Status of {name}", color=discord.Color.from_rgb(255, 191, 0))
          player_status = db_operations.get_afk(name)
          last_update = ''
          warpoints = 0
          alliance_id = ''
          alliance_name = ''
          now = datetime.now()
          if player_status:
              last_update = player_status['last_update']
            #   print(last_update)
              last_update = (now - last_update).days
            #   print(last_update)
      
              if last_update <= 0:
                  last_update = "Less than a day ago"
              elif last_update == 1:
                  last_update = "1 day ago"
              else:
                  last_update = f"{last_update} days ago"
      
              warpoints = player_status['warpoints']
              async with aiohttp.ClientSession() as session:
                  async with session.get(API_NAME + name) as response:
                      if response.status == 200:
                          player_data = await response.json(content_type="text/plain")
                          alliance_id = player_data.get("AllianceId", "")
                          if alliance_id != None and alliance_id != "":
                              async with session.get(API_URL + utility_operations.replace_spaces(alliance_id)) as alliance_response:
                                  if alliance_response.status == 200:
                                      alliance_data = await alliance_response.json(content_type="text/plain")
                                      alliance_name = alliance_data.get("Name", "")
                                  else:
                                      print(f"Failed to fetch data for player: {name} - Status Code: {response.status}")
                          else:
                              alliance_name = "User is not in an alliance"
                      else:
                          print(f"Page 3: Failed to fetch data for player: {name} - Status Code: {response.status}")
          else:
              last_update = "*This player is not being tracked...*"
              warpoints = "*This player is not being tracked...*"
              async with aiohttp.ClientSession() as session:
                  async with session.get(API_NAME + name) as response:
                      if response.status == 200:
                          player_data = await response.json(content_type="text/plain")
                          alliance_id = player_data.get("AllianceId", "")
                          if alliance_id != None and alliance_id != "":
                              async with session.get(API_URL + utility_operations.replace_spaces(alliance_id)) as alliance_response:
                                  if alliance_response.status == 200:
                                      alliance_data = await alliance_response.json(content_type="text/plain")
                                      alliance_name = alliance_data.get("Name", "")
                                  else:
                                      print(f"Failed to fetch data for player: {name} - Status Code: {response.status}")
                          else:
                              alliance_name = "User is not in an alliance"
                      else:
                          print(f"Page 3: Failed to fetch data for player: {name} - Status Code: {response.status}")
              
          embed_status.add_field(name="Alliance", value=alliance_name, inline=False)
          if type(warpoints) == int:
            embed_status.add_field(name="Warpoints", value=f"{utility_operations.format_number(warpoints)} <:Warpoints:1206215489349619722>", inline=False)
          else:
            embed_status.add_field(name="Warpoints", value=warpoints, inline=False)
          embed_status.add_field(name="Last played", value=last_update, inline=False)
          embed_status.set_thumbnail(url=Avatar)

          return embed_status








# async def fetch_embed_alliance(alliance_name):
#           global embed_alliance
#           # 4th page
#           colony_text = ''
#           alliance_data_coords = ''
#           if alliance_name != None:
#               async with aiohttp.ClientSession() as session:
#                   async with session.get(API_URL + utility_operations.replace_spaces(alliance_name)) as alliance_coords:
#                       if alliance_coords.status == 200:
#                           alliance_data_coords = await alliance_coords.json(content_type="text/plain")
#                           members = alliance_data_coords.get("Members", [])
#                           if len(members) < 25:
#                               embed_alliance = discord.Embed(title=f"Coords of {alliance_name}", color=discord.Color.from_rgb(138, 43, 226))
#                               for member in members:
#                                   member_name = member["Name"]
#                                   member_data = db_operations.find_player(member_name)
#                                   colony_text = ""
#                                   if member_data:
#                                       for colony in range(1, 12):
#                                           colony_num = f"C{colony}"
#                                           if colony_num in member_data and colony_num != []:
#                                               colony_data = member_data[colony_num]
#                                               if colony_data:
#                                                   coordinates = colony_data[1]
#                                                   SB_level = colony_data[2]
#                                                   colony_text += f"{colony_num} / {coordinates} / SB{SB_level}\n"
#                                   embed_alliance.add_field(name=member_name, value=colony_text, inline=True)
#                           else:
#                                    columns = 3  # Number of columns
#                                    embed_alliance = discord.Embed(title=f"Coords of {alliance_name}", color=discord.Color.from_rgb(138, 43, 226))
                                   
#                                    # Group members into fields
#                                    fields = [""] * columns
#                                    for i, member in enumerate(members):
#                                        field_index = i % columns
#                                        member_name = member["Name"]
#                                        member_data = db_operations.find_player(member_name)
#                                        colony_text = ""
#                                        if member_data:
#                                            for colony in range(1, 12):
#                                                colony_num = f"C{colony}"
#                                                if colony_num in member_data and member_data[colony_num] != []:
#                                                    colony_data = member_data[colony_num]
#                                                    if colony_data:
#                                                        coordinates = colony_data[1]
#                                                        SB_level = colony_data[2]
#                                                        colony_text += f"{colony_num} / {coordinates} / {SB_level}\n"
                                       
#                                        fields[field_index] += f"**{member_name}**\n{colony_text}\n"
                                   
#                                    # Add fields to embed
#                                    for i, field in enumerate(fields):
#                                        if field.strip():  # Only add non-empty fields
#                                            embed_alliance.add_field(name="", value=field, inline=True)
                                 
#                       else:
#                           print(f"Page 4: Failed to fetch data for alliance: {alliance_name} - Status Code: {alliance_coords.status}")
#           else:
#                 embed_alliance = discord.Embed(title=f"This user is not in an alliance", color=discord.Color.from_rgb(138, 43, 226))

#           return embed_alliance




async def fetch_embed_alliance_status(alliance_name):
    print(alliance_name)
    if alliance_name == None:
        return discord.Embed(
            title="Alliance Status",
            description="This user is not in an alliance.",
            color=discord.Color.red()
        )
    else:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}{alliance_name}") as alliance_response:
                    if alliance_response.status != 200:
                        return discord.Embed(
                            title=f"Error fetching data for alliance: {alliance_name}",
                            description="The alliance could not be found or the server returned an error.",
                            color=discord.Color.red()
                        )
    
                    alliance_info = await alliance_response.json(content_type="text/plain")
    
                    # Create the embed for the alliance status
                    name = alliance_info.get("Name", alliance_name)
                    embed_alliance_status = discord.Embed(
                        title=f"Alliance Status: {name}",
                        color=discord.Color.from_rgb(255, 191, 0)
                    )
                    # Fetch alliance logo
                    emblem_data = alliance_info.get("Emblem", {})
                    shape = emblem_data.get("Shape", 0)
                    pattern = emblem_data.get("Pattern", 0)
                    icon = emblem_data.get("Icon", 0)
                    alliance_logo_url = f"https://cdn.galaxylifegame.net/content/img/alliance_flag/AllianceLogos/flag_{shape}_{pattern}_{icon}.png"
                    embed_alliance_status.set_thumbnail(url=alliance_logo_url)
    
                    members = alliance_info.get("Members", [])
    
                    if not members:
                        embed_alliance_status.description = "This alliance has no members or the data is unavailable."
                        return embed_alliance_status
    
                    # Collect member data for sorting
                    member_data = []
                    for member in members:
                        member_name = member['Name']
                        player_status = db_operations.get_afk(member_name)
                        # Default status if player isn't being tracked
                        last_update = "Not tracked"
                        warpoints = "Not tracked"
                        days_since_update = float('inf')  # Default to infinity for sorting if not tracked
    
                        if player_status != None:
                            now = datetime.now()
                            last_update_date = player_status['last_update']

                            days_since_update = (now - last_update_date).days
                            if days_since_update <= 0:
                                last_update = "Less than a day ago"
                            elif days_since_update == 1:
                                last_update = "1 day ago"
                            else:
                                last_update = f"{days_since_update} days ago"
                            warpoints = player_status['warpoints']
                        member_data.append({
                            "name": member_name,
                            "warpoints": warpoints,
                            "last_update": last_update,
                            "days_since_update": days_since_update
                        })
    
                    # Sort members by days_since_update (ascending)
                    member_data.sort(key=lambda x: x["days_since_update"])
                    # Group members in chunks of 5 for embed fields
                    field_content = []
                    for idx, member in enumerate(member_data):
                        member_name = member['name']
                        warpoints = member['warpoints']
                        last_update = member['last_update']
    

                        # Format each member's data
                        field_content.append(f"**{member_name}**: {utility_operations.format_number(warpoints)} <:Warpoints:1206215489349619722>, ⏱️: {last_update}")
    
                        # Add a field every 5 members or if it's the last member
                        if len(field_content) == 5 or idx == len(member_data) - 1:
                            embed_alliance_status.add_field(
                                name=f"---------------------------------------------------",
                                value="\n".join(field_content),
                                inline=False
                            )
                            field_content = []
    
                    embed_alliance_status.set_footer(text=f"Total members: {len(members)} - updated every 6h")
    
        except Exception as e:
            embed_alliance_status = discord.Embed(
                title=f"Error fetching alliance status: {alliance_name}",
                description=f"An unexpected error occurred: {str(e)}",
                color=discord.Color.red()
            )
    
        return embed_alliance_status










@bot.tree.command(name="player_profile", description="Get the profile of a player")
@app_commands.autocomplete(name=player_suggestion)
@app_commands.describe(name="Player name")
async def player_profile(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    await asyncio.sleep(0.3)
    try:
          # 1st page
          player_id = 0
          player_game_name = ''
          Avatar = ""
          attacks = 0
          coloniesMoved = 0
          nukesUsed = 0
          coinsSpent = 0
          buildingsDestroyed = 0
          xpFromAttacks = 0
          alliance_name = ""
          async with aiohttp.ClientSession() as session:
              async with session.get(API_NAME + name) as response:
                  if response.status == 200:
                      player_data = await response.json(content_type="text/plain")
                      player_id = player_data.get("Id", 0)
                      player_game_name = player_data.get("Name","")
                      alliance_name = player_data.get("AllianceId", "User is not in an alliance")
                      Avatar = player_data.get("Avatar", "")
                      async with session.get(API_STATS + player_id) as personal_response:
                              if personal_response.status == 200:
                                  player_info = await personal_response.json(content_type="text/plain")
                                  attacks = player_info.get("PlayersAttacked", 0)
                                  coloniesMoved = player_info.get("ColoniesMoved", 0)
                                  nukesUsed = player_info.get("NukesUsed", 0)
                                  coinsSpent = player_info.get("CoinsSpent", 0)
                                  buildingsDestroyed = player_info.get("BuildingsDestroyed", 0)
                                  xpFromAttacks = player_info.get("ScoreFromAttacks", 0)
                              else:
                                  await interaction.followup.send(f"Failed to fetch data for player: {name} - Status Code: {response.status}")
          
                  else:
                      await interaction.followup.send(f"Page 1: Failed to fetch data for player: {name} - Status Code: {response.status}")
          
      
          embed_profile = discord.Embed(title=f"Profile of {player_game_name}", color=discord.Color.from_rgb(255, 191, 0))
          embed_profile.set_thumbnail(url=Avatar)
          embed_profile.add_field(name="Players attacked", value=f"<:colossus:1198215925283946566> {utility_operations.format_number(attacks)}", inline=False)
          embed_profile.add_field(name="Colonies moved", value=f":ringed_planet: {utility_operations.format_number(coloniesMoved)}", inline=True)
          embed_profile.add_field(name="Nukes used", value=f"<:nuke:1198215992183115786> {utility_operations.format_number(nukesUsed)}", inline=False)
          embed_profile.add_field(name="Coins spent", value=f"<:coins:1198216072055238706> {utility_operations.format_number(coinsSpent)}", inline=True)
          embed_profile.add_field(name="Buildings destroyed", value=f"<:compact_house:1257676668948971641> {utility_operations.format_number(buildingsDestroyed)}", inline=False)
          embed_profile.add_field(name="XP from attacks", value=f"<:Experience:1257675745514225666> {utility_operations.format_number(xpFromAttacks)}", inline=True)
      
          embed_coords, embed_status, embed_alliance_status = await asyncio.gather(
                fetch_embed_coords(name, Avatar),
                fetch_embed_status(player_game_name, Avatar),
                fetch_embed_alliance_status(alliance_name)
          )  
          pages = [embed_profile, embed_coords, embed_status, embed_alliance_status]
      
          await interaction.followup.send(embed=pages[0], view=button.buttonMenu(pages, player_id))
        
    except json.JSONDecodeError as e:
        if "Expecting value: line 1 column 1 (char 0)" in str(e):
            await interaction.followup.send("You mistyped the name or this player doesn't exist.")
            # Handle the error, for example, by setting a default value
        else:
            # Print the exception message if it's a different JSONDecodeError
            await interaction.followup.send(f"Unexpected JSONDecodeError: {e}")
            # Re-raise the exception
            raise
    except Exception as e:
          await interaction.followup.send(f"Error fetching player profile: {e}")



















@tasks.loop(minutes=3)
async def info():
    global split_needed
    global number_of_splits
    print(split_needed, number_of_splits)
    current_time =''
    remaining_time = ''
    try:
        GE2_data = db_operations.find_opponent_GE2()
        if GE2_data:
            enemy = GE2_data["OpponentAllianceId"]
            if enemy != "":
                async with aiohttp.ClientSession() as session:
                    async with session.get(API_URL + utility_operations.replace_spaces(enemy)) as response:
                        if response.status == 200:
                            enemy_data = await response.json(content_type="text/plain")
                            enemy_name = enemy_data.get("Name", "Unknown")
                            enemy_members = enemy_data.get("Members", [])
                            
                            if not split_needed:
                                columns = 3  # Number of columns for the embed
                                embed_alliance = discord.Embed(title=f"Coordinates of {enemy_name}", color=discord.Color.from_rgb(255, 191, 0),timestamp=datetime.now(timezone.utc))
                                fields = [""] * columns

                                for idx, member in enumerate(enemy_members):
                                    member_name = member['Name']
                                    member_id = member['Id']
                                    colonies = db_Alex.get_colonies(member_id)
                                    found_colonies = db_Alex.found_colonies(member_id)

                                    colony_info = f"**{member_name}**\n"
                                    main_planet = db_Alex.get_player(member_id)
                                    current_time = datetime.now()
                                    time_difference = main_planet["MB_refresh_time"] - current_time - timedelta(hours=2)
                                    hours, remainder = divmod(time_difference.total_seconds(), 3600)
                                    minutes, _ = divmod(remainder, 60)
                                    remaining_time = f"{int(hours)}h{int(minutes)}m"

                                    if main_planet['MB_status'] == "Up":
                                        colony_info += f":white_check_mark: main SB{main_planet['MB_lvl']}\n"
                                    else: 
                                        colony_info += f":octagonal_sign: main SB{main_planet['MB_lvl']} - {remaining_time}\n"

                                    for colony in colonies:
                                        coordinates = f"{colony['colo_coord']['x']},{colony['colo_coord']['y']}"
                                        if coordinates != "-1,-1":
                                             colony_number = f"C{colony['number']}"
                                             SB_level = f"SB{colony['colo_lvl']}"

                                             current_time = datetime.now()
                                             time_difference = colony["colo_refresh_time"] - current_time - timedelta(hours=2)
                                             hours, remainder = divmod(time_difference.total_seconds(), 3600)
                                             minutes, _ = divmod(remainder, 60)
                                             remaining_time = f"{int(hours)}h{int(minutes)}m"

                                             if colony['colo_status'] == "Up":
                                                 colony_info += f":white_check_mark: {colony_number} - {SB_level} - {coordinates}\n"
                                             elif colony['colo_status'] == "Down":
                                                 colony_info += f":octagonal_sign: {colony_number} - {SB_level} - {coordinates} - {remaining_time}\n"
                                             else:
                                                 colony_info += f":warning: {colony_number} - {SB_level} - {coordinates}\n"
                                    
                                    for found_colony in found_colonies:
                                        coordinates = f"{found_colony['X']},{found_colony['Y']}"
                                        colony_info += f":grey_question: {coordinates}\n"

                                    field_index = idx % columns
                                    fields[field_index] += f"{colony_info}\n"
                                
                                for i, field in enumerate(fields):
                                    if field.strip():  # Only add non-empty fields
                                        embed_alliance.add_field(name="", value=field, inline=True)
                                
                                embed_alliance.set_footer(text="Last updated")
                                
                                members = list(db_operations.get_all_members_GE2())
                                dropdown_view = dropdown.ScoreDropDownView(members)
                                guild = bot.get_guild(GUILD_ID)
                                if guild:
                                    channel = guild.get_channel(CHANNEL_ID_COORDS)
                                    if channel:
                                        message_id = await utility_operations.loadJson(PATH + "coords_message.json")
                                        if message_id["id"] != 0:
                                            message = await channel.fetch_message(message_id["id"])
                                            await message.edit(embed=embed_alliance, view=dropdown_view)
                                            print('single message edited')
                                        else:
                                            message = await channel.send(embed=embed_alliance, view=dropdown_view)
                                            print('single message sent')
                                            message_id["id"] = message.id
                                            await utility_operations.saveJson(PATH + "coords_message.json", message_id)
                            else:
                                # Split the members into two groups
                                mid_index = len(enemy_members) // number_of_splits
                                groups = []
                                start_index = 0
                                
                                for i in range(1, number_of_splits + 1):
                                    if i == number_of_splits:  # Ensure the last group gets any remaining members
                                        groups.append(enemy_members[start_index:])
                                    else:
                                        end_index = start_index + mid_index
                                        groups.append(enemy_members[start_index:end_index])
                                        start_index = end_index
                                
                                
                                for group_index, group in enumerate(groups):
                                    columns = 3  # Number of columns for the embed
                                    embed_alliance = discord.Embed(title=f"Coordinates of {enemy_name}", color=discord.Color.from_rgb(255, 191, 0), timestamp=datetime.now(timezone.utc))
                                    fields = [""] * columns

                                    for idx, member in enumerate(group):
                                        member_name = member['Name']
                                        member_id = member['Id']
                                        colonies = db_Alex.get_colonies(member_id)
                                        found_colonies = db_Alex.found_colonies(member_id)

                                        colony_info = f"**{member_name}**\n"
                                        main_planet = db_Alex.get_player(member_id)
                                        current_time = datetime.now()
                                        time_difference = main_planet["MB_refresh_time"] - current_time - timedelta(hours=2)
                                        hours, remainder = divmod(time_difference.total_seconds(), 3600)
                                        minutes, _ = divmod(remainder, 60)
                                        remaining_time = f"{int(hours)}h{int(minutes)}m"

                                        if main_planet['MB_status'] == "Up":
                                            colony_info += f":white_check_mark: main SB{main_planet['MB_lvl']}\n"
                                        else: 
                                            colony_info += f":octagonal_sign: main SB{main_planet['MB_lvl']} - {remaining_time}\n"

                                        for colony in colonies:
                                            coordinates = f"{colony['colo_coord']['x']},{colony['colo_coord']['y']}"
                                            if coordinates != "-1,-1":
                                                colony_number = f"C{colony['number']}"
                                                SB_level = f"SB{colony['colo_lvl']}"

                                                current_time = datetime.now()
                                                time_difference = colony["colo_refresh_time"] - current_time - timedelta(hours=2)
                                                hours, remainder = divmod(time_difference.total_seconds(), 3600)
                                                minutes, _ = divmod(remainder, 60)
                                                remaining_time = f"{int(hours)}h{int(minutes)}m"
                                                
                                                if colony['colo_status'] == "Up":
                                                    colony_info += f":white_check_mark: {colony_number} - {SB_level} - {coordinates}\n"
                                                elif colony['colo_status'] == "Down":
                                                    colony_info += f":octagonal_sign: {colony_number} - {SB_level} - {coordinates} - {remaining_time}\n"
                                                else:
                                                    colony_info += f":warning: {colony_number} - {SB_level} - {coordinates}\n"
                                        
                                        for found_colony in found_colonies:
                                            coordinates = f"{found_colony['X']},{found_colony['Y']}"
                                            colony_info += f":grey_question: {coordinates}\n"

                                        field_index = idx % columns
                                        fields[field_index] += f"{colony_info}\n"
                                    
                                    for i, field in enumerate(fields):
                                        if field.strip():  # Only add non-empty fields
                                            embed_alliance.add_field(name="", value=field, inline=True)
                                    
                                    embed_alliance.set_footer(text="Last updated")
                                    
                                    members = list(db_operations.get_all_members_GE2())
                                    dropdown_view = dropdown.ScoreDropDownView(members)
                                    # creating embed
                                    guild = bot.get_guild(GUILD_ID)
                                    if guild:
                                        channel = guild.get_channel(CHANNEL_ID_COORDS)
                                        if channel:
                                            message_id_path = PATH + f"coords_message_group_{group_index + 1}.json"
                                            message_id = await utility_operations.loadJson(message_id_path)
                                            if message_id["id"] != 0:
                                                message = await channel.fetch_message(message_id["id"])
                                                if group_index == len(groups) - 1:
                                                    await message.edit(embed=embed_alliance, view=dropdown_view)
                                                    print(f'edited group {group_index} with drop')
                                                else:
                                                    await message.edit(embed=embed_alliance, view=None)
                                                    print(f'edited group {group_index}')
                                            else:
                                                message = ''
                                                if group_index == len(groups) - 1:
                                                    message = await channel.send(embed=embed_alliance, view=dropdown_view)
                                                    print(f'sent group {group_index} with drop')
                                                else:
                                                    message = await channel.send(embed=embed_alliance, view=None)
                                                    print(f'sent group {group_index}')
                                                message_id["id"] = message.id
                                                await utility_operations.saveJson(message_id_path, message_id)
                                
                                # deleting no war embed
                                message_id = await utility_operations.loadJson(PATH + "coords_message.json")
                                guild = bot.get_guild(GUILD_ID)
                                if guild:
                                    channel = guild.get_channel(CHANNEL_ID_COORDS)
                                    if channel:
                                        if message_id["id"] != 0:
                                            try:
                                                message_in_channel = await channel.fetch_message(message_id["id"])
                                                if message_in_channel:
                                                    await message_in_channel.delete()
                                                    print('deleted no war in groups')
                                                message_id["id"] = 0
                                            except Exception as e:
                                                message_id["id"] = 0
                                                print('no war is 0 from groups')
                                await utility_operations.saveJson(PATH + "coords_message.json", message_id)

            else:
                # creating embed
                number_of_splits = 1
                split_needed = False
                embed_alliance = discord.Embed(title=f"We are not at war", color=discord.Color.from_rgb(255, 191, 0))
                guild = bot.get_guild(GUILD_ID)
                if guild:
                    channel = guild.get_channel(CHANNEL_ID_COORDS)
                    if channel:
                        message_id = await utility_operations.loadJson(PATH + "coords_message.json")
                        if message_id["id"] != 0:
                            message = await channel.fetch_message(message_id["id"])
                            await message.edit(embed=embed_alliance, view=None)
                            print('no war edited')
                        else:
                            async for msg in channel.history(limit=20):
                                try:
                                    await msg.delete()
                                    print("cleared channel")
                                except Exception as e:
                                    print(f"couldn't delete: {e}")
                            message = await channel.send(embed=embed_alliance, view=None)
                            print('no war send')
                            message_id["id"] = message.id
                            await utility_operations.saveJson(PATH + "coords_message.json", message_id)
                        
                        # deleting other embeds (groups)
                        for i in range(1,7):
                                message = await utility_operations.loadJson(f"{PATH}coords_message_group_{i}.json")
                                guild = bot.get_guild(GUILD_ID)
                                if guild:
                                    channel = guild.get_channel(CHANNEL_ID_COORDS)
                                    if channel:
                                        message_id = message["id"]
                                        if message_id:
                                            try:
                                                message_in_channel = await channel.fetch_message(message_id)
                                                if message_in_channel:
                                                    await message_in_channel.delete()
                                                    print(f'deleted group {i} from no war')
                                                message["id"] = 0
                                            except Exception as e:
                                                message["id"] = 0
                                                print(f'exception group {i} from no war but is 0')
                                await utility_operations.saveJson(f"{PATH}coords_message_group_{i}.json", message)

    except Exception as e:
        if isinstance(e, discord.errors.NotFound):
            print("Message was deleted, regenerating it...")
            message_id = await utility_operations.loadJson(PATH + "coords_message.json")
            message_id['id'] = 0
            await utility_operations.saveJson(PATH + "coords_message.json", message_id)
            for i in range(1,17):
                message = await utility_operations.loadJson(f"{PATH}coords_message_group_{i}.json")
                message["id"] = 0
                message = await utility_operations.saveJson(f"{PATH}coords_message_group_{i}.json", message)


        elif isinstance(e, discord.errors.HTTPException) and "Must be 1024 or fewer in length" in str(e):
            print(f"Character limit reached of 1024")
            split_needed = True
            number_of_splits += 1
            
        elif isinstance(e, discord.errors.HTTPException) and "Embed size exceeds maximum size of 6000" in str(e):
            print(f"embed size of 6000 reached")
            split_needed = True
            number_of_splits += 1
        else:
            print(f"An unexpected error occurred in info: {e}")







bot.run(os.getenv('token'))