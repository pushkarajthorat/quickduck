'''
Created on 27-Oct-2022

@author: pushkarajthorat
'''
import math


class color():

    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
        self.propotion = tuple(self.get_propotion())

    def get_propotion(self):
        gcd = math.gcd(self.r, self.g, self.b)
        return map(lambda x: x / gcd, [self.r, self.g, self.b])

    def __eq__(self, other):
        return self.propotion == other.propotion

    def __ne__(self, other):
        return self.propotion != other.propotion

    def __hash__(self):
        return self.propotion.__hash__()

    def __repr__(self):
        return f"\n({self.r},{self.g},{self.b})"


def valid_color(r, g, b):
    non_negative = list(filter(lambda x:x != 0, [r, g, b]))
    if(len(non_negative) == 3 or len(non_negative) == 2):
        return True
    elif(len(non_negative) == 1):
        l = [r, g, b]
        l.sort(reverse=True)
        if l[0] == 1:
            return True
        return False


def find_color_combinations(red, green, blue):
    color_set = []
    for i in range(red + 1):
        for j in range(green + 1):
            for k in range(blue + 1):
                if valid_color(i, j, k):  # removes 0,0,0 .. 2,0,0 etc
                    c = color(i, j, k)
                    if c not in color_set:
                        color_set.append(c);
    return color_set

def find_longest_path(r, g, b, used_colors=[]):
    choosen_color_sequence = []
    for c in find_color_combinations(r, g, b):
        if c not in used_colors:
            max_color_sequence = find_longest_path(r - c.r, g - c.g, b - c.b, used_colors+[c])
            max_color_sequence = [c] + max_color_sequence
            if len(choosen_color_sequence) < len(max_color_sequence):
                choosen_color_sequence = max_color_sequence
    return choosen_color_sequence


print(find_longest_path(5, 4, 4, []))

