#!/bin/bash

scriptdir="${PWD}"

# Copy core files into homedir
core_files=()
core_files+=(".bashrc")
core_files+=(".tmux.conf")
core_files+=(".vimrc")

echo -e "\n==> Copying core dotfiles into ${HOME}\n"
for entry in "${core_files[@]}"
do
	cp -v "${entry}" "${HOME}"
done

# Add modules for saving tmux session
echo -e "\n==> Extra tmux setup\n"
if [[ ! -d "${HOME}/tmux-resurrect" ]]; then
	echo "Missing tmux-resurrect, cloning"
	git clone https://github.com/tmux-plugins/tmux-resurrect ~/tmux-resurrect
else
	echo "updating tmux-ressurrect"
	cd "${HOME}/tmux-resurrect"
	git pull
	cd "${scriptdir}"
fi

if [[ ! -d "${HOME}/tmux-continuum" ]]; then
	echo "Missing tmux-continuum, cloning"
	git clone https://github.com/tmux-plugins/tmux-continuum ~/tmux-continuum
else
	echo "updating /tmux-continuum"
	cd "${HOME}//tmux-continuum"
	git pull
	cd "${scriptdir}"
fi

# reload tmux conf
echo "reloading tmux conf"
tmux source-file ~/.tmux.conf
