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
    vs | term chatme -c PRO
    sleep 1  " sleepしないとプロンプトの前に貼り付けられてしまう
    normal! "xpA
    " execute "normal! a"
    set nopaste
    set ft=markdown
endfunction

vnoremap <leader>c :call Chat()<CR>
nnoremap <leader>c :call Chat()<CR>
