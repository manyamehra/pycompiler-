.start
resn 1
push 0
dup
set 0
drop 1
.L3
get 0
push 5
cmplt
jumpf L4
get 0
send
get 0
push 1
add
dup
set 0
drop 1
jump L3
.L4
drop 1
halt
.end