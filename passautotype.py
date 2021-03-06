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
# (c) 2016 Alexander Schier <allo -at- laxu.de>


import subprocess
from time import sleep
import os
import sys
from glob import glob1


ZENITY = True
WAIT_TIME = 0.3  # time to wait before starting to type

PASSWORD_STORE_DIR = os.environ.get("PASSWORD_STORE_DIR") or os.environ["HOME"] + "/.password-store"


HELP_TEXT = """
Usage:
======

-h, --help: This help.
--help-add: Show how to add autotype entries to your pass database.
--help-symlink: Show how to use existing entries for autotype.
--help-sequence: Description of the commands in a custom sequence.
-t --type: Type the password for the current window.
-s, --symlink PASSWORDENTRY WINDOWTITLE[/ACCOUNT]: create a autotype
              symlink. See --help-symlink

To be able to run the command while the correct window has the focus,
you should add a hotkey for "passautotype -t" in the shortcut settings of
your desktop environment or window manager.
"""

HELP_TEXT_ADD = """
Adding Autotype Entries
=======================

To use passautotype to type the correct password in a window, you need to
add the password entries with the corresponding window title.

- WINDOWTITLE is the part of the window title, that should be matched to use
the corresponding password. For example you could use "Testwebsite" to match
the title "This is my Testwebsite". You can use spaces and other special
characters, but don't forget to escape them for your shell.
(pass handles them without problems, even chars like "|")

- ACCOUNT is a name you choose for the stored account, which will be used
  in the account chooser, when you have multiple accounts for a site.
  This is optional at all places, if you (only) want to add a default account,
  you can omit the "ACCOUNT/" part when inserting the password.
  ACCOUNT may not be "username", "password" or "sequence"

Password entries:
-----------------
$ pass insert 'autotype/WINDOWTITLE/ACCOUNT'

Username / Password entries:
----------------------------
For the Username:
$ pass insert 'autotype/WINDOWTITLE/ACCOUNT/username'
For the Password:
$ pass insert 'autotype/WINDOWTITLE/ACCOUNT/password'

Custom Sequences:
-----------------
Username:
$ pass insert 'autotype/WINDOWTITLE/ACCOUNT/username'
Password:
$ pass insert 'autotype/WINDOWTITLE/ACCOUNT/password'
Sequence:
$ pass insert -m 'autotype/WINDOWTITLE/ACCOUNT/sequence'

see --help-sequence for how to use custom sequences.
"""

HELP_TEXT_SYMLINK="""
Using the normal pass database with autotype
--------------------------------------------

You can use your usual pass database by creating symlinks
for the autotype entries.

To use an entry as default account for a window title:
$ passautotype --symlink ENTRY WINDOWTITLE

To add multiple accounts for the window title:
$ passautotype --symlink ENTRY WINDOWTITLE/ACCOUNT

You will be prompted to add an optional username and
an optional custom sequence (see --help-sequence)

This allows you to store the password at a easy to find location like
"email/me@mymail" and allows autotype to find it for the
window title "My cool Mail".

Example (do not forget the quotes):
$ passautotype --symlink "email/me@mymail" "My cool Mail/personalaccount"
"""

HELP_TEXT_SEQUENCE="""
Custom Sequences
----------------

When adding a custom sequence, you you use the following keywords:
- "USER": Type the username.
- "PASS": Type the password.
- "KEY somekey": Press a key.
- "TEXT some text": Type some text
- "SLEEP X": Sleep for X seconds (float value)

The key names are in the syntax of "xdotool" and need correct capitalization.
Some examples are: Tab, Return, BackSpace, ctrl+a, shift+Tab.

Example: Login on a site asking for username and password on different pages:
USER
KEY Return
SLEEP 0.5
PASS
KEY Return

The default username/password behaviour is the sequence:
USER
KEY Tab
PASS
Key Return
"""


