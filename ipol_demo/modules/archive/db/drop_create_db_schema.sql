PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS experiments(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            id_demo INTEGER NULL,
                            params TEXT NULL,
                            timestamp TIMESTAMP
                            DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS blobs(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            hash TEXT NULL,
                            type TEXT NULL,
                            format TEXT NULL);
CREATE TABLE IF NOT EXISTS correspondence(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            id_experiment INTEGER NULL,
                            id_blob INTEGER NULL,
                            name TEXT NULL,
                            FOREIGN KEY(id_experiment) REFERENCES experiments(id)
                            ON DELETE CASCADE);

