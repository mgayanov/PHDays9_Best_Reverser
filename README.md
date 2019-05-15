# PHDays9_Best_Reverser

## sub_5EC ##

Значимый кусок кода:

<p align="center">
<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/sub_5EC.png">
</p>

где 0x2c(a2) **всегда 0x00FF1D74**

Этот кусок можно переписать так на псевдокоде:

```c
d0 = a2 + 0x2C
*(a2+0x2C) = *(a2+0x2C) + 1
result = *(d0) & 0xFF
```

То есть 4 байта из 0x00FF1D74 являются адресом, т.к. по ним извлекается значение из памяти.

Как переписать функцию sub_5EC на питоне?

1. Либо сделать дамп памяти и обращаться к нему
2. Либо просто записать все выдаваемые значения

Второй способ выглядит здорово, но что, если при разных данных авторизации выдаваемые значения разные?
Проверим это.

Поможет в этом скрипт

```c
#include <idc.idc>

static main()
{
    auto pc_val=0, d0_val;
    while(pc_val != 0x00001F16){
        
        pc_val = GetRegValue("pc");
        
        if (pc_val == 0x00001F9C)
            StepInto();
        else
            StepOver();
            
        GetDebuggerEvent(WFNE_SUSP, -1);
    
        if (pc_val == 0x00000674){
            d0_val = GetRegValue("d0") & 0xFF;
            print(d0_val);
        }
    }
}
```

Запустив скрипт несколько раз при разных ключах, мы видим, что функция sub_5EC всегда возвращает очередное значение из массива:

```python
def sub_5EC():
  dump = [0x92, 0x8A, 0xDC, 0xDC, 0x94, 0x3B, 0xE4, 0xE4,
          0xFC, 0xB3, 0xDC, 0xEE, 0xF4, 0xB4, 0xDC, 0xDE,
          0xFE, 0x68, 0x4A, 0xBD, 0x91, 0xD5, 0x0A, 0x27,
          0xED, 0xFF, 0xC2, 0xA5, 0xD6, 0xBF, 0xDE, 0xFA,
          0xA6, 0x72, 0xBF, 0x1A, 0xF6, 0xFA, 0xE4, 0xE7,
          0xFA, 0xF7, 0xF6, 0xD6, 0x91, 0xB4, 0xB4, 0xB5,
          0xB4, 0xF4, 0xA4, 0xF4, 0xF4, 0xB7, 0xF6, 0x09,
          0x20, 0xB7, 0x86, 0xF6, 0xE6, 0xF4, 0xE4, 0xC6,
          0xFE, 0xF6, 0x9D, 0x11, 0xD4, 0xFF, 0xB5, 0x68,
          0x4A, 0xB8, 0xD4, 0xF7, 0xAE, 0xFF, 0x1C, 0xB7,
          0x4C, 0xBF, 0xAD, 0x72, 0x4B, 0xBF, 0xAA, 0x3D,
          0xB5, 0x7D, 0xB5, 0x3D, 0xB9, 0x7D, 0xD9, 0x7D,
          0xB1, 0x13, 0xE1, 0xE1, 0x02, 0x15, 0xB3, 0xA3,
          0xB3, 0x88, 0x9E, 0x2C, 0xB0, 0x8F]
          
  l = len(dump)
  offset = 0
  
  while offset < l:
    yield dump[offset]
    offset += 1
  
```

Итак функция sub_5EC готова

## sub_E3E ##

Значимый кусок кода:

<p align="center">
<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/sub_E3E_1.png">
</p>

Расшифруем

```c

Эта конструкция выдает адрес, куда сохранять d2, который сейчас содержит входной аргумент
Регистр a2 хранит значение 0xFF1D48, a2 + 0x34 = 0xFF1D7C
d0 = *(a2 + 0x34)
*(a2 + 0x34) = *(a2 + 0x34) + 1

Входной аргумент сохраняется, в регистре a0 адрес этого сохранения
a0 = d0
*(a0) = d2

Здесь вычисляется некий offset, который сохраняется в регистре d2
Регистр a2 хранит значение 0xFF1D48, a2 + 0x24 = 0xFF1D6C - это место, где хранится
предыдущий результат функции(см. конец)
d0 = *(a2 + 0x24)
d2 = d0 ^ d2
d2 = d2 & 0xFF
d2 = d2 + d2

Вытаскиваются какие-то данные по адресу 0x00011FC0 + d2, это область ROM, поэтому
содержимое 0x00011FC0 + d2 постоянно
a0 = 0x00011FC0
d2 = *(a0 + d2)

Предыдущий результат этой функции сдвигается на 8 бит
d0 = d0 >> 8

Результат
d2 = d0 ^ d2

Записывается текущий результат функции
*(a2 + 0x24) = d2
```

Функция sub_E3E сводится к таким шагам:
1. Сохранить входной аргумент в массив
2. Рассчитать смещение offset
3. Вытащить 2 байта из каких-то данных по адресу 0x00011FC0 + offset(ROM)
4. Результат = (предыдущий результат >> 8) ^ (какие-то данные из 0x00011FC0 + offset)

Предствим функцию sub_E3E в таком виде:

```python

def sub_E3E(prev_xored, d2, d2_storage):

	def calc_offset():
		return 2 * ((prev_xored^d2) & 0xff)
        
    	d2_storage.append(d2)
    
    	offset = calc_offset()

	with open("dump_00011FC0", 'rb') as f:
		dump_00011FC0_4096b = f.read()

	some = dump_00011FC0_4096b[offset:offset+2]
	some = int.from_bytes(some, byteorder="big")

	prev_xored = prev_xored >> 8

	return prev_xored ^ some

```

dump_00011FC0 - это просто файл, куда я сохранил 4096 байт [0x00011FC0:00011FC0+4096]

