import discord
from discord import Interaction
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

class ProfileEditView(discord.ui.View):
    def __init__(self, db, user_id):
        super().__init__(timeout=300)
        self.db = db
        self.user_id = user_id

    async def refresh_embed(self, interaction: Interaction):
        profile = await self.db.get_user_profile(str(interaction.guild_id), str(self.user_id))
        if not profile:
            await self.db.create_user_profile(str(interaction.guild_id), str(self.user_id))
            profile = await self.db.get_user_profile(str(interaction.guild_id), str(self.user_id))
        
        gaming_bio, main_game, social_links_str, embed_color, timezone, team_affiliation = profile
        social_links = json.loads(social_links_str) if social_links_str else {}
        
        embed = discord.Embed(
            title="⚙️ Profile Editor",
            description="🛠️ **Customize your gaming profile**\n\nUse the buttons below to edit different aspects of your profile.",
            color=int(embed_color, 16)
        )
        
        user = interaction.guild.get_member(self.user_id)
        if user:
            embed.set_thumbnail(url=user.display_avatar.url)
        
        embed.add_field(
            name="📝 Gaming Bio",
            value=f"`{gaming_bio}`" if gaming_bio else "`Not set`",
            inline=False
        )
        embed.add_field(
            name="🎮 Main Game",
            value=f"`{get_game_name(main_game)}`",
            inline=True
        )
        embed.add_field(
            name="🌍 Timezone",
            value=f"`{timezone}`",
            inline=True
        )
        embed.add_field(
            name="🏆 Team Affiliation",
            value=f"`{team_affiliation}`" if team_affiliation else "`Not set`",
            inline=True
        )
        embed.add_field(
            name="🔗 Social Links",
            value=f"`{len(social_links)} links`" if social_links else "`No links set`",
            inline=True
        )
        embed.add_field(
            name="🎨 Embed Color",
            value=f"`{embed_color}`",
            inline=True
        )
        
        embed.set_footer(text="💡 Click the buttons below to customize your profile")
        return embed

    @discord.ui.button(label="Gaming Bio", style=discord.ButtonStyle.primary, emoji="📝", row=0)
    async def edit_bio(self, interaction: Interaction, button: discord.ui.Button):
        profile = await self.db.get_user_profile(str(interaction.guild_id), str(self.user_id))
        existing_bio = profile[0] if profile else ""
        
        modal = BioModal(self.db, self.user_id, self, existing_bio)
        modal.setup_existing_value(existing_bio)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Main Game", style=discord.ButtonStyle.primary, emoji="🎮", row=0)
    async def edit_game(self, interaction: Interaction, button: discord.ui.Button):
        view = GameSelectView(self.db, self.user_id, self)
        embed = discord.Embed(
            title="🎮 Select Main Game",
            description="Choose your primary game from the dropdown below:",
            color=0x00d4ff
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Social Links", style=discord.ButtonStyle.primary, emoji="🔗", row=0)
    async def edit_social(self, interaction: Interaction, button: discord.ui.Button):
        profile = await self.db.get_user_profile(str(interaction.guild_id), str(self.user_id))
        existing_links = {}
        if profile and profile[2]:
            existing_links = json.loads(profile[2])
        
        modal = SocialLinksModal(self.db, self.user_id, self, existing_links)
        modal.setup_existing_values(existing_links)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Timezone", style=discord.ButtonStyle.secondary, emoji="🌍", row=1)
    async def edit_timezone(self, interaction: Interaction, button: discord.ui.Button):
        view = TimezoneSelectView(self.db, self.user_id, self)
        embed = discord.Embed(
            title="🌍 Select Timezone",
            description="Choose your timezone from the dropdown below:",
            color=0x00d4ff
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Team", style=discord.ButtonStyle.secondary, emoji="🏆", row=1)
    async def edit_team(self, interaction: Interaction, button: discord.ui.Button):
        modal = TeamModal(self.db, self.user_id, self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Color", style=discord.ButtonStyle.secondary, emoji="🎨", row=1)
    async def edit_color(self, interaction: Interaction, button: discord.ui.Button):
        view = ColorSelectView(self.db, self.user_id, self)
        embed = discord.Embed(
            title="🎨 Select Embed Color",
            description="Choose your profile embed color from the dropdown below:",
            color=0x00d4ff
        )
        await interaction.response.edit_message(embed=embed, view=view)

class BioModal(discord.ui.Modal):
    def __init__(self, db, user_id, parent_view, existing_bio=None):
        super().__init__(title="📝 Edit Gaming Bio")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    bio = discord.ui.TextInput(
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
        embed = await self.parent_view.refresh_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

class SocialLinksModal(discord.ui.Modal):
    def __init__(self, db, user_id, parent_view, existing_links=None):
        super().__init__(title="🔗 Edit Social Links")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view
        
        if existing_links is None:
            existing_links = {}

    twitch = discord.ui.TextInput(
        label="Twitch URL",
        placeholder="https://www.twitch.tv/yourusername",
        max_length=200,
        required=False
    )
    
    youtube = discord.ui.TextInput(
        label="YouTube URL",
        placeholder="https://www.youtube.com/@yourchannel",
        max_length=200,
        required=False
    )
    
    twitter = discord.ui.TextInput(
        label="Twitter/X URL",
        placeholder="https://twitter.com/yourusername",
        max_length=200,
        required=False
    )
    
    instagram = discord.ui.TextInput(
        label="Instagram URL",
        placeholder="https://www.instagram.com/yourusername",
        max_length=200,
        required=False
    )
    
    tiktok = discord.ui.TextInput(
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
        embed = await self.parent_view.refresh_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

class TeamModal(discord.ui.Modal):
    def __init__(self, db, user_id, parent_view):
        super().__init__(title="🏆 Edit Team Affiliation")
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    team = discord.ui.TextInput(
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
        embed = await self.parent_view.refresh_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

class GameSelectView(discord.ui.View):
    def __init__(self, db, user_id, parent_view):
        super().__init__(timeout=60)
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    @discord.ui.select(
        placeholder="Select your main game...",
        options=GAME_OPTIONS,
        min_values=1,
        max_values=1
    )
    async def select_game(self, interaction: Interaction, select: discord.ui.Select):
        await self.db.update_user_profile(
            str(interaction.guild_id),
            str(self.user_id),
            main_game=select.values[0]
        )
        embed = await self.parent_view.refresh_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

class TimezoneSelectView(discord.ui.View):
    def __init__(self, db, user_id, parent_view):
        super().__init__(timeout=60)
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    @discord.ui.select(
        placeholder="Select your timezone...",
        options=TIMEZONE_OPTIONS,
        min_values=1,
        max_values=1
    )
    async def select_timezone(self, interaction: Interaction, select: discord.ui.Select):
        await self.db.update_user_profile(
            str(interaction.guild_id),
            str(self.user_id),
            timezone=select.values[0]
        )
        embed = await self.parent_view.refresh_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

class ColorSelectView(discord.ui.View):
    def __init__(self, db, user_id, parent_view):
        super().__init__(timeout=60)
        self.db = db
        self.user_id = user_id
        self.parent_view = parent_view

    @discord.ui.select(
        placeholder="Select your embed color...",
        options=COLOR_OPTIONS,
        min_values=1,
        max_values=1
    )
    async def select_color(self, interaction: Interaction, select: discord.ui.Select):
        await self.db.update_user_profile(
            str(interaction.guild_id),
            str(self.user_id),
            embed_color=select.values[0]
        )
        embed = await self.parent_view.refresh_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self.parent_view)