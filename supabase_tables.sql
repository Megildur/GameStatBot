
-- Create game_stats table
CREATE TABLE game_stats (
    id BIGSERIAL PRIMARY KEY,
    server_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    game_name TEXT NOT NULL,
    tournaments_played INTEGER DEFAULT 0,
    tournaments_won INTEGER DEFAULT 0,
    earnings INTEGER DEFAULT 0,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    kd REAL DEFAULT 0.0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    wl REAL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(server_id, user_id, game_name)
);

-- Create user_profiles table
CREATE TABLE user_profiles (
    id BIGSERIAL PRIMARY KEY,
    server_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    gaming_bio TEXT DEFAULT '',
    main_game TEXT DEFAULT 'r6s',
    social_links TEXT DEFAULT '{}',
    embed_color TEXT DEFAULT '0x00d4ff',
    timezone TEXT DEFAULT 'UTC',
    team_affiliation TEXT DEFAULT '',
    bf6_favorite_class TEXT DEFAULT '',
    r6s_role TEXT DEFAULT '',
    r6s_favorite_operator TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(server_id, user_id)
);

-- Create player_left table
CREATE TABLE player_left (
    user_id BIGINT PRIMARY KEY,
    server_id BIGINT NOT NULL,
    user_name TEXT,
    display_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(server_id, user_id)
);

-- Create indexes for better performance
CREATE INDEX idx_game_stats_lookup ON game_stats(server_id, user_id, game_name);
CREATE INDEX idx_user_profiles_lookup ON user_profiles(server_id, user_id);
CREATE INDEX idx_player_left_server ON player_left(server_id);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE game_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_left ENABLE ROW LEVEL SECURITY;

-- Create policies to allow all operations (you can make these more restrictive)
CREATE POLICY "Allow all operations on game_stats" ON game_stats FOR ALL USING (true);
CREATE POLICY "Allow all operations on user_profiles" ON user_profiles FOR ALL USING (true);
CREATE POLICY "Allow all operations on player_left" ON player_left FOR ALL USING (true);
