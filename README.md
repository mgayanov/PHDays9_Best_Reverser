# PHDays9_Best_Reverser

## sub_5EC ##

Значимый кусок кода:

```asm
move.l 0x2c(a2), d0
move.l d0, d1
addq.l 1, d1
move.l d1, 0x2c(a2)
movea.l d0, a0
move.b (a0), d0
```

где 0x2c(a2) = 0x00FF1D74
