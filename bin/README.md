# About

## tmux-ressurrect

Source: http://brainscraps.wikia.com/wiki/Resurrecting_tmux_Sessions_After_Reboot

tmux-ressurrect is the best option here

Features:

* tmux windows
* tmux panes
* entered text on screen is still there

Does not:

* keep open files on screen (obvious)

Testing:
```
tmux attach -d -t work
<do stuff>
:detach

./tmux-resurrect.sh -b
tmux kill-session -t work
./tmux-resurrect.sh -r
 
```
