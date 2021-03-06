#!/bin/bash

scriptdir="${PWD}"

echo -e "\n==> OS customization\n"

# setup for tmux will be different if you are on windows or os x
read -erp "What is your primary parent OS you will be using? (windows|osx|linux): " oschoice
if [[ "${oschoice}" == "windows" ]]; then
	TMUX_CONF=".tmux.conf.windows"
elif [[ "${oschoice}" == "osx" || "${oschoice}" == "linux" ]]; then
	TMUX_CONF=".tmux.conf.osx"
else
	echo "ERROR: Invalid choice"
	exit 1
fi

# Setup dirs
mkdir -p ${HOME}/.vim/after/ftplugin/
mkdir -p ${HOME}/.vim/after/ftdetect/
mkdir -p ${HOME}/.vim/syntax
mkdir -p ${HOME}/.vim/bundle

# Copy core files into homedir
core_files=()
core_files+=(".bashrc")
core_files+=(".bash_profile")
core_files+=(".nanorc")
core_files+=("${TMUX_CONF}")
core_files+=(".vimrc")
core_files+=(".zshrc")

echo -e "\n==> Copying core dotfiles into ${HOME}\n"
for entry in "${core_files[@]}"
do
	cp -v "${entry}" "${HOME}"
done

# Adjust tmux filename
mv "${HOME}/${TMUX_CONF}" "${HOME}/.tmux.conf"

echo -e "\n==> Copying vim ftplugin prefs into ${HOME}/.vim/ftplugin\n"
cp -rv .vim/after/ftplugin/* ~/.vim/after/ftplugin/

echo -e "\n==> Copying vim ftdetect prefs into ${HOME}/.vim/ftdetect\n"
cp -rv .vim/after/ftdetect/* ~/.vim/after/ftdetect/

echo -e "\n==> Copying vim syntax prefs into ${HOME}/.vim/syntax\n"
cp -rv .vim/syntax/* ~/.vim/syntax/

echo -e "\n==> Copying vim bundle prefs into ${HOME}/.vim/ftdetect\n"
cp -rv .vim/bundle/* ~/.vim/bundle

#echo -e "==> update-alternatives setup"
# sudo update-alternatives --install <target> <name_to_lits> <actual_path> <priority>
#sudo update-alternatives --install /usr/bin/editor editor /usr/bin/vim 100

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

