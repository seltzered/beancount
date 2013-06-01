"""
A version of bisect that accepts a custom key function, like the sorting ones do.
"""
import random
import unittest


def bisect_left_withkey(sequence, value, key=None):
    """Find the last element before the given date.
    Return the index. May return None"""

    if key is None:
        key = lambda x: x

    lo = 0
    hi = len(sequence)

    while lo < hi:
        mid = (lo + hi) // 2
        if key(sequence[mid]) < value:
            lo = mid + 1
        else:
            hi = mid
    return lo



class TestBisectWithKey(unittest.TestCase):


    def test_bisect_left_withkey(self):
        second = lambda x: x[1]

        data = [(random.random(), i) for i in range(100)]
        index = bisect_left_withkey(data, 40, key=second)
        self.assertEqual(index, 40)
        self.assertEqual(data[index][1] , 40)

        index = bisect_left_withkey(data, 0, key=second)
        self.assertEqual(index, 0)
        self.assertEqual(data[index][1] , 0)

        index = bisect_left_withkey(data, -1, key=second)
        self.assertEqual(index, 0)
        self.assertEqual(data[index][1] , 0)

        index = bisect_left_withkey(data, 99, key=second)
        self.assertEqual(index, 99)

        index = bisect_left_withkey(data, 100, key=second)
        self.assertEqual(index, 100)

        index = bisect_left_withkey(data, 999, key=second)
        self.assertEqual(index, 100)

    def test_bisect_repeats(self):
        data = [('a', 0), ('b', 0), ('c', 1), ('d', 3), ('e', 4), ('f', 4), ('g', 5), ('h', 6)]
        index = bisect_left_withkey(data, 4, key=lambda x: x[1])
        self.assertEqual(index, 4)
        self.assertEqual(data[index][0], 'e')
