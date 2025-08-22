from discord.ext import commands

game_list = ['r6s', 'bf6']

class DatabaseInitializationCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = bot.db
        print(f"DatabaseInitializationCog loaded")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Starting database initialization for all existing users...")
        
        for guild in self.bot.guilds:
            print(f"Initializing database for guild: {guild.name} (ID: {guild.id})")
            
            for member in guild.members:
                if member.bot:
                    continue
                
                try:
                    existing_profile = await self.db.get_user_profile(str(guild.id), str(member.id))
                    
                    if not existing_profile:
                        await self.db.create_user_profile(str(guild.id), str(member.id))
                        print(f"Created profile for {member.name} in {guild.name}")
                    else:
                        print(f"Profile already exists for {member.name} in {guild.name}")
                    
                    for game in game_list:
                        existing_stats = await self.db.get_stats(str(guild.id), str(member.id), game)
                        
                        if not existing_stats:
                            await self.db.insert_or_update_stat(
                                str(guild.id),
                                str(member.id),
                                game,
                                tournaments_played=0,
                                earnings=0,
                                kills=0,
                                deaths=0,
                                wins=0,
                                losses=0
                            )
                            print(f"Created {game} stats for {member.name} in {guild.name}")
                        else:
                            print(f"{game} stats already exist for {member.name} in {guild.name}")
                    
                except Exception as e:
                    print(f"Error initializing database for {member.name} in {guild.name}: {e}")
            
            print(f"Completed database initialization for guild: {guild.name}")
        
        print("Database initialization completed for all existing users")

async def setup(bot) -> None:
    await bot.add_cog(DatabaseInitializationCog(bot))