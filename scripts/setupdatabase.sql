
# Kill the anonymous users
DELETE FROM mysql.user WHERE User='';
# disallow remote login for root
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
# Kill off the demo database
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
# Make our changes take effect
FLUSH PRIVILEGES;

CREATE DATABASE discordbot;
GRANT ALL PRIVILEGES ON *.* TO 'renfield'@'localhost';
SHOW GRANTS FOR 'renfield'@'localhost';
