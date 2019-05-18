# PHDays9_Best_Reverser

# Осматриваемся #

Программа принимает не всякий ключ: ключ обязательно должен быть 16 символов.
Если ключ короче, то вы увидите сообщение: "Wrong length! Try again…"

Попробуем найти эту строчку в программе, для чего воспользуемся бинарным поиском(Alt-B).
Что мы найдем?

Найдем не только эту, но и рядом остальные служебные строки: "Wrong key! Try again…" и "YOU ARE THE BEST REVERSER!".

<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/wrong_len.png">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/wrong_key.png">
</p>

Ярлыки WRONG_LENGTH_MSG, YOU_ARE_THE_BEST_MSG и WRONG_KEY_MSG создал я.


Поставим брейк на чтение адреса 0x0000FDFA - выясним, кто работает с сообщением "Wrong length! Try again…".
И запустим отладчик.
(Он несколько раз остановится еще до того как можно будет вводить ключ, просто жмем F9 на каждой остановке).
Вводим свой email, ключ ABCD.


Отладчик приводит на 0x00006FF0 `tst.b (a1)+`

<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/loc_6FF0.png">
</p>

Ничего интересного в самом блоке нет. Гораздо интереснее, кто передает управление сюда.
Смотрим колл стэк:

<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/callstack_wronglen.png">
</p>

Жмем и попадем сюда - на инструкцию 0x00001D2A `jsr (sub_6FC0)`:
<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/result_branches.png">
</p>

Видим, что все возможные сообщения нашлись в одном месте.
Но давайте узнаем, откуда передается управление в блок `WRONG_KEY_LEN_CASE_1D1C`.
Не будем ставить брейки, просто наведем курсор на стрелку, идущую к блоку.
Вызывающий расположился на адресе 0x000017DE `loc_17DE`(который я переименую в `CHECK_KEY_LEN`).
<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/checklen_loc.png">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/check_key_len.png">
</p>

Поставим брейк на адрес 0x000017EC `cmpi.b 0x20 (a0, d0.l)`(здесь принимается решение о валидности длины),
перезапустимся, снова введем почту и ключ ABCD.
Отладчик останавливается и показывает, что по адресу 0x00FF01C7(хранящемуся в этот момент в регистре `a0`) находится введенный ключ.
<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/check_key_len_debug_0.png">
</p>

Это хорошая находка, через нее мы выцепим вообще все.
Но сначала разметим байты ключа для удобства.
<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/key_storage.png">
</p>

Прокрутив вверх с этого места, увидим что почта хранится рядом с ключем.
<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/email_storage.png">
</p>

Мы погружаемся все глубже и глубже, и пришло время найти схему проверки ключа.
Это будет еще более глубокое погружение.

# Схема проверки ключа #

## Предварительные вычисления ##
Логично предположить, что сразу после проверки длины последуют другие операции с ключем.
Рассмотрим блок сразу за проверкой:

<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/check_key_8b.png">
</p>

В этом блоке идет предварительная работа.
Функция `get_hash_4b`(в оригинале было `sub_1526`) вызывается дважды.
Сначала ей передается адрес первого байта ключа(регистр `a0` содержит адрес `KEY_BYTE_0`), во второй раз - пятого(`KEY_BYTE_4`).

Я назвал функцию так, потому что она считает что-то типа хэша.
Это самое понятное название, которое я подобрал.

Саму функцию рассматривать я не буду, а сразу напишу ее на питоне.
Она делает простые вещи, но ее описание со скринами займет много места.

Самое важное, что о ней нужно сказать, - на вход подается адрес, и работа идет над 4-мя байтами от этого адреса.
То есть подали на вход первый байт ключа, а функция будет работать с 1,2,3,4-ым.
Результат пишется в регистр d0.

Итак, функция get_hash_4b:

