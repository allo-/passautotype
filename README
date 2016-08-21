passautotype
============

Usage
-----

Add some Hotkey for "passautotype.py --type" to your desktop environment. 

- For KDE open "systemsettings" and select "Shortcuts and gestures" and add
  some shortcut under "Custom Shortcuts".
  See https://docs.kde.org/trunk5/en/kde-workspace/kcontrol/khotkeys/manage.html#manage-add-shortcut
- For GNOME go to Keyboard settings and select Shortcuts tab.
  See https://help.gnome.org/users/gnome-help/stable/keyboard-shortcuts-set.html

Then add some autotype windowtitles using "passautotype --symlink mypasswordname 'My Window Title'"

For full usage information run passautotype.py --help

Example
-------

Assume you have some password stored as "websites/github" and want to add
github windows to passautotype. Further you have git integration enabled
in your passwordstore directory.

    $ passautotype.py -s websites/github "GitHub"
    [master xxxxxxx] Add autotype symlink for websites/github- -> autotype/GitHub/password to store.
     1 file changed, 1 insertion(+)
     create mode 120000 autotype/GitHub/password.gpg
    
    Do you want to enter a username? ([y]/n): y
    Enter password for autotype/GitHub/username: MYUSERNAME
    [master xxxxxxx] Add given password for autotype/GitHub/username to store.
     1 file changed, 0 insertions(+), 0 deletions(-)
     create mode 100644 autotype/GitHub/username.gpg
    
    Do you want to use a custom sequence? (y/[n]): n

If you now press the configured hotkey when having a github window open,
passautotype will type your username and password.

You can add another github account using

    $ passautotype.py -s websites/github/myotheraccount "GitHub"

and passautoype will show you a dialog, which allows you to choose which account to use,
when you try to login at the GitHub site.

Security
--------

- passautotype does not verify the website or even the program, but just uses the window title.
  Make sure to check the url before pressing the autotype hotkey!
- passautotype does not automatically focus the username/password field, so make sure
  the correct textfield is focused before starting autotype.
  You can use a custom sequence to change the focus, though.
- passautotype verifies, that the correct window is focused. When you press the hotkey and then another
  window gets the focus before you finished typing your master password, passautotype does not type
  your password in the wrong window.
- Malicious browser addons can only read the passwords you actually use, not the whole password store.
  Keyloggers may or may not be able to log the passwords, depending on the method they use to grab the input.

Custom Sequences
----------------

By default, passautoype types your username, then sends a TAB key, then types the password and sends the ENTER key.
Some sites have another login, like gmail, which asks for the username and then for the password on the next page.
The custom sequence then would look like this:

    USER
    KEY Return
    SLEEP 0.5
    PASS
    KEY Return

Make sure, that the SLEEP is long enough, that the next page finished loading.

You can use these keywords:

- "USER": Type the username.
- "PASS": Type the password.
- "KEY somekey": Press a key.
- "TEXT some text": Type some text
- "SLEEP X": Sleep for X seconds (float value)

The key names are in the syntax of "xdotool" and need correct capitalization.
Some examples are: Tab, Return, BackSpace, ctrl+a, shift+Tab.


Dependencies
------------

- zenity (recommended) or kdialog (change the ZENITY constant in the code)
- xdotool
