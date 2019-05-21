# -*- coding: utf-8 -*-

# key_4s - четыре символа ключа
def get_hash_2b(key_4s):
	# Правило преобразования байта
	def transform(b):

		# numbers -.
		if b <= 0x39:
			r = b - 0x30
		# Letter case and @
		else:
			# @ABCDEF
			if b <= 0x46:
				r = b - 0x37
			else:
				# WXYZ
				if b >= 0x57:
					r = b - 0x57
				# GHIJKLMNOPQRSTUV
				else:
					r = 0xff - (0x57 - b) + 1  # a9+b

		return r

	# Перевод в байты
	key_4b = bytearray(key_4s, encoding="ascii")

	# Каждый байт аргумента трансформируется
	codes = [transform(b) for b in key_4b]

	# А здесь они просто склеиваются
	part0 = (codes[0] & 0xff) << 0xc
	part1 = (codes[1] << 0x8) & 0xf00
	part2 = (codes[2] << 0x4) & 0xf0
	hash_2b = (part0 | part1) & 0xffff
	hash_2b = (hash_2b | part2) & 0xffff
	hash_2b = (hash_2b | (codes[3] & 0xf))

	return hash_2b

def decode_hash_4s(hash_2b):

	# Правило преобразования байта
	def transform(b):
		if b <= 0x9:
			return b + 0x30
		if b <= 0xF:
			return b + 0x37
		if b >= 0x0:
			return b + 0x57
		return b - 0xa9

	# Нарезаем отдельные байты из переданого хэша и переводи
	b0 = transform(hash_2b >> 12)
	b1 = transform((hash_2b & 0xfff) >> 8)
	b2 = transform((hash_2b & 0xff) >> 4)
	b3 = transform(hash_2b & 0xf)

	# Склеиваем
	key_4s = [chr(b0), chr(b1), chr(b2), chr(b3)]
	key_4s = "".join(key_4s)

	return key_4s

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

def finish_hash(hash_2b):

	# Правило преобразования хэша
	def transform(hash_2b):
		new = hash_2b >> 1

		if hash_2b & 0b1 != 0:
			new = new | 0x8000

		return new

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

			d1 = hash_2b & 0xff
			d2 = d0 ^ d1

			curr_sub_E3E_result = sub_E3E(prev_sub_E3E_result, d2, d2_storage)
			prev_sub_E3E_result = curr_sub_E3E_result

		storage_offset = storage_offsets.pop(0)

		for _ in range(c[1]):

			d2 = d2_storage[-storage_offset]

			curr_sub_E3E_result = sub_E3E(prev_sub_E3E_result, d2, d2_storage)
			prev_sub_E3E_result = curr_sub_E3E_result

		hash_2b = transform(hash_2b)

	return curr_sub_E3E_result

def find_CB4C():

	result = []

	for hash_2b in range(0xFFFF+1):
		final_hash = finish_hash(hash_2b)
		if final_hash == 0xCB4C:
			result.append(hash_2b)

	return result

def get_first_half():

	from collections import deque
	from random import randint

	def get_pairs():

		pairs = []

		for i in range(0xFFFF + 1):
			pair = (i, i ^ 0xFEDC)
			pairs.append(pair)

		pairs = deque(pairs)
		pairs.rotate(randint(0, 0xFFFF))

		return list(pairs)

	pairs = get_pairs()

	for pair in pairs:

		key_4s_0 = decode_hash_4s(pair[0])
		key_4s_1 = decode_hash_4s(pair[1])

		hash_2b_0 = get_hash_2b(key_4s_0)
		hash_2b_1 = get_hash_2b(key_4s_1)

		if hash_2b_0 == pair[0] and hash_2b_1 == pair[1]:
			return key_4s_0, key_4s_1

def get_second_half(email):

	from collections import deque
	from random import randint

	def get_koeff():
		k1 = sum([ord(c) for c in email])
		k2 = (len(email) - 1) << 8

		return k1, k2

	def get_pairs(k1, k2):
		pairs = []

		for a in range(0xFFFF + 1):
			pair = (a, (a ^ k1) ^ k2)
			pairs.append(pair)

		pairs = deque(pairs)
		pairs.rotate(randint(0, 0xFFFF))

		return list(pairs)

	k1, k2 = get_koeff()

	pairs = get_pairs(k1, k2)

	for pair in pairs:

		key_4s_0 = decode_hash_4s(pair[0])
		key_4s_1 = decode_hash_4s(pair[1])

		hash_2b_0 = get_hash_2b(key_4s_0)
		hash_2b_1 = get_hash_2b(key_4s_1)

		if hash_2b_0 == pair[0] and hash_2b_1 == pair[1]:
			return key_4s_0, key_4s_1

def keygen(email):

	first_half = get_first_half()
	second_half = get_second_half(email)

	return "".join(first_half) + "".join(second_half)
