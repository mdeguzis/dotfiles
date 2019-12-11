" Even though my current .vimrc has the right defaults,
" ensure that they are still set
" .pp files are for Puppet
set tabstop=2       "" set to 2 spaces
set softtabstop=0   "" no tab stop 
set expandtab       "" expand tab to spaces 
set shiftwidth=2    "" set shift width
set smarttab        "" alignment trickery

if !exists('g:puppet_align_hashes')
    let g:puppet_align_hashes = 1
endif

if g:puppet_align_hashes
    inoremap <buffer> <silent> => =><Esc>:call puppet#align#AlignHashrockets()<CR>$a
endif
