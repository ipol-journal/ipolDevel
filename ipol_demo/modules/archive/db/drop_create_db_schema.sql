PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS experiments (
                            id	INTEGER PRIMARY KEY AUTOINCREMENT,
                            id_demo	INTEGER NOT NULL,
                            params	TEXT,
                            execution	TEXT,
                            timestamp	TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS blobs (
                            id	INTEGER PRIMARY KEY AUTOINCREMENT,
                            hash	TEXT NOT NULL,
                            type	TEXT NOT NULL,
                            format	TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS correspondence (
                            id	INTEGER PRIMARY KEY AUTOINCREMENT,
                            id_experiment	INTEGER NOT NULL,
                            id_blob	INTEGER NOT NULL,
                            name	TEXT,
                            order_exp INTEGER,
                            FOREIGN KEY(`id_experiment`) REFERENCES experiments ( id ) ON DELETE CASCADE,
                            FOREIGN KEY(`id_blob`) REFERENCES blobs ( id ) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS correspondence_id_experiment ON correspondence (id_experiment);
