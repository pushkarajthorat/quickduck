
# Index location
# |       | one   | two   |     |
# | three | four  | five  | six |
# |       | seven | eight |     |

import itertools

array = [1,2,3,4,5,6,7,8]
adjecent = [(1,4),(4,7),(2,5),(5,8),(1,2),(3,4),(4,5),(5,6),(7,8),
            #Omitting diagonally adjecent
            (1,3),(1,5),
            (2,4),(2,6),
            (3,7),(4,8),(5,7),(6,8)]

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

#     |   | 3 | 5 |   |
#     | 7 | 1 | 8 | 2 |
#     |   | 4 | 6 |   |
#     
# 
#     |   | 4 | 6 |   |
#     | 7 | 1 | 8 | 2 |
#     |   | 3 | 5 |   |
#     
# 
#     |   | 5 | 3 |   |
#     | 2 | 8 | 1 | 7 |
#     |   | 6 | 4 |   |
#     
# 
#     |   | 6 | 4 |   |
#     | 2 | 8 | 1 | 7 |
#     |   | 5 | 3 |   |
#     
# total_solutions 4

