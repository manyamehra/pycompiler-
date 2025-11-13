.start
resn 12
.sumArray
resn 2
push 0
dup
set 11
drop 1
push 0
dup
set 12
drop 1
.L0
get 12
get 0
cmplt
jumpf L1
push 1
get 12
add
get 12
write
get 11
push 1
get 12
add
read
add
dup
set 11
drop 1
get 12
push 1
add
dup
set 12
drop 1
jump L0
.L1
get 11
ret
ret
drop 13
halt
.end
