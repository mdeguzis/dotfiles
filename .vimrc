" About {{{

" Fold sections with za (which is mapped to <SPACE>)
" Keep larger headers inside the {{{ CODE }}} wraps
" Remember to start a new fold section on the line after one ends

"}}}
" Main settings {{{

"---------------------------------------------
" Main settings
"---------------------------------------------

set noeb vb t_vb=			" Disable annoying system bell
set foldmethod=marker			" fold sections with markers
set nocompatible        		" Use Vim defaults (much better!)
set bs=indent,eol,start 		" allow backspacing over everything in insert mode
set ai					" always set autoindenting on

set backup				" keep a backup file and set paths
set backupdir=~/.vim-tmp,~/.tmp,~/tmp,/var/tmp,/tmp
set backupskip=/tmp/*,/private/tmp/*
set directory=~/.vim-tmp,~/.tmp,~/tmp,/var/tmp,/tmp
set writebackup

set viminfo='20,\"50    		" read/write a .viminfo file, don't store more
                        		" than 50 lines of registers 

"}}}
" colors {{{

"---------------------------------------------
" Colors
"---------------------------------------------

colorscheme desert			" set the color scheme
set hlsearch				" turn on search highlighting
syntax on				" turn on syntax highlighting

""}}}
" Editing {{{

"---------------------------------------------
" Editing
"---------------------------------------------

set nowrap				" do not wrap lines
set history=50              		" keep 50 lines of command line history
set number				" show line numbers
set ruler               		" show the cursor position all the time
set tabstop=8				" number of visual spaces after tab
set softtabstop=8   			" number of spaces in tab when editing
set formatoptions=cro			" turn off some auto formatting
					" Check current options: 'set formatoptions?'
					" See: http://vimdoc.sourceforge.net/htmldoc/change.html#fo-table
					" Remember, this will require then holding SHIFT for normal behavior
"set mouse+=a				" Set mouse behavior to not grab line numbers                                     │
					" Remember, this will require then holding SHIFT for normal behavior
					" Use SHIFT, then highlight the text, then CTRL+SHIFT+{C,V}
set clipboard=unnamedplus		" Allow copy/paste between windows and unix (visual only)
					" Use this with the mouse in GUI windows like Putty
"}}}
" Maps {{{

"---------------------------------------------
" Maps
"---------------------------------------------

" Note - put comments above commands here
" Because of the syntax, you may end up with <TAB> in your commands

" Toggle paste mode in insert mode
set pastetoggle=<F11>

" Toggle search highlighting
map <F12> :set hlsearch!<CR>

" Map SPACE in normal mode to fold
nnoremap <space> za

" clear the search string. 
" Esc works to exit insert/normal mode, and clear search in command mode
nnoremap <silent> <Esc> :let @/=''<CR>

" If vim/gvim has +clipboard, use a more intuitive map
nnoremap <C-c> +"y

"}}}
