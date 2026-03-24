#
# This file contains functions that have been removed from the bot, to potentially be put back, but not 100% guaranteed
#



# discord.on_voice_state_update(member, before, after)
# VoiceState -> channel -> VoiceChannel
# check if before <> after
# then output to tannoy (with notification?)
@bot.event
async def on_voice_state_update(member, before, after):
	server = member.guild
	logchannel = get_log_channel(server)
	
	try:
		log_voice_channel = get_bot_setting("voice-activity", server.name)
	except Exception as e:
		log.error(e)
	
	aftername = ""
	beforename = ""
	if after.channel is not None:
		aftername = after.channel.name
	if before.channel is not None:
		beforename = before.channel.name
		
	if log_voice_channel == "on":
		if aftername != beforename:
			if beforename == "":
				await logchannel.send("{} has entered the {} channel".format(member.display_name, after.channel.name))
			elif aftername == "":
				await logchannel.send("{} has left the {} channel".format(member.display_name, before.channel.name))
			else:
				await logchannel.send("{} has moved from the {} to the {} channel.".format(member.display_name, before.channel.name, after.channel.name))