```python
#key_4s - четыре символа ключа
def get_hash_4s(key_4s):
	
	#Правило преобразования байта
	def transform(b):
	
		#numbers -.
		if b <= 0x39:
			r = b - 0x30
		#Letter case or @
		else:
			#@ABCDEF
			if b <= 0x46:
				r = b - 0x37
			else:
				#WXYZ
				if b >= 0x57:
					r = b - 0x57
				#GHIJKLMNOPQRSTUV
				else:
					r = 0xff - (0x57-b) + 1 #a9+b

		return r
		
	#Перевод в байты
	key_4b = bytearray(key_4s, encoding="ascii")
	
	#Каждый байт аргумента трансформируется
	codes = [transform(b) for b in key_4b]
	
	#А здесь просто склеивается
	part0 = (codes[0] & 0xff) << 0xc
	part1 = (codes[1] << 0x8) & 0xf00
	part2 = (codes[2] << 0x4) & 0xf0
	r = (part0 | part1) & 0xffff
	r = (r | part2) & 0xffff
	r = (r | (codes[3] & 0xf))

	return r
	
>>> first_hash = get_hash_4s("ABCD")
>>> hex(first_hash)
0xabcd

>>> second_hash = get_hash_4s("EFGH")
>>> hex(second_hash)
0xef01

```

Проверим.
Нас интересует состояние регистра `d0` после выполнения функции.
Ставим брейки на `0x000017FE`, `0x00001808`, ключ ABCDEFGHIJKLMNOP.

<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/first_key_hash.png">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/second_key_hash.png">
</p>

В регистр `d0` заносятся значения `0xabcd`, `0xef01`, проверка пройдена.

Далее производится xor `eor.w d0, d5`, результат заносится в `d5`:

```python
>>> hex(0xabcd ^ 0xef01)
0x44cc
```

В получении такого хэша `0x44cc` и состоят предварительные вычисления.
Далее все только усложняется.

## Куда уплывает предварительный хэш ##

Нам никак не пройти дальше, если мы не узнаем как программа работает с предварительным хэшем.
Наверняка он перемещается из d5 в память, т.к. регистр d5 пригодится где-нибудь еще.
Отыскать такое событие мы можем через трассировку(наблюдая за d5), но не ручную, а автоматическую.
Поможет такой скрипт:

```c
#include <idc.idc>

static main()
{
	auto d5_val;
	auto i;
	for(;;)
	{
		StepOver();
		GetDebuggerEvent(WFNE_SUSP, -1);
		d5_val = GetRegValue("d5");
		if (d5_val != 0xFFFF44CC){
			break;
		}
	}
}

```

Скрипт остановился на инструкции 0x00001C94, в d5 лежит 0.
Но мы видим, что значение из d5 перемещается на инструкции 0x00001C56: оно пишется в память по адресу 0x00FF0D46(2 байта).

Отловим инструкции, которые читают из 0x00FF0D46-0x00FF0D47(ставим брейк).
Попались 4 кандидата
<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/read_from_0d46.png">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/read_from_0d46_1.png">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/read_from_0d46_2.png">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/read_from_0d46_3.png">
</p>

Неизвестно какие из них интересны. Это тупик.

Вернемся в начало.

<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/result_branches.png">
</p>

# Первый важный цикл loc_1F94 #


<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/loc_1F94_1.png">
</p>

На что обратить внимание:
1. есть функция sub_5EC
2. инструкция jsr (a0) вызывает функцию sub_E3E(это можно увидеть простой трассировкой, поставив рядом брейк)

Что здесь происходит:
1. Функция sub_5EC пишет результат своего выполнения в регистр d0(показно ниже)
2. В регистр d1 сохраняется байт по адресу sp+0x33(0x00FFFF79 говорит нам отладчик), это второй байт из адреса хэша первой половины ключа(0x00FF0D47)
Это легко доказать, если поставить брейк на запись по адресу 0x00FFFF79: брейк сработает на инструкции move.b 1(a2), 0x2F(sp).
В регистре a2 в этот момент хранится адрес 0x00FF0D46 - адрес хэша, 0x00FF0D46 + 1 - адрес второго байта
3. В регистр d0 пишется d0^d1
4. Получившийся результат xor'a отдается в функцию sub_E3E, поведение которой зависит от своих прежних вычислений(показано ниже)
5. Повторить

Сколько же раз этот цикл выполняется?

Высним это.
Запустим такой скрипт:

