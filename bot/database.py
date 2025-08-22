import aiosqlite

class GameStatsDatabase:
    def __init__(self, db_file):
        self.db_file = db_file

    async def initialize_db(self):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS game_stats (
                    id INTEGER PRIMARY KEY,
                    server_id TEXT,
                    user_id TEXT,
                    game_name TEXT,
                    tournaments_played INTEGER DEFAULT 0,
                    earnings INTEGER DEFAULT 0,
                    kills INTEGER DEFAULT 0,
                    deaths INTEGER DEFAULT 0,
                    kd REAL DEFAULT 0.0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    wl REAL DEFAULT 0.0,
                    UNIQUE(server_id, user_id, game_name)
                )
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_stats_lookup 
                ON game_stats(server_id, user_id, game_name)
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY,
                    server_id TEXT,
                    user_id TEXT,
                    gaming_bio TEXT DEFAULT '',
                    main_game  TEXT DEFAULT 'r6s',
                    social_links TEXT DEFAULT '{}',
                    embed_color TEXT DEFAULT '0x00d4ff',
                    timezone TEXT DEFAULT 'UTC',
                    team_affiliation TEXT DEFAULT '',
                    UNIQUE(server_id, user_id)
                )
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_profile_lookup 
                ON user_profiles(server_id, user_id)
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS player_left (
                user_id INTEGER PRIMARY KEY,
                server_id INTEGER,
                user_name TEXT,
                display_name TEXT,
                UNIQUE(server_id, user_id)
                )
            ''')
            await db.commit()

    async def insert_or_update_stat(self, server_id, user_id, game_name, **stats):
        async with aiosqlite.connect(self.db_file) as db:
            existing_stats = await self.get_stats(server_id, user_id, game_name)

            if existing_stats:
                updated_stats = {}
                stat_names = ['tournaments_played', 'earnings', 'kills', 'deaths', 'kd', 'wins', 'losses', 'wl']
                for i, stat_name in enumerate(stat_names):
                    if stat_name not in ['kd', 'wl']:
                        if stat_name in stats:
                            updated_stats[stat_name] = existing_stats[i] + stats[stat_name]
                        else:
                            updated_stats[stat_name] = existing_stats[i]
                new_kills = updated_stats['kills']
                new_deaths = updated_stats['deaths']
                new_wins = updated_stats['wins']
                new_losses = updated_stats['losses']

                updated_stats['kd'] = new_kills / new_deaths if new_deaths > 0 else 0.0
                updated_stats['wl'] = new_wins / new_losses if new_losses > 0 else 0.0

                placeholders = ', '.join([f'{key} = ?' for key in updated_stats.keys()])
                update_values = list(updated_stats.values())
                await db.execute(f'''
                    UPDATE game_stats SET {placeholders}
                    WHERE server_id = ? AND user_id = ? AND game_name = ?
                ''', update_values + [server_id, user_id, game_name])

                final_stats = list(updated_stats.values())
            else:
                final_stats = {}
                final_stats['tournaments_played'] = stats.get('tournaments_played', 0)
                final_stats['earnings'] = stats.get('earnings', 0)
                final_stats['kills'] = stats.get('kills', 0)
                final_stats['deaths'] = stats.get('deaths', 0)
                final_stats['kd'] = final_stats['kills'] / final_stats['deaths'] if final_stats['deaths'] > 0 else 0.0
                final_stats['wins'] = stats.get('wins', 0)
                final_stats['losses'] = stats.get('losses', 0)
                final_stats['wl'] = final_stats['wins'] / final_stats['losses'] if final_stats['losses'] > 0 else 0.0

                await db.execute('''
                    INSERT INTO game_stats (server_id, user_id, game_name, tournaments_played, earnings, kills, deaths, kd, wins, losses, wl)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', [server_id, user_id, game_name] + list(final_stats.values()))

                final_stats = list(final_stats.values())

            await db.commit()
            return final_stats

    async def get_stats(self, server_id, user_id=None, game_name=None, stat=None):
        async with aiosqlite.connect(self.db_file) as db:
            available_stats = {
                'tournaments_played': 'tournaments_played',
                'earnings': 'earnings', 
                'kills': 'kills',
                'deaths': 'deaths',
                'kd': 'kd',
                'wins': 'wins',
                'losses': 'losses',
                'wl': 'wl'
            }
            if user_id is None:
                base_columns = "user_id, game_name, tournaments_played, earnings, kills, deaths, kd, wins, losses, wl"
            else:
                if game_name is None:
                    base_columns = "game_name, tournaments_played, earnings, kills, deaths, kd, wins, losses, wl"
                else:
                    base_columns = "tournaments_played, earnings, kills, deaths, kd, wins, losses, wl"
            if stat is not None:
                if isinstance(stat, str):
                    stats_to_select = [stat] if stat in available_stats else []
                elif isinstance(stat, list):
                    stats_to_select = [s for s in stat if s in available_stats]
                else:
                    stats_to_select = []

                if not stats_to_select:
                    return None

                if user_id is None:
                    selected_cols = [available_stats[s] for s in stats_to_select]
                    base_columns = "user_id, game_name, " + ", ".join(selected_cols)
                else:
                    selected_cols = [available_stats[s] for s in stats_to_select]
                    if game_name is None:
                         base_columns = "game_name, " + ", ".join(selected_cols)
                    else:
                         base_columns = ", ".join(selected_cols)
            if user_id is None:
                if game_name is None:
                    query = f'''
                        SELECT {base_columns}
                        FROM game_stats
                        WHERE server_id = ?
                    '''
                    params = (server_id,)
                else:
                    query = f'''
                        SELECT {base_columns}
                        FROM game_stats
                        WHERE server_id = ? AND game_name = ?
                    '''
                    params = (server_id, game_name)

                async with db.execute(query, params) as cursor:
                    return await cursor.fetchall()
            else:
                if game_name is None:
                    query = f'''
                        SELECT {base_columns}
                        FROM game_stats
                        WHERE server_id = ? AND user_id = ?
                    '''
                    params = (server_id, user_id)

                    async with db.execute(query, params) as cursor:
                        return await cursor.fetchall()
                else:
                    query = f'''
                        SELECT {base_columns}
                        FROM game_stats
                        WHERE server_id = ? AND user_id = ? AND game_name = ?
                    '''
                    params = (server_id, user_id, game_name)

                    async with db.execute(query, params) as cursor:
                        return await cursor.fetchone()

    async def delete_stats(self, server_id, user_id, game_name):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute('''
                DELETE FROM game_stats WHERE server_id = ? AND user_id = ? AND game_name = ?
            ''', (server_id, user_id, game_name))
            await db.commit()

    async def create_user_profile(self, server_id, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute('''
                INSERT OR IGNORE INTO user_profiles 
                (server_id, user_id, gaming_bio, main_game, social_links, embed_color, timezone, team_affiliation)
                VALUES (?, ?, '', 'r6s', '{}', '0x00d4ff', 'UTC', '')
            ''', (server_id, user_id))
            await db.commit()

    async def get_user_profile(self, server_id, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute('''
                SELECT gaming_bio, main_game, social_links, embed_color, timezone, team_affiliation
                FROM user_profiles WHERE server_id = ? AND user_id = ?
            ''', (server_id, user_id)) as cursor:
                return await cursor.fetchone()

    async def update_user_profile(self, server_id, user_id, **profile_data):
        async with aiosqlite.connect(self.db_file) as db:
            valid_fields = ['gaming_bio', 'main_game', 'social_links', 'embed_color', 'timezone', 'team_affiliation']
            update_fields = {k: v for k, v in profile_data.items() if k in valid_fields}
            
            if not update_fields:
                return
            
            placeholders = ', '.join([f'{key} = ?' for key in update_fields.keys()])
            update_values = list(update_fields.values())
            
            await db.execute(f'''
                UPDATE user_profiles SET {placeholders}
                WHERE server_id = ? AND user_id = ?
            ''', update_values + [server_id, user_id])
            await db.commit()

    async def delete_user_profile(self, server_id, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute('''
                DELETE FROM user_profiles WHERE server_id = ? AND user_id = ?
            ''', (server_id, user_id))
            await db.commit()

    async def player_left(self, server_id, user_id, user_name, display_name):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute('''
                INSERT OR IGNORE INTO player_left (server_id, user_id, user_name, display_name)
                VALUES (?, ?, ?, ?)
            ''', (server_id, user_id, user_name, display_name))
            await db.commit()

    async def get_player_left(self, server_id, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute('''
                SELECT user_name, display_name
                FROM player_left WHERE server_id = ? AND user_id = ?
            ''', (server_id, user_id)) as cursor:
                return await cursor.fetchone()

    async def delete_player_left(self, server_id, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute('''
                DELETE FROM player_left WHERE server_id = ? AND user_id = ?
            ''', (server_id, user_id))
            await db.commit()

    async def get_server_players_left(self, server_id):
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute('''
                SELECT user_id, user_name, display_name
                FROM player_left WHERE server_id = ?
            ''', (server_id,)) as cursor:
                return await cursor.fetchall()