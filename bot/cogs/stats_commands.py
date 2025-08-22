import discord
from discord.ext import commands
from discord import Interaction, app_commands
from discord.app_commands import Choice
from typing import Optional
import json
from ..database import GameStatsDatabase
from ..edit_stats_views import SelectUserView
from ..edit_profile_views import ProfileEditView
from ..leaderboard_views import LeaderboardPaginator

game_list = ['r6s', 'bf6']

async def user_autocomplete(interaction: Interaction, current: str):
	try:
		db = interaction.client.db
		players_left = await db.get_server_players_left(interaction.guild_id)
		
		choices = []
		for user_id, user_name, display_name in players_left:
			search_text = f"{user_name} {display_name}".lower()
			
			if current.lower() in search_text:
				label = f"{display_name} ({user_name})" if user_name != display_name else user_name
				value = f"{user_id}:{label}"
				choices.append(app_commands.Choice(name=label[:100], value=value[:100]))
			
			if len(choices) >= 25:
				break
		
		return choices
	except Exception as e:
		print(f"Error in user_autocomplete: {e}")
		return []

class Commands(commands.Cog):
	def __init__(self, bot) -> None:
		self.bot = bot
		self.db = GameStatsDatabase('data/game_stats.db')
		self.game_display_names = {'r6s': 'Rainbow Six Siege', 'bf6': 'Battlefield 6'}
		print(f"Commands loaded")

	stats = app_commands.Group(
		name='stats', 
		description='Stats commands'
	)

	@stats.command(
		name='leaderboard', 
		description='Shows the leaderboard'
	)
	@app_commands.choices(
		game=[
			Choice(name='Rainbow Six Siege', value='r6s'),
			Choice(name='Battlefield 6', value='bf6')
		],
		stat=[
			Choice(name='Kills', value='kills'),
			Choice(name='Deaths', value='deaths'),
			Choice(name='K/D Ratio', value='kd'),
			Choice(name='Wins', value='wins'),
			Choice(name='Losses', value='losses'),
			Choice(name='W/L Ratio', value='wl'),
			Choice(name='Earnings', value='earnings'),
			Choice(name='Tournaments Played', value='tournaments_played')
		]
	)
	@app_commands.describe(
		game='The game to show the leaderboard for',
		stat='The stat to show the leaderboard for'
	)
	async def leaderboard(self, i: Interaction, game: str, stat: str):
		paginator = LeaderboardPaginator(
			self.db,
			self.bot,
			game, 
			stat, 
			i.guild_id,
			author_id=i.user.id,
			timeout=300,
			per_page=1
		)
		
		await paginator.setup_pages()
		await paginator.start(i)

	@stats.command(
		name='profile', 
		description='Shows user profile'
	)
	@app_commands.describe(
		user='The user to show the profile for(defaults to yourself)'
	)
	async def profile(self, i: Interaction, user: Optional[discord.Member]) -> None:
		target_user = user if user else i.user
		profile = await self.db.get_user_profile(i.guild_id, target_user.id)
		if not profile:
			await self.db.create_user_profile(i.guild_id, target_user.id)
			profile = await self.db.get_user_profile(i.guild_id, target_user.id)
		
		gaming_bio, main_game, social_links_str, embed_color, timezone, team_affiliation = profile
		social_links = json.loads(social_links_str) if social_links_str else {}
		stats = await self.db.get_stats(i.guild_id, target_user.id, main_game, stat=None)
		
		embed = discord.Embed(
			title=f"🎮 {target_user.display_name}'s Gaming Profile",
			description=f"📝 **Bio:** {gaming_bio}" if gaming_bio else "📝 **Bio:** *No bio set*",
			color=int(embed_color, 16)
		)
		embed.set_thumbnail(url=target_user.display_avatar.url)
		
		game_name = self.game_display_names.get(main_game, main_game)
		
		profile_info = f"🎯 **Main Game:** `{game_name}`\n"
		profile_info += f"🌍 **Timezone:** `{timezone}`\n"
		if team_affiliation:
			profile_info += f"🏆 **Team:** `{team_affiliation}`\n"
		
		embed.add_field(
			name="📊 Profile Information",
			value=profile_info,
			inline=False
		)
		
		if social_links:
			social_text = ""
			for platform, url in social_links.items():
				emoji_map = {
					'twitch': '📺', 
					'youtube': '📹', 
					'twitter': '🐦',
					'instagram': '📷',
					'tiktok': '🎵'
				}
				emoji = emoji_map.get(platform, '🔗')
				social_text += f"{emoji} **{platform.capitalize()}:** [Visit Profile]({url})\n"
			
			embed.add_field(
				name="🔗 Social Links",
				value=social_text,
				inline=False
			)
		
		if stats:
			tournaments_played, earnings, kills, deaths, kd, wins, losses, wl = stats
			
			stats_text = (
				f"🏆 **Tournaments:** `{tournaments_played}`\n"
				f"💰 **Earnings:** `${earnings:,}`\n"
				f"🎯 **K/D Ratio:** `{kd:.2f}`\n"
				f"🏅 **W/L Ratio:** `{wl:.2f}`"
			)
			
			embed.add_field(
				name=f"📈 {game_name} Stats",
				value=stats_text,
				inline=True
			)
		
		embed.set_footer(text="🎮 Gaming Profile • Use /stats set profile to customize")
		
		await i.response.send_message(embed=embed)

	@stats.command(
		name='view', 
		description='Shows user stats'
	)
	@app_commands.choices(
		game=[
			Choice(name='Rainbow Six Siege', value='r6s'),
			Choice(name='Battlefield 6', value='bf6')
		]
	)
	@app_commands.describe(
		user='The user to show the stats for(defaults to yourself)'
	)
	async def view(self, i: Interaction, user: Optional[discord.Member], game: Optional[str] = None) -> None:
		stats = await self.db.get_stats(i.guild_id, user.id if user else i.user.id, game, stat=None)
		if stats is None or (isinstance(stats, list) and len(stats) == 0):
			embed = discord.Embed(
				title="📈 No Statistics Found",
				description=f"🔍 **Player:** {user.mention if user else i.user.mention}\n\n❌ This player has no gaming statistics recorded yet.\n\n💡 *Start playing tournaments to build your stats!*",
				color=0xff6b6b
			)
			await i.response.send_message(embed=embed)
			return

		embed = discord.Embed(
			title=f"📊 Gaming Statistics",
			description=f"🎯 **Player:** {user.mention if user else i.user.mention}\n━━━━━━━━━━━━━━━━━━━━━━━━━━",
			color=0x00d4ff
		)
		embed.set_thumbnail(url=user.display_avatar.url if user else i.user.display_avatar.url)
		embed.set_footer(
			text="🎮 Live Gaming Stats • Real-time Data"
		)

		if isinstance(stats, tuple):
			tournaments_played = stats[0]
			earnings = stats[1]
			kills = stats[2]
			deaths = stats[3]
			kd = stats[4]
			wins = stats[5]
			losses = stats[6]
			wl = stats[7]
			
			game_name = self.game_display_names.get(game, game)

			embed.add_field(
				name=f"🎮 {game_name}",
				value=(
					f"🏆 **Tournaments:** `{tournaments_played}`\n"
					f"💰 **Earnings:** `${earnings:,}`\n"
					f"⚔️ **Kills:** `{kills:,}`\n"
					f"💀 **Deaths:** `{deaths:,}`\n"
					f"🎯 **K/D Ratio:** `{kd:.2f}`\n"
					f"✅ **Wins:** `{wins:,}`\n"
					f"❌ **Losses:** `{losses:,}`\n"
					f"🏅 **W/L Ratio:** `{wl:.2f}`"
				),
				inline=False
			)
		else:
			
			for game_stats in stats:
				game_code = game_stats[0]
				game_name = self.game_display_names.get(game_code, game_code)
				tournaments_played = game_stats[1]
				earnings = game_stats[2]
				kills = game_stats[3]
				deaths = game_stats[4]
				kd = game_stats[5]
				wins = game_stats[6]
				losses = game_stats[7]
				wl = game_stats[8]

				embed.add_field(
					name=f"🎮 {game_name}",
					value=(
						f"🏆 **Tournaments:** `{tournaments_played}`\n"
						f"💰 **Earnings:** `${earnings:,}`\n"
						f"⚔️ **Kills:** `{kills:,}`\n"
						f"💀 **Deaths:** `{deaths:,}`\n"
						f"🎯 **K/D Ratio:** `{kd:.2f}`\n"
						f"✅ **Wins:** `{wins:,}`\n"
						f"❌ **Losses:** `{losses:,}`\n"
						f"🏅 **W/L Ratio:** `{wl:.2f}`"
					),
					inline=False
				)
		
		await i.response.send_message(embed=embed)

	set = app_commands.Group(
		name='set', 
		description='Set your preferences', 
		parent=stats
	)

	@set.command(
		name='profile', 
		description='Set your profile descriptions'
	)
	async def set_profile(self, i: Interaction) -> None:
		profile = await self.db.get_user_profile(i.guild_id, i.user.id)
		if not profile:
			await self.db.create_user_profile(i.guild_id, i.user.id)
		
		view = ProfileEditView(self.db, i.user.id)
		embed = await view.refresh_embed(i)
		
		await i.response.send_message(embed=embed, view=view, ephemeral=True)

	admin = app_commands.Group(
		name='admin', 
		description='Admin commands', 
		default_permissions=discord.Permissions(
			manage_guild=True
		)
	)
	
	@admin.command(
		name='set_stats', 
		description='add or remove stats from users'
	)
	async def set_stats(self, i: Interaction) -> None:
		view = SelectUserView(self.db)
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
		await i.response.send_message(embed=embed, view=view, ephemeral=True)

	@admin.command(
		name='reset_stats', 
		description='Reset all stats for a user'
	)
	@app_commands.describe(
		user='The user to reset the stats for',
		game='The game to reset the stats for (leave blank to reset all games)'
	)
	@app_commands.choices(
		game=[
			Choice(name='Rainbow Six Siege', value='r6s'),
			Choice(name='Battlefield 6', value='bf6')
		]
	)
	async def reset_stats(self, i: Interaction, user: discord.Member, game: Optional[str] = None) -> None:
		if game is None:
			for game in game_list:
				await self.db.insert_or_update_stat(
					i.guild_id,
					user.id,
					game,
					tournaments_played=0,
					earnings=0,
					kills=0,
					deaths=0,
					kd=0.0,
					wins=0,
					losses=0,
					wl=0.0
				)
				embed = discord.Embed(
					title="🛠️ Admin Stats Reset",
					description=f"🎯 **User:** {user.mention}\n\n✅ **Stats Reset Successful**\n\n📋 All gaming statistics for this user have been reset to zero.",
				color=0x00ff00
		)
				embed.set_footer(text="🔐 Admin Only Tool • Secure Stats Management")
				await i.response.send_message(embed=embed, ephemeral=True)
		else:
			await self.db.insert_or_update_stat(
				i.guild_id,
				user.id,
				game,
				tournaments_played=0,
				earnings=0,
				kills=0,
				deaths=0,
				kd=0.0,
				wins=0,
				losses=0,
				wl=0.0
			)
			embed = discord.Embed(
				title="🛠️ Admin Stats Reset",
				description=f"🎯 **User:** {user.mention}\n\n✅ **Stats Reset Successful**\n\n📋 All gaming statistics for this user have been reset to zero for {self.game_display_names.get(game, game)}",
				color=0x00ff00
			)
			embed.set_footer(text="🔐 Admin Only Tool • Secure Stats Management")
			await i.response.send_message(embed=embed, ephemeral=True)

	@admin.command(
		name='delete_user',
		description='Delete all data for a user'
		)
	@app_commands.describe(
		user='The user to delete the data for'
	)
	@app_commands.autocomplete(
		user=user_autocomplete
	)
	async def delete_user(self, i: Interaction, user: str) -> None:
		try:
			user_id = int(user.split(':')[0])
		except (ValueError, IndexError):
			embed = discord.Embed(
				title="❌ Invalid User Selection",
				description="Please select a valid user from the autocomplete list.",
				color=0xff0000
			)
			await i.response.send_message(embed=embed, ephemeral=True)
			return
		
		await self.db.delete_user_profile(i.guild_id, user_id)
		for game in game_list:
			await self.db.delete_stats(i.guild_id, user_id, game)
		await self.db.delete_player_left(i.guild_id, user_id)
		
		embed = discord.Embed(
			title="🗑️ User Data Deleted",
			description=f"✅ All data for user ID `{user_id}` has been successfully deleted from the database.",
			color=0x00ff00
		)
		embed.set_footer(text="🔐 Admin Only Tool • Secure Data Management")
		await i.response.send_message(embed=embed, ephemeral=True)

	@commands.Cog.listener()
	async def on_member_join(self, member: discord.Member) -> None:
		if member.bot:
			return
		player = await self.db.get_player_left(member.guild.id, member.id)
		if player:
			await self.db.delete_player_left(member.guild.id, member.id)
			print(f"Deleted player left record for {member.name} in {member.guild.name}")
			return
		for game in game_list:
			await self.db.insert_or_update_stat(
				member.guild.id,
				member.id,
				game,
				tournaments_played=0,
				earnings=0,
				kills=0,
				deaths=0,
				kd=0.0,
				wins=0,
				losses=0,
				wl=0.0
			)
			print(f"Initialized stats for {member.name} in {member.guild.name} for {game}")
		await self.db.create_user_profile(member.guild.id, member.id)
		print(f"Initialized profile for {member.name} in {member.guild.name}")

	@commands.Cog.listener()
	async def on_member_remove(self, member: discord.Member) -> None:
		if member.bot:
			return
		await self.db.player_left(member.guild.id, member.id, member.name, member.display_name)

async def setup(bot) -> None:
	await bot.add_cog(Commands(bot))