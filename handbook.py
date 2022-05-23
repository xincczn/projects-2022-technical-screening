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

class TreeNode(ABC):
    """Tree class that can add left and right tree nodes.
    Includes an abstract check() function that will evaluate the node.
    """
    def __init__(self) -> None:
        self.left = None
        self.right = None

    def add_left(self, node: 'TreeNode') -> None:
        """Adds node as left child."""
        self.left = node

    def add_right(self, node: 'TreeNode') -> None:
        """Adds node as right child."""
        self.right = node

    @abstractmethod
    def check(self, courses_list: list) -> bool:
        """Evaluates the node using given course list return T or F."""
        raise NotImplementedError()


class CourseCode(TreeNode):
    """CourseCode node holds in a singular course code string.
    Check() will evaluate if the course code is found within given list of codes.
    """
    def __init__(self, course_code: str) -> None:
        super().__init__()
        self.course_code = course_code

    def check(self, courses_list: list) -> bool:
        return self.course_code in courses_list


class AndNode(TreeNode):
    """AndNode is a gate node that will evaluate its two children based on its
    gate logic."""
    def check(self, courses_list: list) -> bool:
        return self.left.check(courses_list) and self.right.check(courses_list)


class OrNode(TreeNode):
    """OrNode is a gate node that will evaluate its two children based on its
    gate logic.
    """
    def check(self, courses_list: list) -> bool:
        return self.left.check(courses_list) or self.right.check(courses_list)

class CreditList(TreeNode):
    """CreditList node holds unit count and a list of courses.
    Check() will evaluate if a there is a minimum amount of matching
    course codes between a given and own list.
    """
    def __init__(self, units: int, course_list: list) -> None:
        super().__init__()
        self.units = units
        self.course_list = course_list

    def check(self, courses_list: list) -> bool:
        check = 0
        for node in self.course_list:
            if node.check(courses_list):
                check += 6
        if check >= self.units:
            return True
        return False

class CreditCount(TreeNode):
    """CreditCount node holds unit count.
    Check() will evaluate if a given list has a minimum amount of courses.
    """
    def __init__(self, units: int):
        super().__init__()
        self.units = units

    def check(self, courses_list: list) -> bool:
        return len(courses_list) * 6 >= self.units

class CreditLevel(TreeNode):
    """CreditLevel node holds unit count, course level number and course area.
    Check() will evaluate if there is a minimum amount of courses in the given
    list that fit the criteria.
    """
    def __init__(self, level: int, units: int, course_area: str = "") -> None:
        super().__init__()
        self.level = level
        self.units = units
        self.course_area = course_area

    def check(self, courses_list: list) -> bool:
        check = 0
        if self.course_area == "":
            for course in courses_list:
                if course[5] == self.level:
                    check += 6
        else:
            for course in courses_list:
                if re.match(f"({self.course_area + str(self.level)})", course):
                    check += 6
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

    # Process Condition
    processed = process(condition)

    # Transform To Tree
    # Tree structure:
    # Parents: AND/ OR
    # Leaves: SUBJECT/ CREDITS
    root = transform(processed)

    # Evaluate Condition
    # Recursive-like evaluation of the tree's nodes
    if root is None:
        return True
    return root.check(courses_list)

def preprocess(condition_string):
    """Preprocesses the string condition,
    generating a new string removing noise.
    """
    condition = ""
    current_word = ""
    for letter in condition_string + " ":
        if letter in ('(', ')', ' ', ',', '.'):
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
            if letter in ('(', ')'):
                condition += letter + " "
        else:
            current_word += letter
    return condition

def process(condition):
    """Process condition string, generating a list/s of tree nodes."""
    stack = [[]]
    tokens = condition.split()
    idx = 0
    while idx < len(tokens):
        keyword = tokens[idx]
        if re.match("[A-Z]{4}[0-9]{4}", keyword):
            stack[-1].append(CourseCode(keyword))
        elif re.match("[0-9]{1,3}", keyword):  # assumption that there are no random numbers
            if tokens[idx + 1] == "UNITS":  # each number is succeeded by UNITS (LEVEL/(...))
                node = create_credit_node(tokens[idx:])
                stack[-1].append(node)
                if isinstance(node, CreditList):
                    idx += len(node.course_list) + 3
        elif keyword == "OR":
            stack[-1].append(OrNode())
        elif keyword == "AND":
            stack[-1].append(AndNode())
        elif keyword == "(":
            stack.append([])
        elif keyword == ")":
            temp = stack.pop()
            stack[-1].append(temp)
        idx += 1
    return stack[-1]

def create_credit_node(tokens):
    """Given a substring, creates and returns the appropriate credit node."""
    units = int(tokens[0])
    token_length = len(tokens)
    if token_length <= 2:
        return CreditCount(units)
    if tokens[2] == "LEVEL":
        level = int(tokens[3])
        if token_length > 4 and re.match("[A-Z]{4}", tokens[4]):
            return CreditLevel(level, units, tokens[4])
        return CreditLevel(level, units)
    if tokens[2] == "(":
        idx = 3
        course_list = []
        while tokens[idx] != ")" and idx < token_length:
            course_list.append(CourseCode(tokens[idx]))
            idx += 1
        return CreditList(units, course_list)
    return CreditCount(units)


def transform(node_list):
    """Constructs a tree from the node list, recursing on any lists found.
    Until there is only one node left (root)."""
    array_size = len(node_list)
    if array_size == 0:
        return None
    while array_size > 1:
        if isinstance(node_list[0], list):
            node_list[0] = transform(node_list[0])
        if isinstance(node_list[2], list):
            node_list[2] = transform(node_list[2])
        if isinstance(node_list[1], (AndNode, OrNode)):
            left_child = node_list.pop(0)
            right_child = node_list.pop(1)
            node_list[0].add_left(left_child)
            node_list[0].add_right(right_child)
        array_size -= 2
    return node_list[0]
