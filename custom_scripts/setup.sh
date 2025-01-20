#!/usr/bin/env bash

rootpass="widurncourygb"
renfieldpass="awdivuyhaefvyer"
discord_token="your_discord_token"
guild_name="your_discord_guild_name"
guild_id="your_discord_guild_id"

yum update

yum install -y libcurl-devel
yum install -y gcc
yum install -y openssl-devel
yum install -y python3-devel
yum install -y opus
yum install -y python3-pip

cd /usr/local/bin
mkdir ffmpeg && cd ffmpeg
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz


adduser renfield
su - renfield -c "mkdir .ssh && chmod 700 .ssh"
su - renfield -c "touch .ssh/authorized_keys"
su - renfield -c "chmod 600 .ssh/authorized_keys"

cat ~/.ssh/authorized_keys >> /home/renfield/.ssh/authorized_keys

curl -LsS -O https://downloads.mariadb.com/MariaDB/mariadb_repo_setup
bash mariadb_repo_setup --os-type=rhel  --os-version=9 --skip-check-installed
rm -rf /var/cache/yum
yum makecache

yum install -y MariaDB-server MariaDB-client

systemctl enable --now mariadb

mariadb -u root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '${rootpass}';
CREATE USER 'renfield'@'localhost' IDENTIFIED BY '${renfieldpass}';
FLUSH PRIVILEGES;
EOF

mariadb -u root -p${rootpass} < /tmp/renfieldbot-master/scripts/setupdatabase.sql
mariadb -u renfield -p${renfieldpass} discordbot < /tmp/renfieldbot-master/scripts/createtables.sql

su - renfield -c "/tmp/renfieldbot-master/scripts/renfield-setup.sh"

cat <<EOF > env.txt
DISCORD_TOKEN=${discord_token}
DISCORD_GUILD="${guild_name}"
DISCORD_GUILD_ID=${guild_id}
DATABASE_USERNAME="renfield"
DATABASE_PASSWORD="${renfieldpass}"
LOG_HOME="/home/renfield/logs"
OWNER=581081113263472643
POLLY_WORD_LIMIT=1000000

DEFAULT_ADMIN_ROLE="Storytellers"
DEFAULT_WORDPRESS_SITE="none"
DEFAULT_POLLY_VOICE="Brian"
DEFAULT_VOICE-ACTIVITY="off"
DEFAULT_CUBBY-HOLE="renfields-cubby-hole"
DEFAULT_EVENT_START="18:00"
DEFAULT_EVENT_END="23:00"
DEFAULT_EVENT_DESC="[No description]"
DEFAULT_LOCATION="[No location]"
EOF

cp env.txt /home/renfield/.env
chown renfield /home/renfield/.env


cp /tmp/renfieldbot-master/scripts/renfield.service /etc/systemd/system
systemctl enable renfield

echo "Setup Complete"
