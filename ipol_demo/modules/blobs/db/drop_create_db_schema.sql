PRAGMA foreign_keys=ON;

CREATE TABLE "blobs" (
	'id'	INTEGER PRIMARY KEY AUTOINCREMENT,
	'hash'	VARCHAR(70) NOT NULL UNIQUE,
	'format'	VARCHAR(30),
	'extension'	VARCHAR(30),
	'credit'	LONGTEXT
);
CREATE TABLE "demos" (
        'id' INTEGER PRIMARY KEY AUTOINCREMENT,
        'editor_demo_id' INTEGER NOT NULL UNIQUE
);
CREATE TABLE "demos_blobs" (
        'id' INTEGER PRIMARY KEY AUTOINCREMENT,
        'demo_id' INTEGER NOT NULL,
        'blob_id' INTEGER NOT NULL,
        'blob_set' VARCHAR (70) DEFAULT NULL,
        'pos_in_set' INTEGER,
        'blob_title'	VARCHAR(255),
	'set_order' INTEGER,
        FOREIGN KEY('demo_id') REFERENCES "demos"('id') ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY('blob_id') REFERENCES "blobs"('id') ON DELETE CASCADE ON UPDATE CASCADE,
        UNIQUE('demo_id','blob_set','pos_in_set', 'set_order')
);
CREATE TABLE "demos_templates" (
        'id' INTEGER PRIMARY KEY AUTOINCREMENT,
        'demo_id' INTEGER NOT NULL,
        'template_id' INTEGER NOT NULL,
        FOREIGN KEY('demo_id') REFERENCES "demos"('id') ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY('template_id') REFERENCES "templates"('id') ON DELETE CASCADE ON UPDATE CASCADE
        UNIQUE('demo_id', 'template_id')
);
CREATE TABLE "templates" (
        'id' INTEGER PRIMARY KEY AUTOINCREMENT,
        'name' VARCHAR (70) NOT NULL UNIQUE
);
CREATE TABLE "templates_blobs" (
        'id' INTEGER PRIMARY KEY AUTOINCREMENT,
        'template_id' INTEGER NOT NULL,
        'blob_id' INTEGER NOT NULL,
        'blob_set' VARCHAR (70) DEFAULT NULL,
        'pos_in_set' INTEGER,
        'blob_title'	VARCHAR(255),
	'set_order' INTEGER,
        FOREIGN KEY('template_id') REFERENCES "templates"('id') ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY('blob_id') REFERENCES "blobs"('id') ON DELETE CASCADE ON UPDATE CASCADE,
        UNIQUE('template_id','blob_set','pos_in_set', 'set_order')
);
