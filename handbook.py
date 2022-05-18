"""
Inside conditions.json, you will see a subset of UNSW courses mapped to their 
corresponding text conditions. We have slightly modified the text conditions
to make them simpler compared to their original versions.

Your task is to complete the is_unlocked function which helps students determine 
if their course can be taken or not. 

We will run our hidden tests on your submission and look at your success rate.
We will only test for courses inside conditions.json. We will also look over the 
code by eye.

NOTE: We do not expect you to come up with a perfect solution. We are more interested
in how you would approach a problem like this.
"""
import json
from abc import ABC, abstractmethod
import re

class tree_node(ABC):
    @abstractmethod
    def check(self, courses_list):
        pass

# Subject node is always a leaf in a tree
class subject_node(tree_node):
    def __init__(self, course_code=""):
        self.course_code = course_code

    def check(self, courses_list):
        for course in courses_list:
            if course == self.course_code:
                return True
        return False

# Gate nodes can add a left and right children and are never leaves in a tree
class gate_node(tree_node):
    @abstractmethod
    def add_left(self, node1):
        pass

    @abstractmethod
    def add_right(self, node2):
        pass

class and_node(gate_node):
    def add_left(self, node1):
        self.node1 = node1

    def add_right(self, node2):
        self.node2 = node2

    def check(self, courses_list):
        return self.node1.check(courses_list) and self.node2.check(courses_list)

class or_node(gate_node):
    def add_left(self, node1):
        self.node1 = node1

    def add_right(self, node2):
        self.node2 = node2

    def check(self, courses_list):
        return self.node1.check(courses_list) or self.node2.check(courses_list)

class credit_in_list(tree_node):
    def __init__(self, units, course_list):
        self.units = units
        self.course_list = course_list
    
    def len_list(self):
        return len(self.course_list)
    
    def check(self, courses_list):
        check = 0
        for node in self.course_list:
            if node.check(courses_list):
                check += 6
        if check >= self.units:
            return True
        return False

class credit_in_units(tree_node):
    def __init__(self, units):
        self.units = units

    def check(self, courses_list):
        return len(courses_list) * 6 >= self.units

class credit_in_level(tree_node):
    def __init__(self, level, units, course_area=""):
        self.level = level
        self.units = units
        self.course_area = course_area

    def check(self, courses_list):
        check = 0
        if self.course_area == "":
            for course in courses_list:
                if course[5] == self.level:
                    check += 6
        else:
            for course in courses_list:
                if re.match(f"({self.course_area + str(self.level)})", course):
                    check += 6
        print(f"({self.course_area + str(self.level)})")
        if check >= self.units:
            return True
        return False

# NOTE: DO NOT EDIT conditions.json
with open("./conditions.json") as f:
    CONDITIONS = json.load(f)
    f.close()

def is_unlocked(courses_list, target_course):
    """Given a list of course codes a student has taken, return true if the target_course 
    can be unlocked by them.
    
    You do not have to do any error checking on the inputs and can assume that
    the target_course always exists inside conditions.json

    You can assume all courses are worth 6 units of credit
    """

    # Plan:
    # Preprocess Condition
    condition = preprocess(CONDITIONS[target_course])
    # print("========PREPROCESSED========")
    # print(condition)
    
    # Process Condition
    processed = process(condition)
    # print("========PROCESSED========")
    # print(processed)
    
    # Transform To Tree
    # Tree structure: 
    # Parents: AND/ OR
    # Leaves: SUBJECT/ UNITS
    root = transform(processed)
    # print("========TRANSFORMED========")
    # print(root)
    
    # Evaluate Condition
    # Recursive-like evaluation of the tree's nodes
    if root is None:
        return True
    else:
        return root.check(courses_list)

def preprocess(input):
    condition = ""
    current_word = ""
    for letter in input + " ":
        if letter == "(" or letter == ")" or letter == " " or letter == "," or letter == ".":
            if re.match("^[0-9]{1,3}$", current_word):
                condition += current_word + " "
            elif re.match("(?i)LEVEL", current_word):
                condition += "LEVEL "
            elif re.match("[0-9]{4}", current_word):
                condition += "COMP" + current_word + " "
            elif re.match("[A-Z]{4}([0-9]{4}|$)", current_word):
                condition += current_word + " "
            elif re.match("(?i)OR", current_word):
                condition += "OR "
            elif re.match("(?i)AND", current_word):
                condition += "AND "
            elif re.match("(?i)UNITS?", current_word):
                condition += "UNITS "
            current_word = ""
            if letter == "(" or letter == ")":
                condition += letter + " "
        else:
            current_word += letter
    return condition

def process(condition):
    stack = [[]]
    tokens = condition.split()
    idx = 0
    while idx < len(tokens):
        keyword = tokens[idx]
        if re.match("[A-Z]{4}[0-9]{4}", keyword):
            stack[-1].append(subject_node(keyword))
        elif re.match("[0-9]{1,3}", keyword):  # assumption that there are no random numbers
            if tokens[idx + 1] == "UNITS":  # each number is succeeded by UNITS (LEVEL/(...))
                node = create_credit_node(tokens[idx:])
                stack[-1].append(node)
                if type(node) is credit_in_list:
                    idx += node.len_list() + 3
        elif keyword == "OR":
            stack[-1].append(or_node())
        elif keyword == "AND":
            stack[-1].append(and_node())
        elif keyword == "(":
            stack.append([])
        elif keyword == ")":
            temp = stack.pop()
            stack[-1].append(temp)
        idx += 1
    return stack[-1]

def create_credit_node(tokens):
    units = int(tokens[0])
    if len(tokens) > 2:
        if tokens[2] == "LEVEL":
            level = int(tokens[3])
            if len(tokens) > 4 and re.match("[A-Z]{4}", tokens[4]):
                return credit_in_level(level, units, tokens[4])
            else:
                return credit_in_level(level, units)
        elif tokens[2] == "(":
            idx = 3
            course_list = []
            while tokens[idx] != ")" and idx < len(tokens):
                course_list.append(subject_node(tokens[idx]))
                idx += 1
            return credit_in_list(units, course_list)
    return credit_in_units(units)

def transform(node_list):
    array_size = len(node_list)
    if array_size == 0:
        return None
    elif array_size == 1:
        return node_list[0]
    else:
        while array_size > 1:
            if type(node_list[0]) is list:
                node_list[0] = transform(node_list[0])
            if type(node_list[2]) is list:
                node_list[2] = transform(node_list[2])
            if issubclass(type(node_list[1]), gate_node):
                left_child = node_list.pop(0)
                right_child = node_list.pop(1)
                node_list[0].add_left(left_child)
                node_list[0].add_right(right_child)
            array_size -= 2
        return node_list[0]