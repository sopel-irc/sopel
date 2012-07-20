#!/usr/bin/env python
"""
ChanBL.py - Individual Channel Blacklists Module
Copyright 2012, Lior Ramati
Licensed under the Eiffel Forum License 2.

More info:
* Willie: https://github.com/embolalia/jenni/
* Jenni: https://github.com/myano/jenni/
* Phenny: http://inamidst.com/phenny/
"""

## predefine a blacklist channel by channel, or add an empty dictionary if user 
## doesnt want to define blacklists
def configure(config):
	config.set_attr("chan_bls", dict())
	if (config.option("Do you want to blacklist commands from specific channels")):
		for channel in config.channels:
			add_list("_chanbls_temp", "What commands (NOT modules) would you like to block for " + str(channel), "command:")
			config.chan_bls[channel] = set(config._chanbls_temp)
	else: 
		for channel in config.channels: 
			config.chan_bls[channel] = set()
	string = "\nchan_bls = " + str(config.chan_bls) +'\n'
	return string

## add a command to the blacklist for the channel the command was issued from
## admins, owner, and chanOps only
def blacklist(jenni, trigger):
	if (trigger.nick is trigger.sender): # make sure this isnt in a pm
		jenni.msg(trigger.nick, "can't blacklist in PM!")
		return
	if not (trigger.admin or trigger.owner or (trigger.nick in jenni.ops[trigger.sender])):  # check for admin or chanOp
		jenni.reply("You dont have great enough permissions!")
		return
	if ((trigger.group(2) is "blacklist") or (trigger.group(2) is "unlist")): # dont want to blacklist the blacklisting commands
		jenni.reply("you shouldn't do that...")
		return
	if (trigger.group(2) in jenni.config.chan_bls[trigger.sender]):
		jenni.reply(str(trigger.group(2)) + " is already blacklisted!")
		return
	### if (trigger.group(2) is not in [list of loaded commands]): 
	###		jenni.reply("can't blacklist " + str(trigger.group(2) + ". It's not loaded!")
	###		return
	jenni.config.chan_bls[trigger.sender].add(trigger.group(2))
	jenni.say(str(trigger.group(2)) + " sucessfully added to " + str(trigger.sender) + "'s blacklist.")
blacklist.commands = ['blacklist']
blacklist.priority = 'high'

## remove a command from the blacklist for the channel the command was issued from
## admins, owner, and chanOps only
def unlist(jenni, trigger):
	if (trigger.nick is trigger.sender):
		jenni.msg(trigger.nick, "can't blacklist in PM!")
		return
	if not (trigger.admin or trigger.owner or (trigger.nick in jenni.ops[trigger.sender])):
		jenni.reply("You dont have great enough permissions!")
		return
	if (trigger.group(2) not in jenni.config.chan_bls[trigger.sender]):
		jenni.reply("can't unlist " + str(trigger.group(2)) + ". It's not blacklisted!")
		return
	jenni.config.chan_bls[trigger.sender].remove(trigger.group(2))
	jenni.say(str(trigger.group(2)) + " sucessfully removed from " + str(trigger.sender) + "'s blacklist.")
unlist.commands = ['unlist']
unlist.priority = 'high'

## clear blacklist for the channel the command was issued from
## admins, owner, and chanOps only
def clearBL(jenni, trigger):
	if (trigger.nick is trigger.sender):
		jenni.msg(trigger.nick, "can't blacklist in PM!")
		return
	if not (trigger.admin or trigger.owner or (trigger.nick in jenni.ops[trigger.sender])):
		jenni.reply("You dont have great enough permissions!")
		return
	jenni.config.chan_bls[trigger.sender] = set ()
	jenni.say(str(trigger.sender) + "'s blacklist has been cleared!")
clearBL.commands = ['clearbl']
clearBL.priority = 'high'
if __name__ == '__main__':
    print __doc__.strip()
