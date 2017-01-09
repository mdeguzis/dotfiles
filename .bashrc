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
