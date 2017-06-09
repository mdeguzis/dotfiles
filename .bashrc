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

# Always use long prompt for less
# http://stackoverflow.com/a/19871578
export LESS="-M"

#
# Handle ssh-agent intelligently
#
# This version is especially nice since it will see if you've already started ssh-agent 
# and, if it can't find it, will start it up and store the settings so that they'll be 
# usable the next time you start up a shell.
# Source: http://stackoverflow.com/a/18915067
# See also: http://mah.everybody.org/docs/ssh
SSH_ENV="$HOME/.ssh/environment"

function start_agent {
    echo "Initialising new SSH agent..."
    /usr/bin/ssh-agent | sed 's/^echo/#echo/' > "${SSH_ENV}"
    echo succeeded
    chmod 600 "${SSH_ENV}"
    . "${SSH_ENV}" > /dev/null
    /usr/bin/ssh-add;
}

# Source SSH settings, if applicable

if [ -f "${SSH_ENV}" ]; then
    . "${SSH_ENV}" > /dev/null
    #ps ${SSH_AGENT_PID} doesn't work under cywgin
    ps -ef | grep ${SSH_AGENT_PID} | grep ssh-agent$ > /dev/null || {
        start_agent;
    }
else
    start_agent;
fi

# Debian packaging
export DEBEMAIL="mdeguzis@gmail.com"
export DEBFULLNAME="Michael DeGuzis"

# Use vi mode for bash shell
# default mode: emacs
set -o vi