def run_piped(cmd_list):
    """
        Run a command with arguments in the form
        ["command", "arg1", "arg2", ...] and return stdout
    """
    return subprocess.Popen(
        cmd_list, stdout=subprocess.PIPE).communicate()[0].strip()


def is_password_dir(dir):
    return not os.path.isfile(dir + "/username.gpg") \
        and os.path.isfile(dir + "/password.gpg") \
        and not os.path.isfile(dir + "/sequence.gpg")


def is_username_password_dir(dir):
    return os.path.isfile(dir + "/username.gpg") \
        and os.path.isfile(dir + "/password.gpg") \
        and not os.path.isfile(dir + "/sequence.gpg")


def is_sequence_dir(dir):
    return os.path.isfile(dir + "/username.gpg") \
        and os.path.isfile(dir + "/password.gpg") \
        and os.path.isfile(dir + "/sequence.gpg")


def get_choices(autotype_dir, autotype_titles):
    choices = []
    for title in autotype_titles:
        title_dir = autotype_dir + "/" + title
        entries = glob1(title_dir, "*")  # autotype/title/account
        entries += [""]  # autotype/title (default account)
        for entry in entries:
            account_name = None
            account_type = None
            if entry.endswith(".gpg"):
                if entry in ["username.gpg", "password.gpg", "sequence.gpg"]:
                    # no account file, but part of the default account folder
                    continue
            elif os.path.isdir(title_dir + "/" + entry):
                entry_dir = title_dir + "/" + entry
                account_name = entry
                if is_sequence_dir(entry_dir):
                    account_type = "sequence"
                elif is_username_password_dir(entry_dir):
                    account_type = "user_password"
                elif is_password_dir(entry_dir):
                    account_type = "password"

            if account_type is not None and account_name is not None:
                choices.append([
                    account_type,
                    account_name,
                    title
                ])

    choices.sort(key=lambda x: x[1])
    return choices


def choose_entry(choices):
    if len(choices) == 0:
        return None
    if len(choices) == 1:
        # use the only one
        return choices[0]

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
            entries.append(
                item[1] + " | " + item[2] + " (" + type_text + ")")
        else:
            entries += [item[1], item[2], type_text]
    if not ZENITY:
        choice = run_piped(["kdialog", "--geometry", "500x300",
                            "--menu", "Multiple Choices:"] + entries)
    else:
        choice = run_piped(["zenity", "--list",
                            "--text", "Multiple Choices:",
                            "--column", "Index",
                            "--column", "Account",
                            "--column", "Title",
                            "--column", "Type",
                            "--hide-column", "1",
                            "--width", "500",
                            "--height", "300"] + entries)
    if len(choice):
        return choices[int(choice)]
    else:
        return None


def autotype():
    autotype_dir = PASSWORD_STORE_DIR + "/autotype"
    window_id = run_piped(["xdotool", "getactivewindow"])
    window_name = run_piped(["xdotool", "getwindowname", window_id])
    autotype_titles = [title for title in glob1(autotype_dir, "*")
                       if title.lower() in window_name.lower()]

    choices = get_choices(autotype_dir, autotype_titles)
    choice = choose_entry(choices)

    if choice is None:
        # no choices or dialog canceled
        sys.exit(0)

    type = choice[0]
    entry = choice[2] + "/" + choice[1]

    # wait a moment to avoid triggering shortcuts, when the user starts
    # the script via shortcut (i.e. ctrl+shift+p and the script triggers
    # other shortcuts with ctrl+shift)
    sleep(WAIT_TIME)
    if type == "password":
        password = run_piped(
            ["pass", "show", "autotype/" + entry + "/password"])
        subprocess.call(["xdotool", "type", password])
        return

    # username_password or sequence
    username = run_piped(
        ["pass", "show", "autotype/" + entry + "/username"])
    password = run_piped(
        ["pass", "show", "autotype/" + entry + "/password"])

    if type == "sequence":
        sequence = run_piped(
            ["pass", "show", "autotype/" + entry + "/sequence"])
    else:  # username and password
        sequence = "USER\nKEY Tab\nPASS\nKEY Return"

    # make sure, the same window as before has the focus
    window_id2 = run_piped(["xdotool", "getactivewindow"])
    if window_id2 != window_id:
        print "active window changed. Aborting."
        return

    for line in sequence.split("\n"):
        if line == "USER":
            subprocess.call(["xdotool", "type",
                             "--clearmodifiers", username])
        elif line == "PASS":
            subprocess.call(["xdotool", "type",
                             "--clearmodifiers", password])
        elif line.startswith("KEY "):
            key = line.split(" ", 1)[1]
            subprocess.call(["xdotool", "key", "--clearmodifiers", key])
        elif line.startswith("TEXT "):
            text = line.split(" ", 1)[1]
            subprocess.call(["xdotool", "type", "--clearmodifiers", text])
        elif line.startswith("SLEEP "):
            delay = float(line.split(" ", 1)[1])
            sleep(delay)

