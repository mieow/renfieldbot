#!/usr/bin/env bash


yum update

yum install -y libcurl-devel
yum install -y gcc
yum install -y openssl-devel
yum install -y python3-devel
yum install -y opus
yum install python3-pip

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

su - renfield -c "/tmp/renfield-setup.sh"

