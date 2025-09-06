
from supabase import create_client, Client
import os
import json

class GameStatsDatabase:
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)

    async def initialize_db(self):
        print("Database connection established with Supabase")
        

    async def insert_or_update_stat(self, server_id, user_id, game_name, **stats):
        try:
            existing_result = self.supabase.table('game_stats').select('*').eq('server_id', server_id).eq('user_id', user_id).eq('game_name', game_name).execute()
            
            if existing_result.data:
                existing_stats = existing_result.data[0]
                updated_stats = {}
                
                stat_names = ['tournaments_played', 'tournaments_won', 'earnings', 'kills', 'deaths', 'wins', 'losses']
                for stat_name in stat_names:
                    if stat_name in stats:
                        updated_stats[stat_name] = existing_stats.get(stat_name, 0) + stats[stat_name]
                    else:
                        updated_stats[stat_name] = existing_stats.get(stat_name, 0)
                
                new_kills = updated_stats['kills']
                new_deaths = updated_stats['deaths']
                new_wins = updated_stats['wins']
                new_losses = updated_stats['losses']

                updated_stats['kd'] = new_kills / new_deaths if new_deaths > 0 else 0.0
                updated_stats['wl'] = new_wins / new_losses if new_losses > 0 else 0.0

                result = self.supabase.table('game_stats').update(updated_stats).eq('server_id', server_id).eq('user_id', user_id).eq('game_name', game_name).execute()
                
                return [updated_stats[key] for key in ['tournaments_played', 'tournaments_won', 'earnings', 'kills', 'deaths', 'kd', 'wins', 'losses', 'wl']]
            else:
                final_stats = {
                    'server_id': server_id,
                    'user_id': user_id,
                    'game_name': game_name,
                    'tournaments_played': stats.get('tournaments_played', 0),
                    'tournaments_won': stats.get('tournaments_won', 0),
                    'earnings': stats.get('earnings', 0),
                    'kills': stats.get('kills', 0),
                    'deaths': stats.get('deaths', 0),
                    'wins': stats.get('wins', 0),
                    'losses': stats.get('losses', 0)
                }
                
                final_stats['kd'] = final_stats['kills'] / final_stats['deaths'] if final_stats['deaths'] > 0 else 0.0
                final_stats['wl'] = final_stats['wins'] / final_stats['losses'] if final_stats['losses'] > 0 else 0.0

                result = self.supabase.table('game_stats').insert(final_stats).execute()
                
                return [final_stats[key] for key in ['tournaments_played', 'tournaments_won', 'earnings', 'kills', 'deaths', 'kd', 'wins', 'losses', 'wl']]
                
        except Exception as e:
            print(f"Error in insert_or_update_stat: {e}")
            raise

    async def get_stats(self, server_id, user_id=None, game_name=None, stat=None):
        try:
            query = self.supabase.table('game_stats').select('*').eq('server_id', server_id)
            
            if user_id is not None:
                query = query.eq('user_id', user_id)
            
            if game_name is not None:
                query = query.eq('game_name', game_name)
            
            result = query.execute()
            
            if not result.data:
                return None if user_id and game_name else []

            if user_id is None:
                processed_results = []
                for row in result.data:
                    if game_name is None:
                        processed_row = [row['user_id'], row['game_name']]
                    else:
                        processed_row = [row['user_id']]

                    stat_names = ['tournaments_played', 'tournaments_won', 'earnings', 'kills', 'deaths', 'kd', 'wins', 'losses', 'wl']
                    for stat_name in stat_names:
                        processed_row.append(row.get(stat_name, 0))
                    
                    processed_results.append(processed_row)
                return processed_results
            else:
                if game_name is None:
                    processed_results = []
                    for row in result.data:
                        processed_row = [row['game_name']]
                        stat_names = ['tournaments_played', 'tournaments_won', 'earnings', 'kills', 'deaths', 'kd', 'wins', 'losses', 'wl']
                        for stat_name in stat_names:
                            processed_row.append(row.get(stat_name, 0))
                        processed_results.append(processed_row)
                    return processed_results
                else:
                    row = result.data[0]
                    stat_names = ['tournaments_played', 'tournaments_won', 'earnings', 'kills', 'deaths', 'kd', 'wins', 'losses', 'wl']
                    return [row.get(stat_name, 0) for stat_name in stat_names]
                    
        except Exception as e:
            print(f"Error in get_stats: {e}")
            return None if user_id and game_name else []

    async def delete_stats(self, server_id, user_id, game_name):
        try:
            result = self.supabase.table('game_stats').delete().eq('server_id', server_id).eq('user_id', user_id).eq('game_name', game_name).execute()
        except Exception as e:
            print(f"Error in delete_stats: {e}")
            raise

    async def create_user_profile(self, server_id, user_id):
        try:
            existing_result = self.supabase.table('user_profiles').select('*').eq('server_id', server_id).eq('user_id', user_id).execute()
            
            if not existing_result.data:
                profile_data = {
                    'server_id': server_id,
                    'user_id': user_id,
                    'gaming_bio': '',
                    'main_game': 'r6s',
                    'social_links': '{}',
                    'embed_color': '0x00d4ff',
                    'timezone': 'UTC',
                    'team_affiliation': '',
                    'bf6_favorite_class': '',
                    'r6s_role': '',
                    'r6s_favorite_operator': ''
                }
                result = self.supabase.table('user_profiles').insert(profile_data).execute()
        except Exception as e:
            print(f"Error in create_user_profile: {e}")
            raise

    async def get_user_profile(self, server_id, user_id):
        try:
            result = self.supabase.table('user_profiles').select('gaming_bio, main_game, social_links, embed_color, timezone, team_affiliation, bf6_favorite_class, r6s_role, r6s_favorite_operator').eq('server_id', server_id).eq('user_id', user_id).execute()
            
            if result.data:
                row = result.data[0]
                return (
                    row.get('gaming_bio', ''),
                    row.get('main_game', 'r6s'),
                    row.get('social_links', '{}'),
                    row.get('embed_color', '0x00d4ff'),
                    row.get('timezone', 'UTC'),
                    row.get('team_affiliation', ''),
                    row.get('bf6_favorite_class', ''),
                    row.get('r6s_role', ''),
                    row.get('r6s_favorite_operator', '')
                )
            return None
        except Exception as e:
            print(f"Error in get_user_profile: {e}")
            return None

    async def update_user_profile(self, server_id, user_id, **profile_data):
        try:
            valid_fields = ['gaming_bio', 'main_game', 'social_links', 'embed_color', 'timezone', 'team_affiliation', 'bf6_favorite_class', 'r6s_role', 'r6s_favorite_operator']
            update_fields = {k: v for k, v in profile_data.items() if k in valid_fields}
            
            if update_fields:
                result = self.supabase.table('user_profiles').update(update_fields).eq('server_id', server_id).eq('user_id', user_id).execute()
        except Exception as e:
            print(f"Error in update_user_profile: {e}")
            raise

    async def delete_user_profile(self, server_id, user_id):
        try:
            result = self.supabase.table('user_profiles').delete().eq('server_id', server_id).eq('user_id', user_id).execute()
        except Exception as e:
            print(f"Error in delete_user_profile: {e}")
            raise

    async def player_left(self, server_id, user_id, user_name, display_name):
        try:
            existing_result = self.supabase.table('player_left').select('*').eq('server_id', server_id).eq('user_id', user_id).execute()
            
            if not existing_result.data:
                player_data = {
                    'server_id': server_id,
                    'user_id': user_id,
                    'user_name': user_name,
                    'display_name': display_name
                }
                result = self.supabase.table('player_left').insert(player_data).execute()
        except Exception as e:
            print(f"Error in player_left: {e}")
            raise

    async def get_player_left(self, server_id, user_id):
        try:
            result = self.supabase.table('player_left').select('user_name, display_name').eq('server_id', server_id).eq('user_id', user_id).execute()
            
            if result.data:
                row = result.data[0]
                return (row.get('user_name', ''), row.get('display_name', ''))
            return None
        except Exception as e:
            print(f"Error in get_player_left: {e}")
            return None

    async def delete_player_left(self, server_id, user_id):
        try:
            result = self.supabase.table('player_left').delete().eq('server_id', server_id).eq('user_id', user_id).execute()
        except Exception as e:
            print(f"Error in delete_player_left: {e}")
            raise

    async def get_server_players_left(self, server_id):
        try:
            result = self.supabase.table('player_left').select('user_id, user_name, display_name').eq('server_id', server_id).execute()
            
            processed_results = []
            for row in result.data:
                processed_results.append((
                    row.get('user_id', ''),
                    row.get('user_name', ''),
                    row.get('display_name', '')
                ))
            return processed_results
        except Exception as e:
            print(f"Error in get_server_players_left: {e}")
            return []