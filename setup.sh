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
# Restore steps for a specific save point:
# make sure you start this with a "fresh" tmux instance
#	$ cd ~/.tmux/resurrect/
#	locate the save file you'd like to use for restore (file names have a timestamp)
#	symlink the last file to the desired save file: $ ln -sf <file_name> last
#	do a restore with tmux-resurrect key: prefix + Ctrl-r
echo -e "\n==> Extra tmux setup\n"

# only install this if tmux > 1.9
# Check for bad exit status on this eval
if [[ ! $(echo "$(tmux -V | sed 's/tmux //') < 1.9" | bc -l) ]]; then

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

else

	echo "$(tmux -V) is too old for tmux-continuum"
	echo "Please use bin/tmux-ressurect instead (see README.md in bin/)"

fi
