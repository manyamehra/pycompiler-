.start
resn 6
push 0
dup
set 5
drop 1
.L6
get 5
push 5
cmplt
jumpf L7
push 0
get 5
add
get 5
push 10
mul
write
get 5
push 1
add
dup
set 5
drop 1
jump L6
.L7
push 0
dup
set 5
drop 1
.L8
get 5
push 5
cmplt
jumpf L9
push 0
get 5
add
read
send
get 5
push 1
add
dup
set 5
drop 1
jump L8
.L9
drop 6
halt
.end