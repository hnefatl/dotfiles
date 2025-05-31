#!/usr/bin/env bash

# This exports WORK_SETUP
source ~/.kenvironment

# Desktop background color.
xsetroot -solid "#333333"

export PATH="$PATH:~/.local/bin"

export EDITOR="vim"
export BROWSER="google-chrome-stable"
export LESS="-r"  # Enable colour output in less
export TERMINAL="terminator"

# Keyboard layout
setxkbmap -layout gb
# Set keyboard repeat rate
xset r rate 200 60
# Load custom keymap
xmodmap .xmodmap

if [[ $WORK_SETUP ]] ; then
  # Necessary to make chrome pick up the proxy settings stored in gconf.
  #export DESKTOP_SESSION=gnome
  
  # NOTE: This may break your compose key.
  # See http://g/i3-users/YBexXGbik7E for more details.
  #export GTK_IM_MODULE=xim
  # Run autostarts like gLinux status indicator
  dex -ae i3

  # Disable middle-mouse-paste (id from `xinput list`, numbers from `xinput get-button-map <id>`)
  xinput set-button-map 16 1 0 3 4 5 6 7
fi

source .profile
exec i3
