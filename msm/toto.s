.start
resn 1
.carre
push BP
move SP, BP
get 0
get 0
mul
pop BP
ret
pop BP
ret
prep carre
push 4
call 1
dup
set 1
drop 1
get 1
send
drop 2
halt
.end