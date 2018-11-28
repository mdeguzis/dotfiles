" Exceptions
" Fold this file differently
set foldmethod=indent
set foldnestmax=10
set nofoldenable
set foldlevel=2
:autocmd BufRead,BufNewFile $HOME/.vimrc setlocal foldmethod=marker
:autocmd BufRead,BufNewFile $HOME/.vimrc setlocal foldenable
:autocmd BufRead,BufNewFile $HOME/.vimrc setlocal foldlevel=0


