
import asyncio
import aiosqlite
import json

async def export_sqlite_data():
    """Export existing SQLite data to JSON files for manual import to Supabase"""
    
    # Connect to existing SQLite database
    async with aiosqlite.connect('data/game_stats.db') as db:
        
        # Export game_stats table
        async with db.execute('SELECT * FROM game_stats') as cursor:
            game_stats = await cursor.fetchall()
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Convert to list of dictionaries
            game_stats_data = []
            for row in game_stats:
                game_stats_data.append(dict(zip(columns, row)))
        
        # Export user_profiles table
        try:
            async with db.execute('SELECT * FROM user_profiles') as cursor:
                user_profiles = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                user_profiles_data = []
                for row in user_profiles:
                    user_profiles_data.append(dict(zip(columns, row)))
        except:
            user_profiles_data = []
        
        # Export player_left table
        try:
            async with db.execute('SELECT * FROM player_left') as cursor:
                player_left = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                player_left_data = []
                for row in player_left:
                    player_left_data.append(dict(zip(columns, row)))
        except:
            player_left_data = []
    
    # Save to JSON files
    with open('game_stats_export.json', 'w') as f:
        json.dump(game_stats_data, f, indent=2)
    
    with open('user_profiles_export.json', 'w') as f:
        json.dump(user_profiles_data, f, indent=2)
    
    with open('player_left_export.json', 'w') as f:
        json.dump(player_left_data, f, indent=2)
    
    print(f"Exported {len(game_stats_data)} game stats records")
    print(f"Exported {len(user_profiles_data)} user profiles records")
    print(f"Exported {len(player_left_data)} player left records")
    print("Data exported to JSON files. You can now import this data into your Supabase database.")

if __name__ == "__main__":
    asyncio.run(export_sqlite_data())
