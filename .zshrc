source /apollo/env/envImprovement/var/zshrc

export BRAZIL_WORKSPACE_DEFAULT_LAYOUT=short

for f in SDETools envImprovement AmazonAwsCli OdinTools; do
    if [[ -d /apollo/env/$f ]]; then
        export PATH=$PATH:/apollo/env/$f/bin
    fi
done

export AUTO_TITLE_SCREENS="NO"

# dumb extra location output removed:
#%{$fg[white]%}(%D %*) <%?> [%~] $program %{$fg[default]%}
export PROMPT="%{$fg[cyan]%}[%m:%{$fg[red]%} %1~%{$fg[cyan]%}]%{$fg[white]%}$ "

# Clear TERM text with vim/less etc..
export TERM=xterm

export RPROMPT=

set-title() {
    echo -e "\e]0;$*\007"
}

ssh() {
    set-title $*;
    /usr/bin/ssh -2 $*;
    set-title $HOST;
}

# Aliases
alias e=emacs
alias bb=brazil-build
alias bba='brazil-build apollo-pkg'
alias bre='brazil-runtime-exec'
alias brc='brazil-recursive-cmd'
alias bws='brazil ws'
alias bwsuse='bws use --gitMode -p'
alias bwscreate='bws create -n'
alias brc=brazil-recursive-cmd
alias bbr='brc brazil-build'
alias bball='brc --allPackages'
alias bbb='brc --allPackages brazil-build'
alias bbra='bbr apollo-pkg'
alias third-party-promote='~/.toolbox/bin/brazil-third-party-tool promote'
alias third-party='~/.toolbox/bin/brazil-third-party-tool'
alias vim='/apollo/env/envImprovement/bin/vim'

if [ -f ~/.zshrc-dev-dsk-post ]; then
    source ~/.zshrc-dev-dsk-post
fi
export PATH=$HOME/.toolbox/bin:$PATH
export PATH="/apollo/env/AmazonAwsCli/bin/:$PATH"

# Pip
export PATH=$HOME/.local/bin:$PATH

# Docker
export DOCKER_HOST=unix:///var/run/docker.sock
source /etc/profile.d/docker_host.sh

# RDE
fpath=(~/.zsh/completion $fpath)
autoload -Uz compinit && compinit -i