```c
#include <idc.idc>

static main()
{
	auto pc_val, d4_val, counter=0;
	while(pc_val != 0x00001F16)
	{
		StepOver();
		GetDebuggerEvent(WFNE_SUSP, -1);
		pc_val = GetRegValue("pc");
		if (pc_val == 0x00001F92){
			counter++;
			d4_val = GetRegValue("d4");
			print(d4_val);
		}
	}
	print(counter);
}

```

Скрипт выведет в консоль, что цикл запустится 9 раз с количеством итераций: 17, 2, 2, 3, 4, 38, 10, 30, 4, 9


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
Регистр a2 хранит значение 0xFF0D46, a2 + 0x34 = 0xFF0D7A
d0 = *(a2 + 0x34)
*(a2 + 0x34) = *(a2 + 0x34) + 1

Входной аргумент сохраняется, в регистре a0 адрес этого сохранения
a0 = d0
*(a0) = d2

Здесь вычисляется некий offset, который сохраняется в регистре d2
Регистр a2 хранит значение 0xFF0D46, a2 + 0x24 = 0xFF0D6A - это место, где хранится
предыдущий результат функции(см. конец) либо 0x00000000, если функция вызывается впервые
d0 = *(a2 + 0x24)
d2 = d0 ^ d2
d2 = d2 & 0xFF
d2 = d2 + d2

Вытаскиваются какие-то 2 байта по адресу 0x00011FC0 + d2, это область ROM, поэтому
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
3. Вытащить 2 байта по адресу 0x00011FC0 + offset(ROM)
4. Результат = (предыдущий результат >> 8) ^ (2 байта 0x00011FC0 + offset)

Представим функцию sub_E3E в таком виде:

```python

def sub_E3E(prev_sub_E3E_xored, d2, d2_storage):

	def calc_offset():
		return 2 * ((prev_sub_E3E_xored^d2) & 0xff)
        
    	d2_storage.append(d2)
    
    	offset = calc_offset()

	with open("dump_00011FC0", 'rb') as f:
		dump_00011FC0_4096b = f.read()

	some = dump_00011FC0_4096b[offset:offset+2]
	some = int.from_bytes(some, byteorder="big")

	prev_sub_E3E_xored = prev_sub_E3E_xored >> 8

	return prev_sub_E3E_xored ^ some

```

dump_00011FC0 - это просто файл, куда я сохранил 4096 байт [0x00011FC0:00011FC0+4096]

# Активность около 1FC4 #

<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/1FC4.png">
</p>

Этот блок меняет содержимое по адресу 0x00FF0D46(регистр a2), а именно там хранится хэш первой половины ключа.
Посмотрим что здесь происходит.

1. Условие, которое определяет, будет выбрана левая или правая ветка, такое: (хэш первой половины ключа) & 0b1 != 0.
То есть проверяется первый бит хэша.
2. Если присмотреться к обоим веткам, станет видно:
* в обоих случаях происходит сдвиг вправо на 1 бит
* в левой ветке над хэшем производится операция ИЛИ 0x8000
* в обоих случаях по адресу 0x00FF0D46 записывается обработанное значение хэша
* дальнейшие вычисления некритичны, потому что, грубо говоря, нет операций записи в (a2)

Представим блок так:

```python
def transform_input_xored(xored):
	new_xored = xored >> 1

	if xored_w & 0b1 != 0:
		new_xored = new_xored | 0x8000

	return new_xored
```


# Второй важный цикл loc_203E #


<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/loc_203E.png">
</p>

Этот цикл досчитывает хэш и вот его главная особенность:
jsr (a0) - это вызов функции sub_E3E, которую мы уже рассмотрели - она опирается на предыдущий результат
своей же работы и на некий входной аргумент(выше он передавался через регистр d2, здесь - через d0)

Давайте выясним, что передается ей через регистр d0.

Мы уже встречались с адресом 0x34(a2) - туда функция sub_E3E сохраняет переданный ей аргумент.
Значит, в этом цикле используются ранее переданные аргументы. Но не все так просто.

Расшифруем часть кода:

```c

Здесь берется 2 байта из адреса a2+0x1C
move.w 0x1C(a2), d0

Инвертируется
neg.l d0

В регистр a0 пишется адрес последнего сохраненного аргумента функции sub_E3E
movea.l 0x34(a2), a0

Наконец, в d0 пишутся 2 байта по адресу a0-d0(вычитание потому что d0 инвертирован)
move.b (a0, d0.l), d0
```

