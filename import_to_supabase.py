
import asyncio
import json
import os
from supabase import create_client, Client

async def import_to_supabase():
    """Import exported JSON data to Supabase"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Connected to Supabase")
    
    # Import game_stats
    try:
        with open('game_stats_export.json', 'r') as f:
            game_stats_data = json.load(f)
        
        print(f"Importing {len(game_stats_data)} game stats records...")
        
        # Import in batches to avoid rate limits
        batch_size = 50
        for i in range(0, len(game_stats_data), batch_size):
            batch = game_stats_data[i:i + batch_size]
            
            # Remove the 'id' field if it exists to let Supabase auto-generate it
            for record in batch:
                record.pop('id', None)
            
            result = supabase.table('game_stats').insert(batch).execute()
            print(f"Imported batch {i//batch_size + 1} of game stats")
        
        print("✓ Game stats imported successfully")
        
    except FileNotFoundError:
        print("game_stats_export.json not found, skipping game stats import")
    except Exception as e:
        print(f"Error importing game stats: {e}")
    
    # Import user_profiles
    try:
        with open('user_profiles_export.json', 'r') as f:
            user_profiles_data = json.load(f)
        
        if user_profiles_data:
            print(f"Importing {len(user_profiles_data)} user profile records...")
            
            batch_size = 50
            for i in range(0, len(user_profiles_data), batch_size):
                batch = user_profiles_data[i:i + batch_size]
                
                # Remove the 'id' field if it exists
                for record in batch:
                    record.pop('id', None)
                
                result = supabase.table('user_profiles').insert(batch).execute()
                print(f"Imported batch {i//batch_size + 1} of user profiles")
            
            print("✓ User profiles imported successfully")
        else:
            print("No user profiles data to import")
            
    except FileNotFoundError:
        print("user_profiles_export.json not found, skipping user profiles import")
    except Exception as e:
        print(f"Error importing user profiles: {e}")
    
    # Import player_left
    try:
        with open('player_left_export.json', 'r') as f:
            player_left_data = json.load(f)
        
        if player_left_data:
            print(f"Importing {len(player_left_data)} player left records...")
            
            batch_size = 50
            for i in range(0, len(player_left_data), batch_size):
                batch = player_left_data[i:i + batch_size]
                
                result = supabase.table('player_left').insert(batch).execute()
                print(f"Imported batch {i//batch_size + 1} of player left records")
            
            print("✓ Player left records imported successfully")
        else:
            print("No player left data to import")
            
    except FileNotFoundError:
        print("player_left_export.json not found, skipping player left import")
    except Exception as e:
        print(f"Error importing player left records: {e}")
    
    print("\n🎉 Import completed!")

if __name__ == "__main__":
    asyncio.run(import_to_supabase())
