import discord
from discord import Interaction

GAME_OPTIONS = [
	discord.SelectOption(label="Rainbow Six Siege", value="r6s", emoji="🎯"),
	discord.SelectOption(label="Battlefield 6", value="bf6", emoji="💥")
]

GAME_NAME_MAP = {
	"r6s": "Rainbow Six Siege",
	"bf6": "Battlefield 6"
}

def get_game_name(game_code: str) -> str:
	return GAME_NAME_MAP.get(game_code, "Unknown Game")

class SelectUserView(discord.ui.View):
	def __init__(self, db) -> None:
		super().__init__(timeout=None)
		self.db = db

	@discord.ui.select(
		placeholder="Select a user...",
		cls=discord.ui.UserSelect
	)
	async def select_user(self, i: Interaction, select: discord.ui.UserSelect) -> None:
		user = select.values[0]
		embed = discord.Embed(
			title=f"🎯 Setting Stats for {user.display_name}",
			description=f"**Selected user:** {user.mention}\n\n🎮 **Next step:** Choose a game from the dropdown below",
			color=0xff6600
		)
		embed.set_thumbnail(url=user.display_avatar.url)
		embed.add_field(
			name="🎲 Available Games",
			value="Select from the game options below to modify statistics",
			inline=False
		)
		embed.set_footer(text="Admin Tool • Step 2 of 3")
		await i.response.edit_message(embed=embed, view=SelectGameView(self.db, user))

class SelectGameView(discord.ui.View):
	def __init__(self, db, user) -> None:
		super().__init__(timeout=None)
		self.db = db
		self.user = user
		self.game = None

	@discord.ui.button(
		label="← Back",
		style=discord.ButtonStyle.secondary,
		custom_id="back_to_user_select",
		emoji="🔙"
	)
	async def back_to_user_select(self, i: Interaction, button: discord.ui.Button) -> None:
		embed = discord.Embed(
			title="🛠️ Admin Stats Editor",
			description="🎯 **Welcome to the Stats Management System**\n\n📋 **Step 1 of 3:** Select a user from the dropdown below to modify their gaming statistics",
			color=0xff6600
		)
		embed.add_field(
			name="⚡ Quick Start",
			value="Click on the user selector below to begin editing stats",
			inline=False
		)
		embed.set_footer(text="🔐 Admin Only Tool • Secure Stats Management")
		await i.response.edit_message(embed=embed, view=SelectUserView(self.db))

	@discord.ui.select(
		placeholder="Select a game...",
		options=GAME_OPTIONS,
		min_values=1,
		max_values=1,
		custom_id="game_select"
	)
	async def select_game(self, i: Interaction, select: discord.ui.Select) -> None:
		self.game = select.values[0]
		stats = await self.db.get_stats(i.guild_id, self.user.id, self.game, stat=None)
		if stats is None:
			stats = await self.db.insert_or_update_stat(i.guild_id, self.user.id, self.game, tournaments_played=0, earnings=0, kills=0, deaths=0, kd=0.0, wins=0, losses=0, wl=0.0)
		
		embed = discord.Embed(
			title=f"📊 Stats Editor: {get_game_name(self.game)}",
			description=f"**Player:** {self.user.mention}\n**Game:** {get_game_name(self.game)}\n\n📈 **Current Statistics:**",
			color=0x00ff00
		)
		embed.set_thumbnail(url=self.user.display_avatar.url)
		kd_ratio = stats[2] / stats[3] if stats[3] > 0 else 0.0
		wl_ratio = stats[5] / stats[6] if stats[6] > 0 else 0.0	
		embed.add_field(name="🏆 Tournaments Played", value=f"`{stats[0]}`", inline=True)
		embed.add_field(name="💰 Earnings", value=f"`${stats[1]:,}`", inline=True)
		embed.add_field(name="🎯 K/D Ratio", value=f"`{kd_ratio:.2f}`", inline=True)
		embed.add_field(name="⚔️ Kills", value=f"`{stats[2]}`", inline=True)
		embed.add_field(name="💀 Deaths", value=f"`{stats[3]}`", inline=True)
		embed.add_field(name="🏅 W/L Ratio", value=f"`{wl_ratio:.2f}`", inline=True)
		embed.add_field(name="✅ Wins", value=f"`{stats[5]}`", inline=True)
		embed.add_field(name="❌ Losses", value=f"`{stats[6]}`", inline=True)
		embed.add_field(name="🎮 Status", value="`Ready to Edit`", inline=True)
		
		embed.set_footer(text="🛠️ Click the button below to modify these stats • Step 3 of 3")
		await i.response.edit_message(embed=embed, view=SetStatsView(self.db, self.user, self.game))

