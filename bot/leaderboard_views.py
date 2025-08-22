import discord
from discord import Interaction
from bot.edit_stats_views import GAME_OPTIONS, get_game_name
from bot.paginator import ButtonPaginator

STAT_DISPLAY_MAP = {
	'kills': '⚔️ Kills',
	'deaths': '💀 Deaths', 
	'kd': '🎯 K/D Ratio',
	'wins': '✅ Wins',
	'losses': '❌ Losses',
	'wl': '🏅 W/L Ratio',
	'earnings': '💰 Earnings',
	'tournaments_played': '🏆 Tournaments Played'
}

STAT_BUTTONS_CONFIG = [
	("kills", "⚔️", "Kills", 0),
	("deaths", "💀", "Deaths", 0),
	("kd", "🎯", "K/D Ratio", 0),
	("wins", "✅", "Wins", 1),
	("losses", "❌", "Losses", 1),
	("wl", "🏅", "W/L Ratio", 1),
	("earnings", "💰", "Earnings", 2),
	("tournaments_played", "🏆", "Tournaments", 2),
]

def format_stat_value(stat, value):
	if stat == 'earnings':
		return f"${value:,}"
	elif stat in ['kd', 'wl']:
		return f"{value:.2f}"
	else:
		return f"{value:,}"

def get_medal_emoji(position):
	if position == 1:
		return "🥇"
	elif position == 2:
		return "🥈"
	elif position == 3:
		return "🥉"
	else:
		return f"{position}."

def sort_stats(stats, stat):
	if stat in ['deaths', 'losses']:
		def sort_key(x):
			user_id, stat_value = x
			if stat_value == 0:
				return float('inf')
			return stat_value
		return sorted(stats, key=sort_key)
	else:
		return sorted(stats, key=lambda x: x[1], reverse=True)

class LeaderboardEmbedGenerator:
	def __init__(self, db, bot) -> None:
		self.db = db
		self.bot = bot

	async def create_leaderboard_embed(self, guild_id: int, game: str, stat: str, page_info=None):
		if stat in ['deaths', 'losses']:
			opposing_stat = 'kills' if stat == 'deaths' else 'wins'
			all_stats = await self.db.get_stats(guild_id, game_name=game, stat=[stat, opposing_stat])
		else:
			stats = await self.db.get_stats(guild_id, game_name=game, stat=stat)
			all_stats = stats

		if not all_stats:
			embed = discord.Embed(
				title=f"🏆 Leaderboard: {get_game_name(game)}",
				description=f"**{STAT_DISPLAY_MAP.get(stat, stat)}**\n\nNo data available for this game/stat combination.",
				color=0xff6600
			)
			embed.set_footer(text="🎮 Leaderboard • No data found")
			return embed

		processed_stats = []
		if stat in ['deaths', 'losses']:
			opposing_stat = 'kills' if stat == 'deaths' else 'wins'
			stat_index = 0 if stat == 'deaths' else 1
			opposing_index = 1 if stat == 'deaths' else 0
			
			for row in all_stats:
				user_id = row[0]
				main_stat_value = row[2 + stat_index]
				opposing_stat_value = row[2 + opposing_index]
				
				if main_stat_value == 0 and opposing_stat_value == 0:
					sort_key = float('inf')
				else:
					sort_key = main_stat_value
				
				processed_stats.append((user_id, main_stat_value, sort_key))
			
			sorted_stats = sorted(processed_stats, key=lambda x: (x[2], x[1]))
			sorted_stats = [(x[0], x[1]) for x in sorted_stats]
		else:
			for row in all_stats:
				user_id = row[0]
				stat_value = row[2]
				processed_stats.append((user_id, stat_value))
			sorted_stats = sort_stats(processed_stats, stat)

		title = f"🏆 Leaderboard: {get_game_name(game)}"
		description = f"**{STAT_DISPLAY_MAP.get(stat, stat)}**\n\n"

		if page_info:
			description += f"📈 **Players {page_info['start']}-{page_info['end']} of {page_info['total']}:**"
		else:
			description += "📈 **Top Players:**"

		embed = discord.Embed(title=title, description=description, color=0x00ff00)

		if page_info:
			stats_to_show = sorted_stats[page_info['start']-1:page_info['end']]
			start_position = page_info['start']
		else:
			stats_to_show = sorted_stats[:10]
			start_position = 1

		guild = self.bot.get_guild(guild_id)

		for idx, (user_id, stat_value) in enumerate(stats_to_show):
			position = start_position + idx
			medal = get_medal_emoji(position)
			value_display = format_stat_value(stat, stat_value)

			user = None
			user_id_int = int(user_id)

			user = self.bot.get_user(user_id_int)

			if not user:
				if guild:
					user = guild.get_member(user_id_int)
					print(f"User {user_id} not found in cache, trying guild {guild_id}")
			user_display = user.mention

			embed.add_field(
				name=f"{medal} {user_display}",
				value=f"`{value_display}`",
				inline=True
			)

		footer_text = "🎮 Leaderboard • Updated in real-time"
		if page_info:
			footer_text = f"🎮 Leaderboard • Page {page_info['current_page']} • Updated in real-time"

		embed.set_footer(text=footer_text)
		return embed

