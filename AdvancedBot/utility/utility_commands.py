import json
import aiohttp
import os
from dotenv import load_dotenv
from datetime import datetime
import time
import pytz

load_dotenv()

PATH = os.getenv('path')
WAR_INFO = os.getenv('WAR_INFO')

class utilityOperations():
    def __init__(self):
        pass

    def replace_spaces(self,name : str) -> str:
        return name.replace(" ", "%20")

    def function_KO(self):
        x = -(19 * (x-1))^2.2 + 14
        return "KO"
    
    def get_regenTime(self,us,enemy):
          actualRegenTime = (3/us)*enemy
          if actualRegenTime < 3:
             actualRegenTime = 3
          elif actualRegenTime > 7:
             actualRegenTime = 7

          return actualRegenTime
    
    # def get_regenTimeEnemy(self,GEWPSum, enemyWPSum):
    #       #   regenTime = (3*enemyWPSum)/GEWPSum
    #       actualRegenTime = (3/enemyWPSum)*GEWPSum
    #       #   base_value = int(regenTime)
    #       #   border_for_rounding = base_value + 0.9
    #       #   if regenTime < border_for_rounding:
    #       #       actualRegenTime = base_value
    #       #   else:
    #       #        actualRegenTime = base_value + 1
    
    #       if actualRegenTime < 3:
    #           actualRegenTime = 3
    #       elif actualRegenTime > 7:
    #           actualRegenTime = 7
    #       return actualRegenTime

    async def loadJson(self,fileName):
        with open(fileName, 'r') as file:
            data = json.load(file)
        return data

    async def saveJson(self,fileName, data):
        with open(fileName, 'w') as file:
            json.dump(data, file, indent=4)

    async def get_sorted_players_by_sb_level(self, path):
         # Load the war_info JSON from the file
         with open(path, 'r') as file:
            war_info = json.load(file)
     
         # Function to get the SB level from the player's data
         def get_sb_level(player_data):
             # Assuming 'C0' contains the relevant SB level
             return int(player_data['C0'][2][2:])
     
         # Extract players and their SB levels
         players = [
             (name, details, get_sb_level(details))
             for name, details in war_info['members'].items()
         ]
     
         # Sort players based on SB level (highest first)
         sorted_players = sorted(players, key=lambda x: x[2], reverse=True)

         # Create a new dictionary with sorted players
         sorted_members = {player[0]: player[1] for player in sorted_players}
         
         # Update the war_info dictionary with sorted members
         war_info['members'] = sorted_members
     
         # Save the updated war_info back to the file
         with open(path, 'w') as file:
            json.dump(war_info, file, indent=4)

    async def get_online_status(self, player_name: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.galaxylifegame.net/Users/name?name={player_name}") as user_data:
                if user_data.status == 200:
                    player_data = await user_data.json(content_type="text/plain")
                    player_id = player_data.get('Id')
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"https://api.galaxylifegame.net/Users/platformId?userId={player_id}") as platform_data:
                            if platform_data.status == 200:
                                steamID = await platform_data.text()
                                if steamID:
                                    url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={os.getenv('steam_API_key')}&format=json&steamids={steamID}"
                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(url) as steam_data:
                                            if steam_data.status not in {204, 500, 429}:
                                                response_parse: dict = json.loads(await steam_data.text())
                                                players = response_parse.get('response', {}).get('players', [])
                                                if players:
                                                    player = players[0]
                                                    if player.get('personastate') != 0:
                                                        if player.get('gameextrainfo') == "Galaxy Life":
                                                            return 2
                                                        else:
                                                            return 1
                                                else:
                                                    return 1
                                            else:
                                                return 0

    def format_number(self, num):
        if isinstance(num, str):
            return num
        if num < 1000:
            return str(num)
        elif num < 10000:
            return f"{num / 1000:.1f}k"
        elif num < 1000000:
            return f"{num // 1000}k"
        elif num < 10000000:
            return f"{num / 1000000:.1f}M"
        elif num < 1000000000:
            return f"{num // 1000000}M"
        else:
            return f"{num / 1000000000:.1f}B"
        
    def format_score(self, num):
        return f"{num:,}"
    
    
    def get_unix_time(self, time):
       cet_timezone = pytz.timezone('CET')

       # Get the current time in UTC and then convert to CET
       current_time_utc = datetime.now(pytz.utc)
       current_time_cet = current_time_utc.astimezone(cet_timezone)
       mb_refresh_time_cet = time.astimezone(cet_timezone)
       time_difference = mb_refresh_time_cet - current_time_cet
       hours, remainder = divmod(time_difference.total_seconds(), 3600)
       minutes, _ = divmod(remainder, 60)
       return f"{int(hours)}h{int(minutes)}m"


