import discord
from discord import Interaction, ui

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

class SelectUserView(ui.LayoutView):
	def __init__(self, db) -> None:
		super().__init__()
		self.db = db

		container = ui.Container(accent_color=0x00d4ff)
		header = ui.TextDisplay('# 🛠️ Admin Stats Editor\n-# Welcome to the Stats Management System')
		container.add_item(header)
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		container.add_item(ui.TextDisplay('## Step 1 of 3: Select User\n-# Select a user from the dropdown below to modify their gaming statistics'))
		container.add_item(UserSelectDropdown(self.db))

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
		container.add_item(ui.TextDisplay('## ⚡ Quick Start\n-# Click on the user selector above to begin editing stats'))

		self.add_item(container)

class UserSelectDropdown(ui.ActionRow['SelectUserView']):
	def __init__(self, db):
		super().__init__()
		self.db = db

	@ui.select(placeholder='Select a user...', max_values=1, min_values=1, cls=ui.UserSelect)
	async def select_user(self, interaction: Interaction, select: ui.UserSelect) -> None:
		user = select.values[0]

		if user.bot:
			container = ui.Container(accent_color=0xff6b6b)
			header = ui.TextDisplay('# ❌ Bot User Selected\n-# Bots cannot have gaming statistics')
			container.add_item(header)
			container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
			container.add_item(ui.TextDisplay('## 🤖 Invalid Selection\n-# Please select a human user instead of a bot. Gaming statistics can only be managed for real users.'))
			container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
			container.add_item(ui.TextDisplay('## 🔄 Try Again\n-# Use the user selector above to choose a different user'))
			container.add_item(UserSelectDropdown(self.db))

			error_view = ui.LayoutView()
			error_view.add_item(container)
			await interaction.response.edit_message(view=error_view)
			return

		await interaction.response.edit_message(view=SelectGameView(self.db, user))

class SelectGameView(ui.LayoutView):
	def __init__(self, db, user) -> None:
		super().__init__()
		self.db = db
		self.user = user
		self.game = None

		container = ui.Container(accent_color=0x00d4ff)
		header = ui.TextDisplay(f'# 🎯 Setting Stats for {user.display_name}\n-# Selected user: {user.mention}')
		container.add_item(header)
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		container.add_item(ui.TextDisplay('## Step 2 of 3: Choose Game\n-# Select from the game options below to modify statistics'))
		container.add_item(GameSelectDropdown(self.db, self.user))

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
		container.add_item(ui.TextDisplay('## 🎲 Available Games\n-# Rainbow Six Siege and Battlefield 6 statistics available'))

		nav_row = ui.ActionRow()
		nav_row.add_item(BackToUserButton(self.db))
		container.add_item(nav_row)

		self.add_item(container)

class GameSelectDropdown(ui.ActionRow['SelectGameView']):
	def __init__(self, db, user):
		super().__init__()
		self.db = db
		self.user = user

	@ui.select(
		placeholder="Select a game...",
		options=GAME_OPTIONS,
		min_values=1,
		max_values=1,
		custom_id="game_select"
	)
	async def select_game(self, i: Interaction, select: ui.Select) -> None:
		game = select.values[0]
		stats = await self.db.get_stats(i.guild_id, self.user.id, game, stat=None)
		if stats is None:
			stats = await self.db.insert_or_update_stat(i.guild_id, self.user.id, game, tournaments_played=0, earnings=0, kills=0, deaths=0, kd=0.0, wins=0, losses=0, wl=0.0)

		await i.response.edit_message(view=SetStatsView(self.db, self.user, game, stats, just_updated=False))

class BackToUserButton(ui.Button['SelectGameView']):
	def __init__(self, db):
		super().__init__(label="← Back to User Selection", style=discord.ButtonStyle.secondary, emoji="🔙")
		self.db = db

	async def callback(self, interaction: Interaction) -> None:
		await interaction.response.edit_message(view=SelectUserView(self.db))

