#!/usr/bin/env bash

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade setuptools
python3 -m pip install --upgrade discord
python3 -m pip install --upgrade discord.py
python3 -m pip install --upgrade mysql-connector-python
python3 -m pip install --upgrade tabulate
python3 -m pip install --upgrade python-dotenv
python3 -m pip install --upgrade discord-py-interactions
python3 -m pip install --upgrade discord-py-slash-command
python3 -m pip install --upgrade certifi
python3 -m pip install --upgrade cryptography
python3 -m pip install --upgrade boto3
python3 -m pip install --upgrade opuslib
python3 -m pip install --upgrade discord.py[voice]
python3 -m pip install --upgrade pycurl
python3 -m pip install --upgrade pytz
python3 -m pip install --upgrade awscli

cd
mkdir logs
cp -r /tmp/renfieldbot-master/discord .

chmod u+x discord/bot.py

mkdir /home/renfield/.aws
cat <<EOF > /home/renfield/.aws/config
[default]
region=us-east-1
EOF
cat <<EOF > /home/renfield/.aws/credentials
[default]
aws_access_key_id = 
aws_secret_access_key = 
EOF