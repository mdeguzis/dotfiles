" About {{{

" Fold sections with za (which is mapped to <SPACE>)
" Keep larger headers inside the {{{ CODE }}} wraps
" Remember to start a new fold section on the line after one ends

"}}}
" Main settings {{{

"---------------------------------------------
" Main settings
"---------------------------------------------

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
set softtabstop=4   			" number of spaces in tab when editing
set formatoptions=cro			" turn off some auto formatting
					" Check current options: 'set formatoptions?'
					" See: http://vimdoc.sourceforge.net/htmldoc/change.html#fo-table
					" Remember, this will require then holding SHIFT for normal behavior
set mouse+=a				" Set mouse behavior to not grab line numbers                                     │
					" Remember, this will require then holding SHIFT for normal behavior
					" Use SHIFT, then highlight the text, then CTRL+SHIFT+{C,V}
set clipboard=unamedplus		" Allow copy/paste between windows and unix (visual only)
					" Use this with the mouse in GUI windows like Putty
"}}}
" Maps {{{

"---------------------------------------------
" Maps
"---------------------------------------------

map <F12> :set hlsearch!<CR>		" Map F12 to toggle search highlighting
nnoremap <space> za			" Map SPACE in normal mode to fold
nnoremap <silent> <Esc> :let @/=""<CR>  " clear the search string

"}}}