Суть сводится к простому действию: на каждой итерации взять d0 сохраненный аргумент с конца массива.
И стоит помнить, что массив меняется на каждой итерации.

Раз так, то какие конкретно принимает значения d0?
Здесь я обошелся без скриптов, просто выписал их на бумажке по ходу трассировки.
Вот они: 0x04, 0x04, 0x04, 0x1C, 0x1A, 0x1A, 0x06, 0x42, 0x02

Теперь у нас есть все, чтобы написать полную функцию вычисления хэша первой половины ключа.

```python
def sub_5EC_gen():
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


def sub_E3E(prev_sub_E3E_result, d2, d2_storage):
	def calc_offset():
		return 2 * ((prev_sub_E3E_result ^ d2) & 0xff)

	d2_storage.append(d2)

	offset = calc_offset()

	with open("dump_00011FC0", 'rb') as f:
		dump_00011FC0_4096b = f.read()

	some = dump_00011FC0_4096b[offset:offset + 2]
	some = int.from_bytes(some, byteorder="big")

	prev_sub_E3E_result = prev_sub_E3E_result >> 8

	return prev_sub_E3E_result ^ some


def transform_key_hash(key_hash_p1):
	new = key_hash_p1 >> 1

	if key_hash_p1 & 0b1 != 0:
		new = new | 0x8000

	return new


def sign_key_hash(key_hash_p1):

	main_cycle_counter = [17, 2, 2, 3, 4, 38, 10, 30, 4]
	second_cycle_counter = [2, 2, 2, 2, 2, 4, 2, 4, 28]
	counters = list(zip(main_cycle_counter, second_cycle_counter))

	d2_storage = []
	storage_offsets = [0x04, 0x04, 0x04, 0x1C, 0x1A, 0x1A, 0x06, 0x42, 0x02]

	prev_sub_E3E_result = 0x0000

	sub_5EC = sub_5EC_gen()

	for i in range(9):

		c = counters[i]

		for _ in range(c[0]):
			d0 = next(sub_5EC)

			d1 = key_hash_p1 & 0xff

			d2 = d0 ^ d1

			curr_sub_E3E_result = sub_E3E(prev_sub_E3E_result, d2, d2_storage)

			prev_sub_E3E_result = curr_sub_E3E_result

		storage_offset = storage_offsets.pop(0)

		for _ in range(c[1]):

			d2 = d2_storage[-storage_offset]

			curr_sub_E3E_result = sub_E3E(prev_sub_E3E_result, d2, d2_storage)

			prev_sub_E3E_result = curr_sub_E3E_result

		key_hash_p1 = transform_key_hash(key_hash_p1)

	return curr_sub_E3E_result

```

## Проверка работоспособности ##

1. В отладчике ставим брейк на адрес 0x0000180A(сразу после вычисления предварительного хэша)
2. В отладчике ставим брейк на адрес 0x00001F16(сравнение окончательного хэша с константой 0xCB4C)
3. В программе вводим ключ ABCDEFGHIJKLMNOP, жмем Enter
4. Отладчик останавливается, и мы видим, что в регистр d5 записалось значение 0xFFFF44CC, 0x44CC - предварительный хэш
5. Запускаем отладчик дальше
6. Останавливаемся на 0x00001F16 и видим, что по адресу 0xFF1D6C лежит 0x4840 - окончательный хэш
7. Теперь проверям нашу функцию sign_key_hash(key_hash_p1):
```python
>>> r = sign_key_hash(0x44CC)
>>> print(hex(r))
0x4840
```

# Ищем правильный ключ 1 #

Правильный ключ - этот ключ, у которого окончательный хэш равен 0xCB4C
Отсюда вопрос: каким должен быть предварительный хэш, чтобы окончательный стал 0xCB4C?

Теперь это просто выяснить:

```python

result = []

for h1 in range(0x0000, 0xFFFF+1):

	h2 = sign_key(h1)

	if h2 == 0xCB4C:
		result.append(h2)

print(result)

```

Вывод программы говорит о том, что предварительный хэш должен быть 0xFEDC

