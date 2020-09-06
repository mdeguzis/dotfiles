# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi

# set tmux to use xterm not screen
# This correct the annoying behavior of fucntion keys changing case in normal vim normal mode.
export TERM=xterm-256color

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions

# colors
# https://misc.flogisoft.com/bash/tip_colors_and_formatting

alias grepc="grep --color=always"
alias grep="grep --color=always"
alias ls="ls --color=always"
alias python="/usr/bin/python3"

# Always use long prompt for less
# http://stackoverflow.com/a/19871578
# R allows the ANSI escape sequences to pass through unscathed,
# and they'll be rendered as colors in the terminal.
export LESS="RM"

# Prompt
# "slash bracket, slash e, [COLOR_CODE], slash bracket"
# example: "\[\e[36m\] PROMPT_STUFF [\e[0m\]" 
# always end with [\e[0m\]
# https://xta.github.io/HalloweenBash/
PS1="\[\e[36m\][\u@\h: \[\e[31m\]\W\[\e[36m\]]\[\e[0m\]\$ "

# For Debian packaging
export DEBEMAIL="mdeguzis@gmail.com"
export DEBFULLNAME="Michael DeGuzis"
# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi

# set tmux to use xterm not screen
# This correct the annoying behavior of fucntion keys changing case in normal vim normal mode.
export TERM=xterm-256color

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions

# Set an alias for grep color option
# For 'less', pass -R to it
alias grepc="grep --color=always"
alias pia-connect="sudo echo 'starting PIA'; sudo openvpn --config /etc/openvpn/client/New_Zealand.conf &"
alias pia-disconnect="sudo killall -9 openvpn"

# Debian packaging
export DEBEMAIL="mdeguzis@gmail.com"
export DEBFULLNAME="Michael DeGuzis"

# NOTE: set only in tmux.conf for now
# Don't exit with CTRL+D (annoying with tmux) right away
# Shell only exists after the 10th consecutive Ctrl-d
#IGNOREEOF=3
# Same as setting IGNOREEOF=10
#set -o ignoreeof

# Use vi mode for bash shell
# default mode: emacs
# set -o vi

alias pip="/usr/bin/pip3"
alias upgrade="${HOME}/software/scripts/upgrade-system.sh"
