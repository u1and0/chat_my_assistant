" usage:
" source chat_function.vim
" :'<,'>call Chat()
function! Chat()
    " 選択範囲をレジスタxへ格納
    normal! gv"xy
    sp | term python ${PYTHONPATH}/chat_my_assistant/chatme.py
    " sleepしないとプロンプトの前に貼り付けられてしまう
    sleep 1
    normal! "xp
    execute "normal! a<CR>"
    " execute "normal! \<CR>"
endfunction

vnoremap <leader>c :call Chat()<CR>
