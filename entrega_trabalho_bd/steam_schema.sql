PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS game_tags;
DROP TABLE IF EXISTS game_genres;
DROP TABLE IF EXISTS game_categories;
DROP TABLE IF EXISTS game_platforms;
DROP TABLE IF EXISTS game_developers;
DROP TABLE IF EXISTS game_publishers;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS platforms;
DROP TABLE IF EXISTS developers;
DROP TABLE IF EXISTS publishers;
DROP TABLE IF EXISTS games;

CREATE TABLE games (
    game_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    release_date TEXT,
    price_usd REAL,
    owners_lower INTEGER,
    owners_upper INTEGER,
    peak_ccu INTEGER,
    positive_reviews INTEGER,
    negative_reviews INTEGER,
    recommendations INTEGER,
    avg_playtime_minutes INTEGER,
    metacritic_score INTEGER
);

CREATE TABLE developers (
    developer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE publishers (
    publisher_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE genres (
    genre_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE tags (
    tag_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE platforms (
    platform_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE game_developers (
    game_id INTEGER NOT NULL,
    developer_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, developer_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (developer_id) REFERENCES developers(developer_id) ON DELETE CASCADE
);

CREATE TABLE game_publishers (
    game_id INTEGER NOT NULL,
    publisher_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, publisher_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id) ON DELETE CASCADE
);

CREATE TABLE game_genres (
    game_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, genre_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
);

CREATE TABLE game_categories (
    game_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, category_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);

CREATE TABLE game_tags (
    game_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, tag_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
);

CREATE TABLE game_platforms (
    game_id INTEGER NOT NULL,
    platform_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, platform_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id) ON DELETE CASCADE
);

CREATE INDEX idx_games_name ON games(name);
CREATE INDEX idx_games_release_date ON games(release_date);
CREATE INDEX idx_game_developers_developer ON game_developers(developer_id);
CREATE INDEX idx_game_publishers_publisher ON game_publishers(publisher_id);
CREATE INDEX idx_game_genres_genre ON game_genres(genre_id);
CREATE INDEX idx_game_categories_category ON game_categories(category_id);
CREATE INDEX idx_game_tags_tag ON game_tags(tag_id);
CREATE INDEX idx_game_platforms_platform ON game_platforms(platform_id);
