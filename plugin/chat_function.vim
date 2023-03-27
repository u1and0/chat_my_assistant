" usage:
" source chat_function.vim
" :'<,'>call Chat()
function! Chat()
    " 選択範囲をレジスタxへ格納
    normal! gv"xy
    vs | term python ${PYTHONPATH}/chat_my_assistant/chatme.py -c PRO
    sleep 1  " sleepしないとプロンプトの前に貼り付けられてしまう
    normal! "xp
    execute "normal! a<CR>"
endfunction

vnoremap <leader>c :call Chat()<CR>