class SetStatsView(discord.ui.View):
	def __init__(self, db, user, game) -> None:
		super().__init__(timeout=None)
		self.db = db
		self.user = user
		self.game = game

	@discord.ui.button(
		label="← Back to Games",
		style=discord.ButtonStyle.secondary,
		custom_id="back_to_game_select",
		emoji="🎮",
		row=0
	)
	async def back_to_game_select(self, i: Interaction, button: discord.ui.Button) -> None:
		embed = discord.Embed(
			title=f"🎯 Setting Stats for {self.user.display_name}",
			description=f"**Selected user:** {self.user.mention}\n\n🎮 **Next step:** Choose a game from the dropdown below",
			color=0xff6600
		)
		embed.set_thumbnail(url=self.user.display_avatar.url)
		embed.add_field(
			name="🎲 Available Games",
			value="Select from the game options below to modify statistics",
			inline=False
		)
		embed.set_footer(text="Admin Tool • Step 2 of 3")
		await i.response.edit_message(embed=embed, view=SelectGameView(self.db, self.user))

	@discord.ui.button(
		label="Select New User",
		style=discord.ButtonStyle.secondary,
		custom_id="select_new_user",
		emoji="👤",
		row=0
	)
	async def select_new_user(self, i: Interaction, button: discord.ui.Button) -> None:
		embed = discord.Embed(
			title="🛠️ Admin Stats Editor",
			description="🎯 **Welcome to the Stats Management System**\n\n📋 **Step 1 of 3:** Select a user from the dropdown below to modify their gaming statistics",
			color=0xff6600
		)
		embed.add_field(
			name="⚡ Quick Start",
			value="Click on the user selector below to begin editing stats",
			inline=False
		)
		embed.set_footer(text="🔐 Admin Only Tool • Secure Stats Management")
		await i.response.edit_message(embed=embed, view=SelectUserView(self.db))

	@discord.ui.button(
		label="Modify Stats",
		style=discord.ButtonStyle.green,
		custom_id="set_stats",
		emoji="✏️",
		row=1
	)
	async def set_stats(self, i: Interaction, button: discord.ui.Button) -> None:
		modal = SetStatsModal(self.db, self.user, self.game)
		await i.response.send_modal(modal)

class SetStatsModal(discord.ui.Modal):
	def __init__(self, db, user, game):
		super().__init__(title=f"📊 Edit Stats: {get_game_name(game)}")
		self.db = db
		self.user = user
		self.game = game
		
		self.tournaments = discord.ui.TextInput(
			label="🏆 Tournaments Played",
			placeholder="Enter number of tournaments...",
			required=False,
			max_length=10
		)
		self.earnings = discord.ui.TextInput(
			label="💰 Earnings ($)",
			placeholder="Enter earnings amount...",
			required=False,
			max_length=15
		)
		self.kills = discord.ui.TextInput(
			label="⚔️ Kills",
			placeholder="Enter kill count...",
			required=False,
			max_length=10
		)
		self.deaths = discord.ui.TextInput(
			label="💀 Deaths",
			placeholder="Enter death count...",
			required=False,
			max_length=10
		)
		self.wins_losses = discord.ui.TextInput(
			label="🏅 Wins,Losses (format: 10,5)",
			placeholder="Enter wins,losses separated by comma...",
			required=False,
			max_length=20
		)
		
		self.add_item(self.tournaments)
		self.add_item(self.earnings)
		self.add_item(self.kills)
		self.add_item(self.deaths)
		self.add_item(self.wins_losses)

	async def on_submit(self, interaction: Interaction):
		try:
			stats_to_update = {}
			
			if self.tournaments.value:
				stats_to_update['tournaments_played'] = int(self.tournaments.value)
			if self.earnings.value:
				stats_to_update['earnings'] = int(self.earnings.value)
			if self.kills.value:
				stats_to_update['kills'] = int(self.kills.value)
			if self.deaths.value:
				stats_to_update['deaths'] = int(self.deaths.value)
			if self.wins_losses.value:
				wins, losses = map(int, self.wins_losses.value.split(','))
				stats_to_update['wins'] = wins
				stats_to_update['losses'] = losses
			
			if not stats_to_update:
				embed = discord.Embed(
					title="⚠️ No Changes Made",
					description="No stat values were provided to update.",
					color=0xffaa00
				)
				await interaction.response.send_message(embed=embed, ephemeral=True)
				return
			
			await self.db.insert_or_update_stat(
				interaction.guild_id, 
				self.user.id, 
				self.game, 
				**stats_to_update
			)
			updated_stats = await self.db.get_stats(interaction.guild_id, self.user.id, self.game, stat=None)
			embed = discord.Embed(
				title=f"📊 Stats Editor: {get_game_name(self.game)}",
				description=f"**Player:** {self.user.mention}\n**Game:** {get_game_name(self.game)}\n\n📈 **Updated Statistics:**",
				color=0x00ff00
			)
			kd_ratio = updated_stats[2] / updated_stats[3] if updated_stats[3] > 0 else 0.0
			wl_ratio = updated_stats[5] / updated_stats[6] if updated_stats[6] > 0 else 0.0
			embed.add_field(name="🏆 Tournaments Played", value=f"`{updated_stats[0]}`", inline=True)
			embed.add_field(name="💰 Earnings", value=f"`${updated_stats[1]:,}`", inline=True)
			embed.add_field(name="🎯 K/D Ratio", value=f"`{kd_ratio:.2f}`", inline=True)
			embed.add_field(name="⚔️ Kills", value=f"`{updated_stats[2]}`", inline=True)
			embed.add_field(name="💀 Deaths", value=f"`{updated_stats[3]}`", inline=True)
			embed.add_field(name="🏅 W/L Ratio", value=f"`{wl_ratio:.2f}`", inline=True)
			embed.add_field(name="✅ Wins", value=f"`{updated_stats[5]}`", inline=True)
			embed.add_field(name="❌ Losses", value=f"`{updated_stats[6]}`", inline=True)
			embed.add_field(name="✅ Status", value="`Successfully Updated`", inline=True)
			
			embed.set_footer(text="🛠️ Stats updated successfully! Click to modify again • Step 3 of 3")
			await interaction.response.edit_message(embed=embed, view=SetStatsView(self.db, self.user, self.game))
			
		except ValueError as e:
			embed = discord.Embed(
				title="❌ Invalid Input",
				description="Please ensure all values are valid numbers.\nFor wins/losses, use format: `wins,losses` (e.g., `10,5`)",
				color=0xff0000
			)
			await interaction.response.send_message(embed=embed, ephemeral=True)
		except Exception as e:
			embed = discord.Embed(
				title="❌ Error Updating Stats",
				description=f"An error occurred: {str(e)}",
				color=0xff0000
			)
			await interaction.response.send_message(embed=embed, ephemeral=True)