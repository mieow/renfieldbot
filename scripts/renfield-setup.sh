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

cd
mkdir logs
cp -r /tmp/renfieldbot-master/discord .
