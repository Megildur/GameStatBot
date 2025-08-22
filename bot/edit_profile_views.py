
import discord
from discord import Interaction, ui
import json
import pytz

GAME_OPTIONS = [
    discord.SelectOption(label="Rainbow Six Siege", value="r6s", emoji="🎯"),
    discord.SelectOption(label="Battlefield 6", value="bf6", emoji="💥")
]

GAME_NAME_MAP = {
    "r6s": "Rainbow Six Siege",
    "bf6": "Battlefield 6"
}

TIMEZONE_OPTIONS = [
    discord.SelectOption(label="UTC", value="UTC"),
    discord.SelectOption(label="Eastern (EST/EDT)", value="America/New_York"),
    discord.SelectOption(label="Central (CST/CDT)", value="America/Chicago"),
    discord.SelectOption(label="Mountain (MST/MDT)", value="America/Denver"),
    discord.SelectOption(label="Pacific (PST/PDT)", value="America/Los_Angeles"),
    discord.SelectOption(label="European Central (CET/CEST)", value="Europe/Berlin"),
    discord.SelectOption(label="British (GMT/BST)", value="Europe/London"),
    discord.SelectOption(label="Australian Eastern (AEST/AEDT)", value="Australia/Sydney"),
    discord.SelectOption(label="Japanese (JST)", value="Asia/Tokyo"),
]

COLOR_OPTIONS = [
    discord.SelectOption(label="Blue", value="0x00d4ff", emoji="🔵"),
    discord.SelectOption(label="Green", value="0x00ff88", emoji="🟢"),
    discord.SelectOption(label="Red", value="0xff0000", emoji="🔴"),
    discord.SelectOption(label="Purple", value="0x8a2be2", emoji="🟣"),
    discord.SelectOption(label="Orange", value="0xff6600", emoji="🟠"),
    discord.SelectOption(label="Pink", value="0xff69b4", emoji="🩷"),
    discord.SelectOption(label="Yellow", value="0xffff00", emoji="🟡"),
    discord.SelectOption(label="Cyan", value="0x00ffff", emoji="🔷"),
]

def get_game_name(game_code: str) -> str:
    return GAME_NAME_MAP.get(game_code, "Unknown Game")

def get_timezone_display(timezone: str) -> str:
    try:
        tz = pytz.timezone(timezone)
        return f"{timezone} ({tz.zone})"
    except:
        return timezone

class ProfileEditView(ui.LayoutView):
    def __init__(self, db, user_id):
        super().__init__()
        self.db = db
        self.user_id = user_id

    async def refresh_content(self, interaction: Interaction):
        profile = await self.db.get_user_profile(str(interaction.guild_id), str(self.user_id))
        if not profile:
            await self.db.create_user_profile(str(interaction.guild_id), str(self.user_id))
            profile = await self.db.get_user_profile(str(interaction.guild_id), str(self.user_id))
        
        gaming_bio, main_game, social_links_str, embed_color, timezone, team_affiliation = profile
        social_links = json.loads(social_links_str) if social_links_str else {}
        
        user = interaction.guild.get_member(self.user_id)
        user_name = user.display_name if user else "Unknown User"
        
        # Clear existing items and rebuild
        self.clear_items()
        
        container = ui.Container(accent_color=0x00d4ff)
        header = ui.TextDisplay(f'# ⚙️ Profile Editor for {user_name}\n-# Customize your gaming profile')
        container.add_item(header)
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        # Gaming Bio Section
        bio_text = gaming_bio if gaming_bio else 'Not set'
        container.add_item(
            ui.Section(
                ui.TextDisplay(f'## 📝 Gaming Bio\n-# Current: {bio_text}'),
                accessory=EditBioButton(self.db, self.user_id, self)
            )
        )

        # Main Game Section
        game_text = get_game_name(main_game)
        container.add_item(
            ui.Section(
                ui.TextDisplay(f'## 🎮 Main Game\n-# Current: {game_text}'),
                accessory=EditGameButton(self.db, self.user_id, self)
            )
        )

        # Social Links Section
        links_text = f'{len(social_links)} links' if social_links else 'No links set'
        container.add_item(
            ui.Section(
                ui.TextDisplay(f'## 🔗 Social Links\n-# Current: {links_text}'),
                accessory=EditSocialButton(self.db, self.user_id, self)
            )
        )

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Timezone Section
        container.add_item(
            ui.Section(
                ui.TextDisplay(f'## 🌍 Timezone\n-# Current: {timezone}'),
                accessory=EditTimezoneButton(self.db, self.user_id, self)
            )
        )

        # Team Section
        team_text = team_affiliation if team_affiliation else 'Not set'
        container.add_item(
            ui.Section(
                ui.TextDisplay(f'## 🏆 Team Affiliation\n-# Current: {team_text}'),
                accessory=EditTeamButton(self.db, self.user_id, self)
            )
        )

        # Color Section
        container.add_item(
            ui.Section(
                ui.TextDisplay(f'## 🎨 Embed Color\n-# Current: {embed_color}'),
                accessory=EditColorButton(self.db, self.user_id, self)
            )
        )

        self.add_item(container)
        return None  # No content string needed for container layout

