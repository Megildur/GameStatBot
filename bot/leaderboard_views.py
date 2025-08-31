
import discord
from discord import Interaction
import discord.ui as ui
from bot.edit_stats_views import GAME_OPTIONS, get_game_name

STAT_DISPLAY_MAP = {
	'kills': '⚔️ Kills',
	'deaths': '💀 Deaths', 
	'kd': '🎯 K/D Ratio',
	'wins': '✅ Wins',
	'losses': '❌ Losses',
	'wl': '🏅 W/L Ratio',
	'earnings': '💰 Earnings',
	'tournaments_played': '🏆 Tournaments Played',
	'tournaments_won': '🥇 Tournaments Won'
}

STAT_BUTTONS_CONFIG = [
	("kills", "⚔️", "Kills"),
	("deaths", "💀", "Deaths"),
	("kd", "🎯", "K/D"),
	("wins", "✅", "Wins"),
	("losses", "❌", "Losses"),
	("wl", "🏅", "W/L"),
	("earnings", "💰", "Earnings"),
	("tournaments_played", "🏆", "Tournaments"),
	("tournaments_won", "🥇", "T. Won"),
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

class LeaderboardView(discord.ui.View):
	def __init__(self, db, bot, game, stat, guild_id, **kwargs):
		super().__init__(timeout=kwargs.get('timeout', 300))
		self.db = db
		self.bot = bot
		self.game = game
		self.stat = stat
		self.guild_id = guild_id
		self.author_id = kwargs.get('author_id')
		self.current_page = 0
		self.pages = []
		self.max_pages = 0
		self.players_per_page = 10

	async def setup_pages(self):
		if self.stat in ['deaths', 'losses']:
			opposing_stat = 'kills' if self.stat == 'deaths' else 'wins'
			all_stats = await self.db.get_stats(self.guild_id, game_name=self.game, stat=[self.stat, opposing_stat])
		else:
			stats = await self.db.get_stats(self.guild_id, game_name=self.game, stat=self.stat)
			all_stats = stats

		if not all_stats:
			self.pages = [None]
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

		pages = []
		for i in range(0, len(sorted_stats), self.players_per_page):
			page_stats = sorted_stats[i:i + self.players_per_page]
			pages.append(page_stats)

		self.pages = pages
		self.max_pages = len(self.pages)

	def create_embed(self, page_stats=None):
		game_name = get_game_name(self.game)
		stat_name = STAT_DISPLAY_MAP.get(self.stat, self.stat)

		embed = discord.Embed(
			title=f"🏆 Leaderboard: {game_name}",
			color=0x00d4ff
		)

		if page_stats is None:
			embed.description = f"**{stat_name}**\n\n❌ No data available for this game/stat combination."
		else:
			total_players = sum(len(page) for page in self.pages)
			start_position = self.current_page * self.players_per_page + 1
			end_position = min(start_position + len(page_stats) - 1, total_players)

			embed.description = f"**{stat_name}**\n\n📈 **Players {start_position}-{end_position} of {total_players}:**"

			guild = self.bot.get_guild(self.guild_id)
			start_position = self.current_page * self.players_per_page + 1

			leaderboard_text = ""
			for idx, (user_id, stat_value) in enumerate(page_stats):
				position = start_position + idx
				medal = get_medal_emoji(position)
				value_display = format_stat_value(self.stat, stat_value)

				user = self.bot.get_user(int(user_id))
				if not user and guild:
					user = guild.get_member(int(user_id))

				user_display = user.display_name if user else f"User {user_id}"
				leaderboard_text += f"{medal} **{user_display}** - `{value_display}`\n"

			embed.add_field(name="Rankings", value=leaderboard_text, inline=False)

		footer_text = "🎮 Leaderboard • Updated in real-time"
		if self.max_pages > 1:
			footer_text = f"🎮 Leaderboard • Page {self.current_page + 1}/{self.max_pages} • Updated in real-time"

		embed.set_footer(text=footer_text)
		return embed

	def update_buttons(self):
		# Clear all items first
		self.clear_items()

		# Add navigation buttons if multiple pages
		if self.max_pages > 1:
			prev_button = discord.ui.Button(
				label="◀️ Previous",
				style=discord.ButtonStyle.secondary,
				disabled=self.current_page == 0,
				row=0
			)
			prev_button.callback = self._previous_callback
			self.add_item(prev_button)

			page_button = discord.ui.Button(
				label=f"Page {self.current_page + 1}/{self.max_pages}",
				style=discord.ButtonStyle.primary,
				disabled=True,
				row=0
			)
			self.add_item(page_button)

			next_button = discord.ui.Button(
				label="Next ▶️",
				style=discord.ButtonStyle.secondary,
				disabled=self.current_page == self.max_pages - 1,
				row=0
			)
			next_button.callback = self._next_callback
			self.add_item(next_button)

		# Add game selector
		game_select = discord.ui.Select(
			placeholder="Choose a different game",
			options=GAME_OPTIONS,
			min_values=0,
			max_values=1,
			row=1
		)
		game_select.callback = self._game_select_callback
		self.add_item(game_select)

		# Add stat buttons in rows
		for i in range(0, len(STAT_BUTTONS_CONFIG), 3):
			row_num = 2 + (i // 3)
			for j in range(3):
				if i + j < len(STAT_BUTTONS_CONFIG):
					stat_name, emoji, label = STAT_BUTTONS_CONFIG[i + j]
					button = discord.ui.Button(
						label=label,
						style=discord.ButtonStyle.secondary,
						emoji=emoji,
						row=row_num
					)

					async def make_callback(stat):
						async def callback(interaction):
							self.stat = stat
							await self.update_leaderboard_data(interaction)
						return callback

					button.callback = make_callback(stat_name)
					self.add_item(button)

	async def _previous_callback(self, interaction: Interaction):
		if self.current_page > 0:
			self.current_page -= 1
			await self.update_page(interaction)

	async def _next_callback(self, interaction: Interaction):
		if self.current_page < self.max_pages - 1:
			self.current_page += 1
			await self.update_page(interaction)

	async def _game_select_callback(self, interaction: Interaction):
		if hasattr(interaction.data, 'values') and interaction.data['values']:
			self.game = interaction.data['values'][0]
			await self.update_leaderboard_data(interaction)

	async def update_page(self, interaction: Interaction):
		page_stats = self.pages[self.current_page] if self.pages and self.current_page < len(self.pages) else None
		embed = self.create_embed(page_stats)
		self.update_buttons()
		await interaction.response.edit_message(embed=embed, view=self)

	async def update_leaderboard_data(self, interaction: Interaction):
		await self.setup_pages()
		self.current_page = 0
		page_stats = self.pages[self.current_page] if self.pages and self.current_page < len(self.pages) else None
		embed = self.create_embed(page_stats)
		self.update_buttons()
		await interaction.response.edit_message(embed=embed, view=self)

	async def interaction_check(self, interaction: Interaction) -> bool:
		if not self.author_id:
			return True

		if self.author_id != interaction.user.id:
			await interaction.response.send_message("You cannot interact with this menu.", ephemeral=True)
			return False

		return True

	async def start(self, interaction: Interaction):
		await self.setup_pages()
		page_stats = self.pages[self.current_page] if self.pages and self.current_page < len(self.pages) else None
		embed = self.create_embed(page_stats)
		self.update_buttons()
		await interaction.response.send_message(embed=embed, view=self)

# Keep backwards compatibility
LeaderboardPaginator = LeaderboardView
ContainerPaginator = LeaderboardView