Теперь главный вопрос звучит так: какие символы надо ввести, чтобы их предварительный хэш равнялся 0xFEDC?

Так как предварительный хэш = process_key(first_4b) ^ process_key(second_4b), то найти нужно только
first_4b, потому что second_4b = first_4b ^ 0xFEDC

Единственное, что ограничивает, это то, что байты должны соответствовать символам.

Алгоритм такой:

```python

def encode(key_s):

	def make(b):
		r = 0

		#numbers -.
		if b <= 0x39:
			r = b - 0x30
		#Letter case or @
		else:
			#@ABCDEF
			if b <= 0x46:
				r = b - 0x37

			else:
				#WXYZ
				if b >= 0x57:
					r = b - 0x57
				#GHIJKLMNOPQRSTUV
				else:
					r = 0xff - (0x57-b) + 1 #a9+b

		return r

	key_b = bytearray(key_s, encoding="ascii")

	codes = [make(b) for b in key_b]

	part0 = (codes[0] & 0xff) << 0xc

	part1 = (codes[1] << 0x8) & 0xf00

	part2 = (codes[2] << 0x4) & 0xf0

	r = (part0 | part1) & 0xffff

	r = (r | part2) & 0xffff

	r = (r | (codes[3] & 0xf))

	return r

def decode(h):

	def a(b):
		if b <= 0x9:
			return b + 0x30

		if b <= 0xF:
			return b + 0x37

		if b >= 0x0:
			return b + 0x57

		return b - 0xa9

	p0 = a(h >> 12)

	p1 = a((h & 0xfff) >> 8)

	p2 = a((h & 0xff) >> 4)

	p3 = a(h & 0xf)

	result = [chr(p0), chr(p1), chr(p2), chr(p3)]

	return "".join(result)
	
#Найдем все пары
def find_pairs():
	pairs = []

	for i in range(0xFFFF+1):
		pair = (i, i ^ 0xFEDC)
		pairs.append(pair)

	return pairs
	
pairs = find_pairs()

#Найдем только правильные
for pair in pairs:
	p0_s = decode(pair[0])
	p1_s = decode(pair[1])

	p0_b = encode(p0_s)
	p1_b = encode(p1_s)
	
	#Я не уверен в функции декодирования, поэтому этот шаг необходим
	if p0_b == pair[0] and p1_b == pair[1]:
		print(p0_s, p1_s)

```

Вариантов куча. Я выберу "FE3A00E6".

# Ищем правильный ключ 2 #

Первая половина ключа готова, что со второй?

Эта часть горзадо легче.
Ответственный кусок кода располагается на 0x00FF2012

<p align="center">
	<img src="https://github.com/mgayanov/PHDays9_Best_Reverser/blob/master/img/loc_FF2012.png">
</p>

Сделаем его понятнее:

```
while(d1 != 0x20){
	#Подсчитывается длина почты
	d2++
	d1 = d1 & 0xFF
	
	#Подсчитывается сумма байтов почты
	d3 = d3 + d1
	d0 = 0
	d0 = d2
	
	#Очередной байт почты
	d1 = *(a0+d0)
}

d0 = handle_key_bytes(key_byte_8)
d3 = d0^d3

d0 = handle_key_bytes(key_byte_12)
d2 = d2 - 1
d2 = d2 << 8
d2 = d0^d2

if (d2 == d3)
	success_branch

```

d2 - (длина почты-1) <<8
d3 - сумма байтов почты

Критерий корректности: половина_ключа_1^d2=половина_ключа_2^d3

```python
def get_second_half(email):

	from random import randint

	def get_koeff():
		k1 = sum([ord(c) for c in email])
		k2 = (len(email) - 1) << 8

		return k1, k2

	def get_pairs(k1, k2):
		pairs = []

		for a in range(0xFFFF+1):
			pair = (a, (a^k1)^k2)
			pairs.append(pair)

		return pairs

	k1, k2 = get_koeff()

	pairs = get_pairs(k1, k2)

	pair = pairs[randint(0, len(pairs))]

	p0 = hex(pair[0])[2:]
	p1 = hex(pair[1])[2:]

	return p0 + p1

```
