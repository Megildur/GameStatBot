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
		self.db = bot.db
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
			Choice(name='Tournaments Played', value='tournaments_played'),
			Choice(name='Tournaments Won', value='tournaments_won')
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
			timeout=300
		)

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
		profile = await self.db.get_user_profile(str(i.guild_id), str(target_user.id))
		if not profile:
			await self.db.create_user_profile(str(i.guild_id), str(target_user.id))
			profile = await self.db.get_user_profile(str(i.guild_id), str(target_user.id))

		if len(profile) == 6:
			gaming_bio, main_game, social_links_str, embed_color, timezone, team_affiliation = profile
			bf6_favorite_class, r6s_role, r6s_favorite_operator = '', '', ''
		else:
			gaming_bio, main_game, social_links_str, embed_color, timezone, team_affiliation, bf6_favorite_class, r6s_role, r6s_favorite_operator = profile

		social_links = json.loads(social_links_str) if social_links_str else {}

		game_name = "None selected" if not main_game else self.game_display_names.get(main_game, main_game)

		embed = discord.Embed(
			title=f"🎮 {target_user.display_name}'s Gaming Profile",
			description=f"📝 **Bio:** {gaming_bio}" if gaming_bio else "📝 **Bio:** *No bio set*",
			color=int(embed_color, 16)
		)
		embed.set_thumbnail(url=target_user.display_avatar.url)

		profile_info = f"🎯 **Main Game:** `{game_name}`\n"
		profile_info += f"🌍 **Timezone:** `{timezone}`\n"
		if team_affiliation:
			profile_info += f"🏆 **Team:** `{team_affiliation}`\n"

		if main_game == 'bf6' and bf6_favorite_class:
			profile_info += f"⭐ **Favorite Class:** `{bf6_favorite_class}`\n"
		elif main_game == 'r6s':
			if r6s_role:
				profile_info += f"⭐ **Role:** `{r6s_role}`\n"
			if r6s_favorite_operator:
				profile_info += f"⭐ **Favorite Operator:** `{r6s_favorite_operator}`\n"


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

		if stats := await self.db.get_stats(i.guild_id, target_user.id, main_game, stat=None) if main_game else None:
			tournaments_played, tournaments_won, earnings, kills, deaths, kd, wins, losses, wl = stats

			stats_text = (
				f"🏆 **Tournaments Played:** **`{tournaments_played:,}`**\n"
				f"🥇 **Tournaments Won:** **`{tournaments_won:,}`**\n"
				f"💰 **Earnings:** **`${earnings:,}`**\n"
				f"🎯 **K/D Ratio:** **`{kd:.2f}`**\n"
				f"🏅 **W/L Ratio:** **`{wl:.2f}`**"
			)

			embed.add_field(
				name=f"📈 {game_name} Stats",
				value=stats_text,
				inline=True
			)

		container = discord.ui.Container(accent_color=int(embed_color, 16))

		header_text = f"# 🎮 {target_user.display_name}'s Gaming Profile"
		if gaming_bio:
			header_text += f"\n📝 **Bio:** {gaming_bio}"
		else:
			header_text += f"\n📝 **Bio:** *No bio set*"

		container.add_item(discord.ui.TextDisplay(header_text))
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		container.add_item(discord.ui.TextDisplay("## 📊 Profile Information"))
		profile_info = f"🎯 **Main Game:** `{game_name}`\n"
		profile_info += f"🌍 **Timezone:** `{timezone}`\n"
		if team_affiliation:
			profile_info += f"🏆 **Team:** `{team_affiliation}`\n"

		if main_game == 'bf6' and bf6_favorite_class:
			profile_info += f"⭐ **Favorite Class:** `{bf6_favorite_class}`\n"
		elif main_game == 'r6s':
			if r6s_role:
				profile_info += f"⭐ **Role:** `{r6s_role}`\n"
			if r6s_favorite_operator:
				profile_info += f"⭐ **Favorite Operator:** `{r6s_favorite_operator}`\n"

		container.add_item(discord.ui.TextDisplay(profile_info))

		if social_links:
			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
			container.add_item(discord.ui.TextDisplay("## 🔗 Social Links"))
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

			container.add_item(discord.ui.TextDisplay(social_text))

		if stats := await self.db.get_stats(i.guild_id, target_user.id, main_game, stat=None) if main_game else None:
			tournaments_played, tournaments_won, earnings, kills, deaths, kd, wins, losses, wl = stats

			container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
			container.add_item(discord.ui.TextDisplay(f"## 📈 {game_name} Stats"))

			stats_text = (
				f"🏆 **Tournaments Played:** **`{tournaments_played:,}`**\n"
				f"🥇 **Tournaments Won:** **`{tournaments_won:,}`**\n"
				f"💰 **Earnings:** **`${earnings:,}`**\n"
				f"⚔️ **Kills:** **`{kills:,}`**\n"
				f"💀 **Deaths:** **`{deaths:,}`**\n"
				f"🎯 **K/D Ratio:** **`{kd:.2f}`**\n"
				f"✅ **Wins:** **`{wins:,}`**\n"
				f"❌ **Losses:** **`{losses:,}`**\n"
				f"🏅 **W/L Ratio:** **`{wl:.2f}`**"
			)

			container.add_item(discord.ui.TextDisplay(stats_text))

		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
		container.add_item(discord.ui.TextDisplay("-# 🎮 Gaming Profile • Use /stats set profile to edit"))

		view = discord.ui.LayoutView()
		view.add_item(container)
		await i.response.send_message(view=view)

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
		target_user = user if user else i.user
		stats = await self.db.get_stats(i.guild_id, target_user.id, game, stat=None)

		container = discord.ui.Container(accent_color=0x00d4ff)

		header_text = f"# 📊 Gaming Statistics\n🎯 **Player:** {target_user.mention}"
		container.add_item(discord.ui.TextDisplay(header_text))
		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

		if stats is None or (isinstance(stats, list) and len(stats) == 0):
			container.add_item(discord.ui.TextDisplay("## ❌ No Statistics Found"))
			no_stats_text = f"This player has no gaming statistics recorded yet.\n\n💡 *Start playing tournaments to build your stats!*"
			container.add_item(discord.ui.TextDisplay(no_stats_text))
		else:
			if isinstance(stats, tuple):
				tournaments_played = stats[0]
				tournaments_won = stats[1]
				earnings = stats[2]
				kills = stats[3]
				deaths = stats[4]
				kd = stats[5]
				wins = stats[6]
				losses = stats[7]
				wl = stats[8]

				game_name = self.game_display_names.get(game, game)

				container.add_item(discord.ui.TextDisplay(f"## 🎮 {game_name}"))

				stats_text = (
					f"🏆 **Tournaments Played:** **`{tournaments_played:,}`**\n"
					f"🥇 **Tournaments Won:** **`{tournaments_won:,}`**\n"
					f"💰 **Earnings:** **`${earnings:,}`**\n"
					f"⚔️ **Kills:** **`{kills:,}`**\n"
					f"💀 **Deaths:** **`{deaths:,}`**\n"
					f"🎯 **K/D Ratio:** **`{kd:.2f}`**\n"
					f"✅ **Wins:** **`{wins:,}`**\n"
					f"❌ **Losses:** **`{losses:,}`**\n"
					f"🏅 **W/L Ratio:** **`{wl:.2f}`**"
				)

				container.add_item(discord.ui.TextDisplay(stats_text))
			else:
				for idx, game_stats in enumerate(stats):
					if idx > 0:
						container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

					game_code = game_stats[0]
					game_name = self.game_display_names.get(game_code, game_code)
					tournaments_played = game_stats[1]
					tournaments_won = game_stats[2]
					earnings = game_stats[3]
					kills = game_stats[4]
					deaths = game_stats[5]
					kd = game_stats[6]
					wins = game_stats[7]
					losses = game_stats[8]
					wl = game_stats[9]

					container.add_item(discord.ui.TextDisplay(f"## 🎮 {game_name}"))

					stats_text = (
						f"🏆 **Tournaments Played:** **`{tournaments_played:,}`**\n"
						f"🥇 **Tournaments Won:** **`{tournaments_won:,}`**\n"
						f"💰 **Earnings:** **`${earnings:,}`**\n"
						f"⚔️ **Kills:** **`{kills:,}`**\n"
						f"💀 **Deaths:** **`{deaths:,}`**\n"
						f"🎯 **K/D Ratio:** **`{kd:.2f}`**\n"
						f"✅ **Wins:** **`{wins:,}`**\n"
						f"❌ **Losses:** **`{losses:,}`**\n"
						f"🏅 **W/L Ratio:** **`{wl:.2f}`**"
					)

					container.add_item(discord.ui.TextDisplay(stats_text))

		container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
		container.add_item(discord.ui.TextDisplay("-# 🎮 Live Gaming Stats • Real-time Data"))

		view = discord.ui.LayoutView()
		view.add_item(container)
		await i.response.send_message(view=view)

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
		profile = await self.db.get_user_profile(str(i.guild_id), str(i.user.id))
		if not profile:
			await self.db.create_user_profile(str(i.guild_id), str(i.user.id))

		view = ProfileEditView(self.db, i.user.id)
		await view.refresh_content(i)

		await i.response.send_message(view=view, ephemeral=True)

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
		await i.response.send_message(view=view, ephemeral=True)

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
					str(i.guild_id),
					str(user.id),
					game,
					tournaments_played=0,
					tournaments_won=0,
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
				str(i.guild_id),
				str(user.id),
				game,
				tournaments_played=0,
				tournaments_won=0,
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

		await self.db.delete_user_profile(str(i.guild_id), str(user_id))
		for game in game_list:
			await self.db.delete_stats(str(i.guild_id), str(user_id), game)
		await self.db.delete_player_left(str(i.guild_id), str(user_id))

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
		player = await self.db.get_player_left(str(member.guild.id), str(member.id))
		if player:
			await self.db.delete_player_left(str(member.guild.id), str(member.id))
			print(f"Deleted player left record for {member.name} in {member.guild.name}")
			return
		for game in game_list:
			await self.db.insert_or_update_stat(
				str(member.guild.id),
				str(member.id),
				game,
				tournaments_played=0,
				tournaments_won=0,
				earnings=0,
				kills=0,
				deaths=0,
				kd=0.0,
				wins=0,
				losses=0,
				wl=0.0
			)
			print(f"Initialized stats for {member.name} in {member.guild.name} for {game}")
		await self.db.create_user_profile(str(member.guild.id), str(member.id))
		print(f"Initialized profile for {member.name} in {member.guild.name}")

	@commands.Cog.listener()
	async def on_member_remove(self, member: discord.Member) -> None:
		if member.bot:
			return
		await self.db.player_left(str(member.guild.id), str(member.id), member.name, member.display_name)

async def setup(bot) -> None:
	await bot.add_cog(Commands(bot))