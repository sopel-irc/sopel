# coding=utf-8
"""This module is able to run a command in the background, or
execute it and wait until it is over, then return its status
code and output.

Licensed under the Eiffel Forum License 2.
"""
from __future__ import unicode_literals, absolute_import
from subprocess import Popen, PIPE

from sopel.module import commands, example, require_admin

# this is the index of the argument of the invoked Sopel command
ARGUMENT = 2


def run(command):
    '''Run the given command and return its output
    and exit_code'''
    process = Popen(command.split(), stdout=PIPE)
    (output, _status) = process.communicate()
    exit_code = process.wait()
    return output, exit_code


def run_pipe(command):
    '''Same as `run`, but it is also able to handle commands
    that contain pipes by chaining them together. Written by @PlugaruT'''

    # for some reason there is a problem if there are double
    # or single quotes in command
    command = command.replace('"', '')
    command = command.replace("'", "")
    if "|" in command:
        command_parts = command.split("|")
    else:
        command_parts = []
        command_parts.append(command)
    i = 0
    pipe = {}
    for command_part in command_parts:
        if i == 0:
            pipe[i] = Popen(command_part.split(), stdout=PIPE)
        else:
            pipe[i] = Popen(command_part.split(),
                            stdin=pipe[i-1].stdout, stdout=PIPE)
        i = i + 1
    (output, _status) = pipe[i-1].communicate()
    exit_code = pipe[i-1].wait()
    return output, exit_code



def run_and_forget(command):
    '''Run the given command and move on, while it
    runs in the background. Returns the PID of the
    spawned process.'''
    process = Popen(command.split())
    return process.pid


@require_admin(message='Insufficient rights')
@commands('run')
@example('.run whoami')
def run_command(bot, trigger):
    '''Run an arbitrary command in the OS and return
    its status code and output'''
    command = trigger.group(ARGUMENT)
    if '|' in command:
        # use the fancier function if you see that the command
        # contains pipes; otherwise use the regular run function
        output, status = run_pipe(command)
    else:
        output, status = run(command)
    if output:
        # for convenience and clutter reduction, we will print
        # everything on a single line of there was nothing shown
        # on stdout, or if there was just one line
        lines = output.splitlines()
        if len(lines) == 1:
            bot.reply('Status: %i, Stdout: %s <<END' % (status, lines[0]))
        else:
            bot.reply('Status: %i, Stdout: ' % status)
            for line in lines:
                bot.say(line)
            bot.say('<<END')
    else:
        bot.reply('Status: %i, Stdout: <<EMPTY' % status)



@require_admin(message='Insufficient rights')
@commands('runbackground')
@example('.runbackground sleep 30')
def run_background(bot, trigger):
    '''Run the arbitrary command in the background,
    without waiting for it to return'''
    pid = run_and_forget(trigger.group(ARGUMENT))
    bot.reply('Started process %i' % pid)
