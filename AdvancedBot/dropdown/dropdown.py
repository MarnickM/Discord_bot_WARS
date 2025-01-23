import discord
from database import database
db_operations = database.DatabaseConnection()


class ScoreDropDown(discord.ui.Select):
    def __init__(self, members, index):
        members = sorted(members, key=lambda x: x['points_gained'], reverse=True)
        options = [
            discord.SelectOption(label=f"{member['points_gained']} - {member['Name']}", value=member['Name'], emoji="⭐")
            for member in members
        ]
        member_count = len(members)
        if member_count <= 25:
            super().__init__(placeholder=f"View scores of the members", options=options)
        else:
            super().__init__(placeholder=f"View scores of the members (Part{index})", options=options)

    # to send a message to the user when they select an option
    # async def callback(self, interaction: discord.Interaction):
    #     selected_member = self.values[0]
    #     player_data = db_operations.find_player(selected_member)
    #     if player_data:
    #         score = player_data['total_warpoints']
    #         await interaction.response.send_message(f"{selected_member}'s score: {score} <:Warpoints:1206215489349619722>", ephemeral=True)
    #     else:
    #         await interaction.response.send_message(f"No data found for {selected_member}", ephemeral=True)

class ScoreDropDownView(discord.ui.View):
    def __init__(self, members):
        super().__init__()
        chunk_size = 25
        for i in range(0, len(members), chunk_size):
            chunk = members[i:i + chunk_size]
            dropdown = ScoreDropDown(chunk, index=(i // chunk_size) + 1)
            self.add_item(dropdown)
