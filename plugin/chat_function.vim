" 範囲選択してleader cを実行すると、
" レジスタにInsertモードで
" usage:
" source chat_function.vim
" :'<,'>call Chat()
function! Chat()
    " 改行を勝手に挿入しない
    set paste
    " 選択範囲をレジスタxへ格納
    normal! gv"xy
    vs | term python3 ${PYTHONPATH}/chat_my_assistant/chatme.py -c PRO
    sleep 1  " sleepしないとプロンプトの前に貼り付けられてしまう
    normal! "xpA
    " execute "normal! a"
    set nopaste
endfunction

vnoremap <leader>c :call Chat()<CR>
nnoremap <leader>c :call Chat()<CR>
