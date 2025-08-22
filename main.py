import discord
from discord.ext import commands, tasks
import os
import logging
from dotenv import load_dotenv
import random
from bot.database import GameStatsDatabase

load_dotenv()

intents = discord.Intents.all()

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w'),
        logging.StreamHandler()
    ]
)

class MyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix='!', intents=intents)
        self.db = GameStatsDatabase('data/game_stats.db')
        self.presence_data = {
            'r6s': {
                'game_name': 'Rainbow Six Siege',
                'maps': [
                    "Oregon",
                    "Clubhouse",
                    "Bank",
                    "Border",
                    "Coastline",
                    "Villa",
                    "Kafe Dostoyevsky",
                    "Chalet",
                    "Skyscraper",
                    "Theme Park",
                    "Tower",
                    "Favela",
                    "Yacht",
                    "House",
                    "Plane"
                ],
                'activities': [
                    "Ranked",
                    "Unranked",
                    "Casual",
                    "Terrorist Hunt",
                    "Training Grounds",
                    "Custom Game",
                    "Newcomer",
                    "Quick Match"
                ]
            },
            'bf6': {
                'game_name': 'Battlefield 6',
                'maps': [
                    "Siege of Cairo",
                    "Iberian Offensive",
                    "Liberation Peak",
                    "Empire State",
                    "Manhattan Bridge",
                    "Saints Quarter",
                    "New Sobek City",
                    "Mirak Valley",
                    "Operation Firestorm"
                ],
                'activities': [
                    "Conquest",
                    "Closed Weapon Conquest",
                    "Breakthrough",
                    "Domination",
                    "King of the Hill",
                    "Rush"
                ]
            },
            'statuses': [
                discord.Status.online,
                discord.Status.idle,
                discord.Status.dnd
            ]
        }
        
        self.current_game = random.choice(['r6s', 'bf6'])
        self.game_session_start = None
        self.min_session_hours = 2
        self.max_session_hours = 6
        self.current_session_duration = random.uniform(self.min_session_hours, self.max_session_hours)

    async def setup_hook(self) -> None:
        for filename in os.listdir('bot/cogs'):
            if filename.endswith('.py'):
                cog_name = filename[:-3]
                await bot.load_extension(f'bot.cogs.{cog_name}')    

    async def on_ready(self) -> None:
        print(f'Logged in as {self.user.name} (ID: {self.user.id})')
        await self.db.initialize_db()
        print("Database initialized")
        self.cycle_presence.start()
        print("Bot presence cycling started")

    @tasks.loop(minutes=20)
    async def cycle_presence(self):
        try:
            if self.game_session_start is None:
                self.game_session_start = discord.utils.utcnow()
            elapsed_hours = (discord.utils.utcnow() - self.game_session_start).total_seconds() / 3600
            
            if elapsed_hours >= self.current_session_duration:
                if random.random() < 0.7:
                    self.current_game = 'bf6' if self.current_game == 'r6s' else 'r6s'
                    self.game_session_start = discord.utils.utcnow()
                    self.current_session_duration = random.uniform(self.min_session_hours, self.max_session_hours)
                    print(f"Switched to {self.presence_data[self.current_game]['game_name']} for {self.current_session_duration:.1f} hours")
            
            game_data = self.presence_data[self.current_game]    
            map_name = random.choice(game_data['maps'])
            activity_type = random.choice(game_data['activities'])
            status = random.choice(self.presence_data['statuses'])
            state = f"{activity_type} - {map_name}"
            
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.playing,
                    name=game_data['game_name'],
                    state=state
                ),
                status=status
            )
            
            remaining_hours = self.current_session_duration - elapsed_hours
            print(f"Presence updated: {game_data['game_name']} - {state} (Status: {status.name}) | Session: {remaining_hours:.1f}h remaining")
        except Exception as e:
            print(f"Error updating presence: {e}")

    @cycle_presence.before_loop
    async def before_cycle_presence(self):
        await self.wait_until_ready()

bot = MyBot()

TOKEN = str(os.getenv('TOKEN'))

bot.run(TOKEN, log_level=logging.ERROR)