class EditBioButton(ui.Button['ProfileEditView']):
    def __init__(self, db, user_id, parent_view):
        super().__init__(label="Edit Bio", style=discord.ButtonStyle.primary, emoji="📝")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        profile = await self.db.get_user_profile(str(interaction.guild_id), str(self.user_id))
        existing_bio = profile[0] if profile else ""
        
        modal = BioModal(self.db, self.user_id, self.parent_view, existing_bio)
        modal.setup_existing_value(existing_bio)
        await interaction.response.send_modal(modal)

class EditGameButton(ui.Button['ProfileEditView']):
    def __init__(self, db, user_id, parent_view):
        super().__init__(label="Change Game", style=discord.ButtonStyle.primary, emoji="🎮")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        view = GameSelectView(self.db, self.user_id, self.parent_view)
        await interaction.response.edit_message(view=view)

class EditSocialButton(ui.Button['ProfileEditView']):
    def __init__(self, db, user_id, parent_view):
        super().__init__(label="Edit Links", style=discord.ButtonStyle.primary, emoji="🔗")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        profile = await self.db.get_user_profile(str(interaction.guild_id), str(self.user_id))
        existing_links = {}
        if profile and profile[2]:
            existing_links = json.loads(profile[2])
        
        modal = SocialLinksModal(self.db, self.user_id, self.parent_view, existing_links)
        modal.setup_existing_values(existing_links)
        await interaction.response.send_modal(modal)

class EditTimezoneButton(ui.Button['ProfileEditView']):
    def __init__(self, db, user_id, parent_view):
        super().__init__(label="Change Timezone", style=discord.ButtonStyle.secondary, emoji="🌍")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        view = TimezoneSelectView(self.db, self.user_id, self.parent_view)
        await interaction.response.edit_message(view=view)

class EditTeamButton(ui.Button['ProfileEditView']):
    def __init__(self, db, user_id, parent_view):
        super().__init__(label="Edit Team", style=discord.ButtonStyle.secondary, emoji="🏆")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        modal = TeamModal(self.db, self.user_id, self.parent_view)
        await interaction.response.send_modal(modal)

class EditColorButton(ui.Button['ProfileEditView']):
    def __init__(self, db, user_id, parent_view):
        super().__init__(label="Change Color", style=discord.ButtonStyle.secondary, emoji="🎨")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        view = ColorSelectView(self.db, self.user_id, self.parent_view)
        await interaction.response.edit_message(view=view)

