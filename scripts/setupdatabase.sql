CREATE USER 'renfield'@'localhost' IDENTIFIED BY 'your_password_here';
CREATE DATABASE discordbot;
GRANT ALL PRIVILEGES ON *.* TO 'renfield'@'localhost';
SHOW GRANTS FOR 'renfield'@'localhost';