class SetStatsView(ui.LayoutView):
	def __init__(self, db, user, game, stats, just_updated=False) -> None:
		super().__init__()
		self.db = db
		self.user = user
		self.game = game
		self.just_updated = just_updated

		container = ui.Container(accent_color=0x00d4ff)
		header = ui.TextDisplay(f'# 📊 Stats Editor: {get_game_name(game)}\n-# Player: {user.mention} • Game: {get_game_name(game)}')
		container.add_item(header)
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		kd_ratio = stats[3] / stats[4] if stats[4] > 0 else 0.0
		wl_ratio = stats[6] / stats[7] if stats[7] > 0 else 0.0

		status_text = "✅ Stats Updated Successfully!" if self.just_updated else "Ready to Edit"
		status_emoji = "✅" if self.just_updated else "🎮"

		stats_text = (
			f'## 📈 Current Statistics\n'
			f'🏆 **Tournaments Played:** `{stats[0]}`\n'
			f'🥇 **Tournaments Won:** `{stats[1]}`\n'
			f'💰 **Earnings:** `${stats[2]:,}`\n'
			f'🎯 **K/D Ratio:** `{kd_ratio:.2f}`\n'
			f'⚔️ **Kills:** `{stats[3]}`\n'
			f'💀 **Deaths:** `{stats[4]}`\n'
			f'🏅 **W/L Ratio:** `{wl_ratio:.2f}`\n'
			f'✅ **Wins:** `{stats[6]}`\n'
			f'❌ **Losses:** `{stats[7]}`\n'
			f'{status_emoji} **Status:** `{status_text}`'
		)

		container.add_item(ui.TextDisplay(stats_text))
		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		container.add_item(
			ui.Section(
				ui.TextDisplay('## ✏️ Modify Statistics\n-# Click the button below to open the stats editor'),
				accessory=ModifyStatsButton(self.db, self.user, self.game)
			)
		)

		container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

		nav_row = ui.ActionRow()
		nav_row.add_item(BackToGameButton(self.db, self.user))
		nav_row.add_item(SelectNewUserButton(self.db))
		container.add_item(nav_row)

		self.add_item(container)

class ModifyStatsButton(ui.Button['SetStatsView']):
	def __init__(self, db, user, game):
		super().__init__(label="Modify Stats", style=discord.ButtonStyle.green, emoji="✏️")
		self.db = db
		self.user = user
		self.game = game

	async def callback(self, interaction: Interaction) -> None:
		modal = SetStatsModal(self.db, self.user, self.game)
		await interaction.response.send_modal(modal)

class BackToGameButton(ui.Button['SetStatsView']):
	def __init__(self, db, user):
		super().__init__(label="← Back to Games", style=discord.ButtonStyle.secondary, emoji="🎮")
		self.db = db
		self.user = user

	async def callback(self, interaction: Interaction) -> None:
		await interaction.response.edit_message(view=SelectGameView(self.db, self.user))

class SelectNewUserButton(ui.Button['SetStatsView']):
	def __init__(self, db):
		super().__init__(label="Select New User", style=discord.ButtonStyle.secondary, emoji="👤")
		self.db = db

	async def callback(self, interaction: Interaction) -> None:
		await interaction.response.edit_message(view=SelectUserView(self.db))

class SetStatsModal(ui.Modal):
	def __init__(self, db, user, game):
		super().__init__(title=f"📊 Edit Stats: {get_game_name(game)}")
		self.db = db
		self.user = user
		self.game = game

		self.tournaments = ui.TextInput(
			label="🏆 Tournaments (format: played,won)",
			placeholder="Enter tournaments played,won (e.g., 15,3)...",
			required=False,
			max_length=20
		)
		self.earnings = ui.TextInput(
			label="💰 Earnings ($)",
			placeholder="Enter earnings amount...",
			required=False,
			max_length=15
		)
		self.kills = ui.TextInput(
			label="⚔️ Kills",
			placeholder="Enter kill count...",
			required=False,
			max_length=10
		)
		self.deaths = ui.TextInput(
			label="💀 Deaths",
			placeholder="Enter death count...",
			required=False,
			max_length=10
		)
		self.wins_losses = ui.TextInput(
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
				tournaments_played, tournaments_won = map(int, self.tournaments.value.split(','))
				stats_to_update['tournaments_played'] = tournaments_played
				stats_to_update['tournaments_won'] = tournaments_won
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
				container = ui.Container(accent_color=0x00d4ff)
				container.add_item(ui.TextDisplay('# ⚠️ No Changes Made\n-# No stat values were provided to update.'))
				await interaction.response.send_message(view=ui.LayoutView().add_item(container), ephemeral=True)
				return

			await self.db.insert_or_update_stat(
				interaction.guild_id,
				self.user.id,
				self.game,
				**stats_to_update
			)
			updated_stats = await self.db.get_stats(interaction.guild_id, self.user.id, self.game, stat=None)

			await interaction.response.edit_message(view=SetStatsView(self.db, self.user, self.game, updated_stats, just_updated=True))

		except ValueError as e:
			container = ui.Container(accent_color=0x00d4ff)
			container.add_item(ui.TextDisplay('# ❌ Invalid Input\n-# Please ensure all values are valid numbers.\n-# For wins/losses, use format: `wins,losses` (e.g., `10,5`)\n-# For tournaments, use format: `played,won` (e.g., `15,3`)'))
			await interaction.response.send_message(view=ui.LayoutView().add_item(container), ephemeral=True)
		except Exception as e:
			container = ui.Container(accent_color=0x00d4ff)
			container.add_item(ui.TextDisplay(f'# ❌ Error Updating Stats\n-# An error occurred: {str(e)}'))
			await interaction.response.send_message(view=ui.LayoutView().add_item(container), ephemeral=True)