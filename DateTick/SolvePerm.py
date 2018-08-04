
# Index location
# |       | one   | two   |     |
# | three | four  | five  | six |
# |       | seven | eight |     |

import itertools

array = [1,2,3,4,5,6,7,8]
adjecent = [(1,4),(4,7),(2,5),(5,8),(1,2),(3,4),(4,5),(5,6),(7,8)]

adjecent_normalized = [ (x - 1, y - 1) for (x, y) in adjecent]

def validate(perm, adjecent):
    for (x, y) in adjecent:
        if abs(perm[x] - perm[y]) == 1: return False
    return True

def print_permutation(perm):
    print """
    |   | {} | {} |   |
    | {} | {} | {} | {} |
    |   | {} | {} |   |
    """.format(*perm)

total_solutions=0
for perm in itertools.permutations(array):
    if validate(perm, adjecent_normalized):
        print_permutation(perm)
        total_solutions += 1

print "total_solutions {}".format(total_solutions) 


#     |   | 8 | 6 |   |
#     | 5 | 1 | 4 | 2 |
#     |   | 3 | 7 |   |
#     
# 
#     |   | 8 | 6 |   |
#     | 7 | 4 | 1 | 3 |
#     |   | 2 | 5 |   |
#     
# 
#     |   | 8 | 6 |   |
#     | 7 | 5 | 1 | 3 |
#     |   | 2 | 4 |   |
#     
# total_solutions 1656

