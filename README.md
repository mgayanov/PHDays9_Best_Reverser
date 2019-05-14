# PHDays9_Best_Reverser

## sub_5EC ##

Значимый кусок кода:

```asm
move.l 0x2c(a2), d0
move.l       d0, d1
addq.l        1, d1
move.l       d1, 0x2c(a2)
movea.l      d0, a0
move.b     (a0), d0
```

где 0x2c(a2) всегда 0x00FF1D74

Этот кусок можно переписать так на псевдокоде:

```c
d0 = a2 + 0x2C
*(a2+0x2C) = *(a2+0x2C) + 1
result = *(d0) & 0xFF
```

То есть 4 байта из 0x00FF1D74 являются адресом, т.к. по ним извлекается значение из памяти.

