# EEE340_Lab3

5.4. Sets
Python also includes a data type for sets. A set is an unordered collection with no duplicate elements. Basic uses include membership testing and eliminating duplicate entries. Set objects also support mathematical operations like union, intersection, difference, and symmetric difference.

Curly braces or the set() function can be used to create sets. Note: to create an empty set you have to use set(), not {}; the latter creates an empty dictionary, a data structure that we discuss in the next section.

Here is a brief demonstration:

>>>
basket = {'apple', 'orange', 'apple', 'pear', 'orange', 'banana'}
print(basket)                      # show that duplicates have been removed
{'orange', 'banana', 'pear', 'apple'}
'orange' in basket                 # fast membership testing
True
'crabgrass' in basket
False

# Demonstrate set operations on unique letters from two words

a = set('abracadabra')
b = set('alacazam')
a                                  # unique letters in a
{'a', 'r', 'b', 'c', 'd'}
a - b                              # letters in a but not in b
{'r', 'd', 'b'}
a | b                              # letters in a or b or both
{'a', 'c', 'r', 'd', 'b', 'm', 'z', 'l'}
a & b                              # letters in both a and b
{'a', 'c'}
a ^ b                              # letters in a or b but not both
{'r', 'd', 'b', 'm', 'z', 'l'}
Similarly to list comprehensions, set comprehensions are also supported:

>>>
a = {x for x in 'abracadabra' if x not in 'abc'}
a
{'r', 'd'}







Sets are lists with no duplicate entries. Let's say you want to collect a list of words used in a paragraph:

print(set("my name is Eric and Eric is my name".split()))


This will print out a list containing "my", "name", "is", "Eric", and finally "and". Since the rest of the sentence uses words which are already in the set, they are not inserted twice.

Sets are a powerful tool in Python since they have the ability to calculate differences and intersections between other sets. For example, say you have a list of participants in events A and B:

a = set(["Jake", "John", "Eric"])
print(a)
b = set(["John", "Jill"])
print(b)


To find out which members attended both events, you may use the "intersection" method:

a = set(["Jake", "John", "Eric"])
b = set(["John", "Jill"])

print(a.intersection(b))
print(b.intersection(a))


To find out which members attended only one of the events, use the "symmetric_difference" method:

a = set(["Jake", "John", "Eric"])
b = set(["John", "Jill"])

print(a.symmetric_difference(b))
print(b.symmetric_difference(a))


To receive a list of all participants, use the "union" method:

a = set(["Jake", "John", "Eric"])
b = set(["John", "Jill"])

print(a.union(b))




