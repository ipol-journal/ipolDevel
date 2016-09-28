CREATE TABLE "demo" (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`name`	VARCHAR(30),
	`is_template`	BOOLEAN DEFAULT 0,
	`template_id`	INTEGER DEFAULT 0
);
CREATE TABLE "blob" (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`hash`	VARCHAR(70),
	`format`	VARCHAR(30),
	`extension`	VARCHAR(30) DEFAULT '.png',
	`title`	VARCHAR(255),
	`credit`	LONGTEXT
);
CREATE TABLE "tag" (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`name`	VARCHAR(70)
);
CREATE TABLE  "blob_tag" (
	`blob_id`	INTEGER NOT NULL,
	`tag_id`	INTEGER NOT NULL,
	PRIMARY KEY(blob_id,tag_id),
	FOREIGN KEY(`blob_id`) REFERENCES "blob" ( `id` ) ON DELETE CASCADE ON UPDATE RESTRICT,
	FOREIGN KEY(`tag_id`) REFERENCES "tag" ( `id` ) ON DELETE CASCADE ON UPDATE RESTRICT
);
CREATE INDEX `fk_blob_has_tag_tag1_idx` ON `blob_tag` (`tag_id` ASC);
CREATE INDEX `fk_blob_has_tag_blob1_idx` ON `blob_tag` (`blob_id` ASC);
CREATE TABLE CREATE TABLE "demo_blob" (
	`blob_id`	INTEGER NOT NULL,
	`demo_id`	INTEGER NOT NULL,
	`blob_set`	VARCHAR(70) DEFAULT NULL,
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	`blob_pos_in_set`	INTEGER,
	FOREIGN KEY(`blob_id`) REFERENCES "blob" ( `id` ) ON DELETE CASCADE ON UPDATE RESTRICT,
	FOREIGN KEY(`demo_id`) REFERENCES "demo" ( `id` ) ON DELETE CASCADE ON UPDATE RESTRICT
);
CREATE INDEX fk_blob_has_demo_demo1_idx ON demo_blob (demo_id ASC);
CREATE INDEX fk_blob_has_demo_blob1_idx ON demo_blob (blob_id ASC);