class LeaderboardView(discord.ui.View):
	def __init__(self, db, bot, game, stat, embed_generator) -> None:
		super().__init__(timeout=300)
		self.db = db
		self.bot = bot
		self.game = game
		self.stat = stat
		self.embed_generator = embed_generator

	async def update_leaderboard(self, interaction: Interaction):
		embed = await self.embed_generator.create_leaderboard_embed(
			interaction.guild_id, self.game, self.stat
		)
		await interaction.response.edit_message(embed=embed, view=self)

	@discord.ui.select(
		placeholder="Choose a different game",
		options=GAME_OPTIONS,
		min_values=0,
		max_values=1,
		custom_id="game_select_leaderboard"
	)
	async def select_game(self, i: Interaction, select: discord.ui.Select) -> None:
		if select.values:
			self.game = select.values[0]
			await self.update_leaderboard(i)

	def _create_stat_buttons(self):
		for stat_name, emoji, label, row_offset in STAT_BUTTONS_CONFIG:
			button = discord.ui.Button(
				label=label,
				style=discord.ButtonStyle.secondary,
				custom_id=f"{stat_name}_button",
				row=row_offset + 1,
				emoji=emoji
			)

			async def make_callback(stat):
				async def callback(interaction):
					self.stat = stat
					await self.update_leaderboard(interaction)
				return callback

			button.callback = make_callback(stat_name)
			self.add_item(button)

	def __post_init__(self):
		self._create_stat_buttons()

