" About {{{

" Fold sections with za, which is mapped to <SPACE>
" Keep larger headers inside the {{{ CODE }}} wraps
" Remember to start a new fold section on the line after one ends
"
" Plugin docs
" http://learnvimscriptthehardway.stevelosh.com/chapters/42.html

"}}}
" Main settings {{{

"---------------------------------------------
" Main settings
"---------------------------------------------

set nocompatible            " Use Vim defaults (much better!)
set noeb vb t_vb=           " Disable annoying system bell
set foldmethod=indent   
set foldnestmax=10
set nofoldenable
set foldlevel=2
set bs=indent,eol,start     " allow backspacing over everything in insert mode
set ai                      " always set autoindenting on

set backup                  " keep a backup file and set paths
set backupdir=~/.vim-tmp,~/.tmp,~/tmp,/var/tmp,/tmp
set backupskip=/tmp/*,/private/tmp/*
set directory=~/.vim-tmp,~/.tmp,~/tmp,/var/tmp,/tmp
set writebackup

set viminfo='20,\"50        " read/write a .viminfo file, don't store more
                            " than 50 lines of registers 

"}}}
" colors {{{

"---------------------------------------------
" Colors
"---------------------------------------------

colorscheme desert          " set the color scheme, and set overrides aith autocmd
autocmd ColorScheme * highlight Search cterm=NONE ctermfg=darkblue ctermbg=darkgreen 
autocmd ColorScheme * highlight Visual cterm=NONE ctermfg=black ctermbg=cyan
autocmd BufNewFile,BufRead Jenkinsfile   set syntax=groovy
set hlsearch                " turn on search highlighting
syntax on                   " turn on syntax highlighting

""}}}
" Editing {{{

"---------------------------------------------
" Editing defaults
"---------------------------------------------
"For more details on any of these see :help 'optionname' in vim (e.g. :help 'tabstop')

set nowrap                  " do not wrap lines
set history=50              " keep 50 lines of command line history
set number                  " show line numbers
set ruler                   " show the cursor position all the time
set tabstop=4               " Set TAB to input 4 spaces
set softtabstop=0           " Do not simulate tab key
set expandtab               " Enable tab key to insert space
set shiftwidth=4 smarttab   " 
    
"set mouse+=a               " Set mouse behavior to not grab line numbers                                     │
                            " Remember, this will require then holding SHIFT for normal behavior
                            " Use SHIFT, then highlight the text, then CTRL+SHIFT+{C,V}
set clipboard=unnamedplus   " Allow copy/paste between windows and unix (visual only)
                            " Use this with the mouse in GUI windows like Putty
set ignorecase              " Use Smartcase instead (uses case-sensitive only if a capital letter is present)
set smartcase               " https://stackoverflow.com/questions/2287440/how-to-do-case-insensitive-search-in-vim
"}}}
" Maps {{{

"---------------------------------------------
" Maps
"---------------------------------------------

" Note - put comments above commands here
" Because of the syntax, you may end up with <TAB> in your commands

" Toggle line numbers (mainly just for pasting)
nnoremap <F2> :set nonumber!<CR>

" Toggle paste mode in insert mode
set pastetoggle=<F10>

" Toggle search highlighting
map <F12> :set hlsearch!<CR>

" Map SPACE in normal mode to fold
nnoremap <space> za

" clear the search string. 
" Esc works to exit insert/normal mode, and clear search in command mode
nnoremap <silent> <F12> :let @/=''<CR>

" If vim/gvim has +clipboard, use a more intuitive map for clipboard
nnoremap <C-c> +\"y

"}}}

""}}}
" Pathogen {{{

"---------------------------------------------
" Plugins
"---------------------------------------------
"https://github.com/tpope/vim-pathogen

"execute pathogen#infect()
syntax on
filetype plugin indent on

