" :norm "y+ :sp | term python ${HOME}/Dropbox/Program/python/chat_my_assistant/memory_chat_digest.py <CR> <C-r>+<CR>
" 選択範囲をクリップしてGPTチャットを開く
" vnoremap <leader>g :y <bar> sp <bar> term python ${HOME}/Dropbox/Program/python/chat_my_assistant/memory_chat_digest.py<CR>
" command!  Chat execute "echo '". escape(@\", "'\\")."'"
function! Chat()
    " 選択範囲をレジスタxへ格納
    normal! gv"xy
    " let result = getreg('')
    " call setreg('"', result, 'x')
    sp | term python ${HOME}/Dropbox/Program/python/chat_my_assistant/memory_chat_digest.py
    " sleepしないとプロンプトの前に貼り付けられてしまう
    sleep 1
    normal! "xp
    execute "normal! a<CR>"
    " execute "normal! \<CR>"
endfunction
