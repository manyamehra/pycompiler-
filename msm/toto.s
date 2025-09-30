.start
resn 1
push 0
dup
set 0
drop 1
.L0
get 0
push 5
cmplt
jumpf L1
get 0
send
get 0
push 1
add
dup
set 0
drop 1
jump L0
.L1
drop 1
halt