class BioModal(ui.Modal):
    def __init__(self, db, user_id, parent_view, existing_bio=None):
        super().__init__(title="📝 Edit Gaming Bio")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    bio = ui.TextInput(
        label="Gaming Bio",
        placeholder="Describe your playstyle, achievements, or personality...",
        max_length=200,
        style=discord.TextStyle.paragraph,
        required=False
    )
    
    def setup_existing_value(self, existing_bio):
        self.bio.default = existing_bio or ''

    async def on_submit(self, interaction: Interaction):
        await self.db.update_user_profile(
            str(interaction.guild_id), 
            str(self.user_id), 
            gaming_bio=self.bio.value
        )
        await self.parent_view.refresh_content(interaction)
        await interaction.response.edit_message(view=self.parent_view)

class SocialLinksModal(ui.Modal):
    def __init__(self, db, user_id, parent_view, existing_links=None):
        super().__init__(title="🔗 Edit Social Links")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view
        
        if existing_links is None:
            existing_links = {}

    twitch = ui.TextInput(
        label="Twitch URL",
        placeholder="https://www.twitch.tv/yourusername",
        max_length=200,
        required=False
    )
    
    youtube = ui.TextInput(
        label="YouTube URL",
        placeholder="https://www.youtube.com/@yourchannel",
        max_length=200,
        required=False
    )
    
    twitter = ui.TextInput(
        label="Twitter/X URL",
        placeholder="https://twitter.com/yourusername",
        max_length=200,
        required=False
    )
    
    instagram = ui.TextInput(
        label="Instagram URL",
        placeholder="https://www.instagram.com/yourusername",
        max_length=200,
        required=False
    )
    
    tiktok = ui.TextInput(
        label="TikTok URL",
        placeholder="https://www.tiktok.com/@yourusername",
        max_length=200,
        required=False
    )
    
    def setup_existing_values(self, existing_links):
        self.twitch.default = existing_links.get('twitch', '')
        self.youtube.default = existing_links.get('youtube', '')
        self.twitter.default = existing_links.get('twitter', '')
        self.instagram.default = existing_links.get('instagram', '')
        self.tiktok.default = existing_links.get('tiktok', '')

    async def on_submit(self, interaction: Interaction):
        profile = await self.db.get_user_profile(str(interaction.guild_id), str(self.user_id))
        existing_links = {}
        if profile and profile[2]:
            existing_links = json.loads(profile[2])
        
        if self.twitch.value.strip():
            existing_links['twitch'] = self.twitch.value.strip()
        elif 'twitch' in existing_links and not self.twitch.value.strip():
            del existing_links['twitch']
            
        if self.youtube.value.strip():
            existing_links['youtube'] = self.youtube.value.strip()
        elif 'youtube' in existing_links and not self.youtube.value.strip():
            del existing_links['youtube']
            
        if self.twitter.value.strip():
            existing_links['twitter'] = self.twitter.value.strip()
        elif 'twitter' in existing_links and not self.twitter.value.strip():
            del existing_links['twitter']
            
        if self.instagram.value.strip():
            existing_links['instagram'] = self.instagram.value.strip()
        elif 'instagram' in existing_links and not self.instagram.value.strip():
            del existing_links['instagram']
            
        if self.tiktok.value.strip():
            existing_links['tiktok'] = self.tiktok.value.strip()
        elif 'tiktok' in existing_links and not self.tiktok.value.strip():
            del existing_links['tiktok']
        
        await self.db.update_user_profile(
            str(interaction.guild_id),
            str(self.user_id),
            social_links=json.dumps(existing_links)
        )
        await self.parent_view.refresh_content(interaction)
        await interaction.response.edit_message(view=self.parent_view)

class TeamModal(ui.Modal):
    def __init__(self, db, user_id, parent_view):
        super().__init__(title="🏆 Edit Team Affiliation")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    team = ui.TextInput(
        label="Team Name",
        placeholder="Your current team or organization...",
        max_length=100,
        required=False
    )

    async def on_submit(self, interaction: Interaction):
        await self.db.update_user_profile(
            str(interaction.guild_id),
            str(self.user_id),
            team_affiliation=self.team.value
        )
        await self.parent_view.refresh_content(interaction)
        await interaction.response.edit_message(view=self.parent_view)

