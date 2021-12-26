import hashlib
import time

tasks = [1, 2, 3, 4, 5, 3, 5, 1, 5, 4]

if __name__ == '__main__':
    test = [(1, b'123'), (1, b'123'), (2, b'123')]
    test = list(set(test))
    print(test)