class LeaderboardPaginator(ButtonPaginator):
	def __init__(self, db, bot, game, stat, guild_id, **kwargs):
		self.db = db
		self.bot = bot
		self.game = game
		self.stat = stat
		self.guild_id = guild_id
		self.embed_generator = LeaderboardEmbedGenerator(db, bot)
		super().__init__([], **kwargs)

	async def setup_pages(self):
		if self.stat in ['deaths', 'losses']:
			opposing_stat = 'kills' if self.stat == 'deaths' else 'wins'
			all_stats = await self.db.get_stats(self.guild_id, game_name=self.game, stat=[self.stat, opposing_stat])
		else:
			stats = await self.db.get_stats(self.guild_id, game_name=self.game, stat=self.stat)
			all_stats = stats

		if not all_stats:
			embed = await self.embed_generator.create_leaderboard_embed(
				self.guild_id, self.game, self.stat
			)
			self.pages = [embed]
			self.max_pages = 1
			return

		processed_stats = []
		if self.stat in ['deaths', 'losses']:
			opposing_stat = 'kills' if self.stat == 'deaths' else 'wins'
			stat_index = 0 if self.stat == 'deaths' else 1
			opposing_index = 1 if self.stat == 'deaths' else 0
			
			for row in all_stats:
				user_id = row[0]
				main_stat_value = row[2 + stat_index]
				opposing_stat_value = row[2 + opposing_index]
				
				if main_stat_value == 0 and opposing_stat_value == 0:
					sort_key = float('inf')
				else:
					sort_key = main_stat_value
				
				processed_stats.append((user_id, main_stat_value, sort_key))
			
			sorted_stats = sorted(processed_stats, key=lambda x: (x[2], x[1]))
			sorted_stats = [(x[0], x[1]) for x in sorted_stats]
		else:
			for row in all_stats:
				user_id = row[0]
				stat_value = row[2]
				processed_stats.append((user_id, stat_value))
			sorted_stats = sort_stats(processed_stats, self.stat)
		players_per_page = 10
		pages = []

		for i in range(0, len(sorted_stats), players_per_page):
			page_stats = sorted_stats[i:i + players_per_page]
			page_info = {
				'start': i + 1,
				'end': min(i + players_per_page, len(sorted_stats)),
				'total': len(sorted_stats),
				'current_page': len(pages) + 1
			}

			embed = await self.embed_generator.create_leaderboard_embed(
				self.guild_id, self.game, self.stat, page_info
			)
			pages.append(embed)

		self.pages = pages
		self.max_pages = len(self.pages)

	def _setup_buttons(self, custom_buttons=None):
		super()._setup_buttons(custom_buttons)

		dropdown_row = 1 if self.max_pages > 1 else 0
		button_start_row = 2 if self.max_pages > 1 else 1

		game_select = self._create_game_select()
		game_select.row = dropdown_row
		self.add_item(game_select)

		for stat_name, emoji, label, row_offset in STAT_BUTTONS_CONFIG:
			button = self._create_stat_button(stat_name, emoji, label, button_start_row + row_offset)
			self.add_item(button)

	def _create_game_select(self):
		select = discord.ui.Select(
			placeholder="Choose a different game",
			options=GAME_OPTIONS,
			min_values=0,
			max_values=1,
			custom_id="game_select_leaderboard"
		)
		select.callback = self._game_select_callback
		return select

	def _create_stat_button(self, stat_name, emoji, label, row):
		button = discord.ui.Button(
			label=label,
			style=discord.ButtonStyle.secondary,
			custom_id=f"{stat_name}_button",
			row=row,
			emoji=emoji
		)

		async def stat_callback(interaction):
			self.stat = stat_name
			await self.update_leaderboard_data(interaction)

		button.callback = stat_callback
		return button

	async def _game_select_callback(self, interaction: Interaction):
		select = next((item for item in self.children 
		              if isinstance(item, discord.ui.Select) and 
		              item.custom_id == "game_select_leaderboard"), None)

		if select and select.values:
			self.game = select.values[0]
			await self.update_leaderboard_data(interaction)

	async def start(self, obj, **send_kwargs):
		await self.setup_pages()
		self.clear_items()
		self._setup_buttons()

		self.update_buttons()
		kwargs = await self.get_page_kwargs(self.get_page(self.current_page))
		self.reset_files(kwargs)

		if isinstance(obj, discord.Interaction):
			if obj.response.is_done():
				self.message = await obj.followup.send(**kwargs, **send_kwargs)
			else:
				await obj.response.send_message(**kwargs, **send_kwargs)
				self.message = await obj.original_response()
		elif isinstance(obj, discord.abc.Messageable):
			self.message = await obj.send(**kwargs, **send_kwargs)
		else:
			raise TypeError(f"Expected Interaction or Messageable, got {obj.__class__.__name__}")

		return self.message

	async def update_leaderboard_data(self, interaction: Interaction, new_game=None, new_stat=None):
		if new_game:
			self.game = new_game
		if new_stat:
			self.stat = new_stat

		await self.setup_pages()
		self.current_page = 0

		self.clear_items()
		self._setup_buttons()

		self.update_buttons()
		kwargs = await self.get_page_kwargs(self.get_page(self.current_page))
		self.reset_files(kwargs)
		kwargs["attachments"] = kwargs.pop("files", [])
		await interaction.response.edit_message(**kwargs)