class GameSelectView(ui.LayoutView):
    def __init__(self, db, user_id, parent_view):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

        container = ui.Container(accent_color=0x00d4ff)
        header = ui.TextDisplay('# 🎮 Select Main Game\n-# Choose your primary game from the dropdown below')
        container.add_item(header)
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        container.add_item(ui.TextDisplay('## 🎯 Available Games\n-# Select from Rainbow Six Siege or Battlefield 6'))
        container.add_item(GameSelectDropdown(self.db, self.user_id, self.parent_view))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        nav_row = ui.ActionRow()
        nav_row.add_item(BackToProfileButton(self.parent_view))
        container.add_item(nav_row)

        self.add_item(container)

class GameSelectDropdown(ui.ActionRow['GameSelectView']):
    def __init__(self, db, user_id, parent_view):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    @ui.select(
        placeholder="Select your main game...",
        options=GAME_OPTIONS,
        min_values=1,
        max_values=1
    )
    async def select_game(self, interaction: Interaction, select: ui.Select):
        await self.db.update_user_profile(
            str(interaction.guild_id),
            str(self.user_id),
            main_game=select.values[0]
        )
        await self.parent_view.refresh_content(interaction)
        await interaction.response.edit_message(view=self.parent_view)

class TimezoneSelectView(ui.LayoutView):
    def __init__(self, db, user_id, parent_view):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

        container = ui.Container(accent_color=0x00d4ff)
        header = ui.TextDisplay('# 🌍 Select Timezone\n-# Choose your timezone from the dropdown below')
        container.add_item(header)
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        container.add_item(ui.TextDisplay('## 🕒 Available Timezones\n-# Select your local timezone for accurate time display'))
        container.add_item(TimezoneSelectDropdown(self.db, self.user_id, self.parent_view))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        nav_row = ui.ActionRow()
        nav_row.add_item(BackToProfileButton(self.parent_view))
        container.add_item(nav_row)

        self.add_item(container)

class TimezoneSelectDropdown(ui.ActionRow['TimezoneSelectView']):
    def __init__(self, db, user_id, parent_view):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    @ui.select(
        placeholder="Select your timezone...",
        options=TIMEZONE_OPTIONS,
        min_values=1,
        max_values=1
    )
    async def select_timezone(self, interaction: Interaction, select: ui.Select):
        await self.db.update_user_profile(
            str(interaction.guild_id),
            str(self.user_id),
            timezone=select.values[0]
        )
        await self.parent_view.refresh_content(interaction)
        await interaction.response.edit_message(view=self.parent_view)

class ColorSelectView(ui.LayoutView):
    def __init__(self, db, user_id, parent_view):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

        container = ui.Container(accent_color=0x00d4ff)
        header = ui.TextDisplay('# 🎨 Select Embed Color\n-# Choose your profile embed color from the dropdown below')
        container.add_item(header)
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        container.add_item(ui.TextDisplay('## 🌈 Available Colors\n-# Select a color for your profile embeds'))
        container.add_item(ColorSelectDropdown(self.db, self.user_id, self.parent_view))

        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        nav_row = ui.ActionRow()
        nav_row.add_item(BackToProfileButton(self.parent_view))
        container.add_item(nav_row)

        self.add_item(container)

class ColorSelectDropdown(ui.ActionRow['ColorSelectView']):
    def __init__(self, db, user_id, parent_view):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    @ui.select(
        placeholder="Select your embed color...",
        options=COLOR_OPTIONS,
        min_values=1,
        max_values=1
    )
    async def select_color(self, interaction: Interaction, select: ui.Select):
        await self.db.update_user_profile(
            str(interaction.guild_id),
            str(self.user_id),
            embed_color=select.values[0]
        )
        await self.parent_view.refresh_content(interaction)
        await interaction.response.edit_message(view=self.parent_view)

class BackToProfileButton(ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="← Back to Profile", style=discord.ButtonStyle.secondary, emoji="🔙")
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        await self.parent_view.refresh_content(interaction)
        await interaction.response.edit_message(view=self.parent_view)
