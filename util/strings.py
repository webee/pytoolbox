# coding=utf-8
import string
import random


def gen_rand_str(size=32, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
