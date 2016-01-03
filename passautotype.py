#!/usr/bin/env python

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# (c) 2016 Alexander Schier


import subprocess
from time import sleep
import os, sys
from glob import glob1


ZENITY = True


def run_piped(cmd_list):
    """
        Run a command with arguments in the form
        ["command", "arg1", "arg2", ...] and return stdout
    """
    return subprocess.Popen(cmd_list, stdout=subprocess.PIPE).communicate()[0]


def is_username_password_dir(dir):
    return os.path.isfile(dir + "/username.gpg") \
    and os.path.isfile(dir + "/password.gpg") \
    and not os.path.isfile(dir + "/sequence.gpg")


def is_sequence_dir(dir):
    return os.path.isfile(dir + "/username.gpg") \
    and os.path.isfile(dir + "/password.gpg") \
    and os.path.isfile(dir + "/sequence.gpg")

if len(sys.argv) > 1 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
    print """
Usage:
======

To use passautotype to type the correct password in a window, you need to
add the correct entries to you pass database.

- WINDOWTITLE is the part of the window title, that should be matched to use
the corresponding password. For example you could use "Testwebsite" to match
the title "This is my Testwebsite". You can use spaces and other special
characters, but don't forget to escape them for your shell
(pass handles them without problems, even chars like "|")
- ACCOUNT is a name you choose for the stored account, which will be used
  in the account chooser when you have multiple accounts for a site.

Password entries:
-----------------
pass insert 'autotype/ACCOUNT/WINDOWTITLE'

Username / Password entries:
----------------------------
For the Username:
pass insert 'autotype/WINDOWTITLE/ACCOUNT/username'
For the Password:
pass insert 'autotype/WINDOWTITLE/ACCOUNT/password'

Custom Sequence:
----------------
Username:
pass insert 'autotype/WINDOWTITLE/ACCOUNT/username'
Password:
pass insert 'autotype/WINDOWTITLE/ACCOUNT/password'
Sequence:
pass insert -m 'autotype/WINDOWTITLE/ACCOUNT/sequence'

In the sequence, you can use the following keywords:
- "USER": type the username.
- "PASS": type the password.
- "KEY somekey": press a key.
- "TEXT some text": Type some text
- "SLEEP X": Sleep for X seconds (float value)

The key names are in the syntax of xdotool and depend on captialization.
Some examples are: Tab, Return, BackSpace, ctrl+a, shift+Tab.

Example: Login on a site asking for username and password on different pages:
USER
KEY Enter
SLEEP 0.5
PASS
KEY Enter

You can use your usual pass database by creating symlinks like this:
$ mkdir -p ~/.password-store/autotype/site/default/
$ ln -s ~/.password-store/user@site.gpg ~/.password-store/autotype/sitetitle/default/password.gpg
$ pass insert -e autotype/sitetitle/default/username # enter the corresponding username
"""
    sys.exit(0)


autotype_dir = os.environ["HOME"] + "/.password-store/autotype"

window_id = run_piped(["xdotool", "getactivewindow"])
window_name = run_piped(["xdotool", "getwindowname", window_id])

autotype_titles = [title for title in glob1(autotype_dir, "*")
                   if title.lower() in window_name.lower()]

password_matches = []
user_password_matches = []
sequence_matches = []
for title in autotype_titles:
    title_dir = autotype_dir + "/" + title
    entries = glob1(title_dir, "*")
    for entry in entries:
        if entry.endswith(".gpg"):
            password_matches.append([
                entry[:-4],
                title
            ])
        elif os.path.isdir(title_dir + "/" + entry):
            entry_dir = title_dir + "/" + entry
            if is_sequence_dir(entry_dir):
                sequence_matches.append([
                    entry,
                    title
                ])
            elif is_username_password_dir(entry_dir):
                user_password_matches.append([
                    entry,
                    title
                ])


choices  = [["password"] + match for match in password_matches]
choices += [["user_password"] + match for match in user_password_matches]
choices += [["sequence"] + match for match in sequence_matches]
choices.sort(key=lambda x: x[1])

choice = None 
if len(choices) == 0:
    sys.exit(1)
elif len(choices) == 1:
    choice = 0
else:
    entries = []
    for index, item in enumerate(choices):
        entries.append(str(index))
        if item[0] == "password":
            type_text = "Password"
        elif item[0] == "user_password":
            type_text = "Username and Password"
        elif item[0] == "sequence":
            type_text = "Custom Sequence"
        if not ZENITY:
            entries.append(item[1] + " | " + item[2] + " (" + type_text + ")")
        else:
            entries += [item[1], item[2], type_text]
    if not ZENITY:
        choice=run_piped(["kdialog", "--geometry", "500x300", "--menu", "Multiple Choices:"] + entries)
    else:
        choice=run_piped(["zenity", "--list", "--text", "Multiple Choices:",
            "--column", "Index",
            "--column", "Account",
            "--column", "Title",
            "--column", "Type",
            "--hide-column", "1",
            "--width", "500",
            "--height", "300"] + entries)

if choice is not None:
    item = choices[int(choice)]
    type = item[0]
    entry = item[2] + "/" + item[1]
    if type == "password":
        password = run_piped(["pass", "show", "autotype/" + entry])
        subprocess.call(["xdotool", "type", password])
    elif type == "user_password":
        username = run_piped(
            ["pass", "show", "autotype/" + entry + "/username"])
        password = run_piped(
            ["pass", "show", "autotype/" + entry + "/password"])
        subprocess.call(["xdotool", "type", "--clearmodifiers", username])
        subprocess.call(["xdotool", "key", "--clearmodifiers", "Tab"])
        subprocess.call(["xdotool", "type", "--clearmodifiers", password])
        subprocess.call(["xdotool", "key", "--clearmodifiers", "Return"])
    elif type == "sequence":
        username = run_piped(
            ["pass", "show", "autotype/" + entry + "/username"])
        password = run_piped(
            ["pass", "show", "autotype/" + entry + "/password"])
        sequence = run_piped(
            ["pass", "show", "autotype/" + entry + "/sequence"])
        for line in sequence.split("\n"):
            if line == "USER":
                subprocess.call(["xdotool", "type", "--clearmodifiers", username])
            elif line == "PASS":
                subprocess.call(["xdotool", "type", "--clearmodifiers", password])
            elif line.startswith("KEY "):
                key = line.split(" ", 1)[1]
                subprocess.call(["xdotool", "key", "--clearmodifiers", key])
            elif line.startswith("TEXT "):
                text = line.split(" ", 1)[1]
                subprocess.call(["xdotool", "type", "--clearmodifiers", text])
            elif line.startswith("SLEEP "):
                delay = float(line.split(" ", 1)[1])
                sleep(delay)
