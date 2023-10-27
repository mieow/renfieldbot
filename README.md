# renfieldbot

## About Renfield


## Setting up on AWS

### Migration

If you are migrating the bot to another server instance, you should first take a download of the existing database.

> renfield> mariadb-dump discordbot -p > /tmp/dump.sql

Also take a download of the encryption key, or everyone will need to re-link their characters again.

> renfield> ls /home/renfield/.wp_key

### Launch instance

https://aws.amazon.com/free/

1. Log in to console.aws.amazon.com
1. Select EC2 service
1. Click "Launch Instance"
1. Name: Renfield
1. Quick Start:
1.1 amazon Linux 2023, 64bit (x86) (free tier)
1.1 t2.micro (free tier)
1.1 Create new key pair
1.1 Allow SSH from... My IP
1.1 Advanced details - create an IAM profile with access to PollyVoice
1. [ review and launch ]
1. Launch

### Allocate Elastic IP address

This is optional, but means you don't have to change the connection IP address every time to reboot the instance.

1. EC2 -> Elastic IPs
1. [Allocate Elastic IP address]

### create an IAM role with polly access

This is so that you can use the /speak command

### Update and install OS packages

Log on with SSH to instance as ec2-user, with key pair

https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/putty.html


Upload scripts to /tmp

> ec2-user> sudo -i
> root> cd /tmp
> root> wget https://github.com/mieow/renfieldbot/archive/refs/heads/master.zip
> root> unzip master.zip
> root> cd /tmp/renfieldbot-master/scripts/
> root> chmod u+x setup.sh
> root> chmod a+x renfield-setup.sh

If migrating, replace the createtables.sql file with the database dump.

> root> cd /tmp/renfieldbot-master/scripts/
> root> mv createtables.sql createtables.sql.bak
> root> mv /tmp/dump.sql createtables.sql

Edit the setup script with the database passwords and Discord information you want to use:

rootpass="widurncourygb"
renfieldpass="awdivuyhaefvyer"
discord_token="your_discord_token"
guild_name="your_discord_guild_name"
guild_id="your_discord_guild_id"

> root> vi setup.sh

Run the setup script:

> root> ./setup.sh


### Final setup

Edit the /home/renfield/.env file with your discord bot information

Edit the /home/renfield/.aws/credentials file with your aws polly credentials

Migrations: upload the encryption key to /home/renfield/.wp_key

systemctl start renfield
systemctl status renfield

# Invite the bot to your server

https://discord.com/api/oauth2/authorize?client_id=690906493742088242&permissions=1099511630848&scope=bot%20applications.commands
add manage roles
add speak permission

# Useful pages:

https://docs.aws.amazon.com/polly/latest/dg/get-started-what-next.html
https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
https://docs.aws.amazon.com/polly/latest/dg/API_SynthesizeSpeech.html
https://docs.python.org/3/library/tempfile.html