def symlink(password_file, autotype_dir):
    password_path = PASSWORD_STORE_DIR + "/" + password_file + ".gpg"
    autotype_path = PASSWORD_STORE_DIR + "/autotype/" + autotype_dir
    if not os.path.isfile(password_path):
        print 'Password "{0}" does not exist'.format(password_file)
        sys.exit(1)
    elif os.path.lexists(autotype_path + "/password.gpg"):
        print 'Autotype for "{0}" already exists'.format(autotype_dir)
        title_folder = autotype_dir.split("/", 1)[0]
        print 'You can add another account at "{0}/ACCOUNTNAME" using a new account name.'.format(title_folder)
        sys.exit(1)
    elif os.path.lexists(autotype_path) and not os.path.isdir(autotype_path):
        # autotype_path exists and is no directory
        print 'Error, autotype directory "{0}" already exists'.format(autotype_dir)
        sys.exit(1)

    if not os.path.lexists(autotype_path):
        os.makedirs(autotype_path)
    depth = len(autotype_dir.split("/"))
    os.symlink("../" * ( depth + 1) + password_file + ".gpg", autotype_path + "/password.gpg")
    if os.path.lexists(PASSWORD_STORE_DIR + "/.git"):
        subprocess.call(["pass", "git", "add", autotype_path + "/password.gpg"])
        subprocess.call(["pass", "git", "commit", "-m",
            "Add autotype symlink for {name} -> autotype/{autotype}/password to store.".format(name=password_file, autotype=autotype_dir),
            autotype_path + "/password.gpg"])
    print
    if raw_input("Do you want to enter a username? ([y]/n): ") != "n":
        subprocess.call(["pass", "insert", "-e", "autotype/" + autotype_dir + "/username"])
    print
    if raw_input("Do you want to use a custom sequence? (y/[n]): ") == "y":
        subprocess.call(["pass", "insert", "-m", "autotype/" + autotype_dir + "/sequence"])



# Commandline argument parsing
if len(sys.argv) == 2 and (sys.argv[1] == "-t" or sys.argv[1] == "--type"):
    autotype()
elif len(sys.argv) == 4 and (sys.argv[1] == "-s" or sys.argv[1] == "--symlink"):
    symlink(sys.argv[2], sys.argv[3])
elif len(sys.argv) == 2 and sys.argv[1] == "--help-add":
    print HELP_TEXT_ADD
    sys.exit(0)
elif len(sys.argv) == 2 and sys.argv[1] == "--help-symlink":
    print HELP_TEXT_SYMLINK
    sys.exit(0)
elif len(sys.argv) == 2 and sys.argv[1] == "--help-sequence":
    print HELP_TEXT_SEQUENCE
    sys.exit(0)
elif len(sys.argv) == 2 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
    print HELP_TEXT
    sys.exit(0)
else:
    print "run \"{0} --help\" for usage information".format(
        os.path.basename(sys.argv[0]))
    sys.exit(0)
