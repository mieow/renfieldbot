CREATE TABLE events (
	id INT AUTO_INCREMENT PRIMARY KEY,
	name TEXT,
	server TEXT,
	eventdate DATETIME
);

CREATE TABLE attendance (
	id INT AUTO_INCREMENT PRIMARY KEY,
	member_id INT,
	event_id INT,
	displayname TEXT
);

CREATE TABLE members (
	member_id INT AUTO_INCREMENT PRIMARY KEY,
	name TEXT,
	wordpress_id TEXT,
	playername TEXT
);

CREATE TABLE niceness (
	id INT AUTO_INCREMENT PRIMARY KEY,
	compliment TEXT,
	server TEXT
);

CREATE TABLE logging (
	id INT AUTO_INCREMENT PRIMARY KEY,
	active TINYINT(1),
	linecount INT,
	filename TEXT,
	channel_id TEXT,
	server TEXT
);

CREATE TABLE linearsettings (
	id INT AUTO_INCREMENT PRIMARY KEY,
	name TEXT,
	setting_name TEXT,
	setting_level INT,
	server TEXT
);

CREATE TABLE serversettings (
	id INT AUTO_INCREMENT PRIMARY KEY,
	setting_name TEXT,
	setting_value TEXT,
	server TEXT
);

CREATE TABLE wp_link (
	id INT AUTO_INCREMENT PRIMARY KEY,
	server TEXT,
	name TEXT,
	wordpress_id TEXT,
	secret TEXT
);

