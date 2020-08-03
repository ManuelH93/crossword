import sys
import copy
import itertools
import pandas as pd

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        domains = copy.deepcopy(self.domains)
        for variable, domain in domains.items():
            for word in domain:
                if len(word) != variable.length:
                    self.domains[variable].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        overlap = self.crossword.overlaps[x, y]
        if overlap == None:
            return revised
        else:
            position_x = overlap[0]
            position_y = overlap[1]
            set_y = set()
            for word in self.domains[y]:
                set_y.add(word[position_y])

            domain_x = copy.deepcopy(self.domains[x])
            for word in domain_x:
                if word[position_x] in set_y:
                    continue
                else:
                    self.domains[x].remove(word)
                    revised = True
            return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            queue = list(itertools.permutations(self.crossword.variables, 2))
        else:
            queue = arcs
        while len(queue) != 0:
            (x,y) = queue.pop()
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for neighbor in self.crossword.neighbors(x) - {y}:
                    queue.append((neighbor, x))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        if len(assignment) == len(self.crossword.variables):
            return True
        else:
            return False

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        consistent = True
        # Check if each value is distinct:
        vals = {}
        for i in assignment.values():
            l = list(i)
            vals.setdefault(l[0],0)
            vals[l[0]] += 1
        for v in vals.values():
            if v != 1:
                consistent = False
        # Check if each value is of correct length:
        for k,v in assignment.items():
            if k.length != len(list(v)[0]):
                consistent = False
        # Check that there are no conflicts between neigbhors:
        for v1,w1 in assignment.items():
            for v2,w2 in assignment.items():
                if v1 == v2:
                    continue
                if self.crossword.overlaps[v1, v2] == None:
                    continue
                w1_index, w2_index = self.crossword.overlaps[v1, v2]
                word1 = list(w1)[0]
                word2 = list(w2)[0]
                if word1[w1_index] != word2[w2_index]:
                    consistent = False
        return consistent

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Determine all neighbors that have not been assigned yet
        neighbors_unassigned = copy.deepcopy(self.crossword.neighbors(var))
        for v1 in self.crossword.neighbors(var):
            if v1 in assignment.keys():
                neighbors_unassigned.remove(v1)
        # Determine number of eliminated words for each possible value
        choices = list(self.domains[var])
        tracker = {}
        for neighbor in neighbors_unassigned:
            w1_index, w2_index = self.crossword.overlaps[var, neighbor]
            neighbor_words = [word for word in self.domains[neighbor]]
            for word1 in choices:
                for word2 in neighbor_words:
                    if word1[w1_index] != word2[w2_index]:
                        tracker.setdefault(word1,0)
                        tracker[word1] += 1
        order_domain_values = [k for k, v in sorted(tracker.items(), key=lambda item: item[1])]
        return order_domain_values

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # Determine unassigned variables
        unassigned = copy.deepcopy(self.crossword.variables)
        for variable in self.crossword.variables:
            if variable in assignment.keys():
                unassigned.remove(variable)
        # Create lists of criteria by which we want to sort variables
        variable = []
        values = []
        n_neighbors = []
        for v in unassigned:
            variable.append(v)
            values.append(len(self.domains[v]))
            neighbors = copy.deepcopy(self.crossword.neighbors(v))
            # Note: we want to return variable, that will impose
            # highest number of restrictions on other variables (i.e: neighbors).
            # If a neighbor is already asssigned, no additional restriction will
            # be imposed on that neighbor. For the degree heuristic, we therefore
            # only count neighbors that have not been assigned yet.
            for v in self.crossword.neighbors(v):
                if v in assignment.keys():
                    neighbors.remove(v)
            n_neighbors.append(len(neighbors))
        # Sort variables
        listofkeys = ('variable', 'values', 'n_neighbors')
        listofvalues = (variable, values, n_neighbors)
        dictionary=dict(zip(listofkeys,listofvalues))
        df = pd.DataFrame(dictionary)
        df = df.sort_values(["values", "n_neighbors"], ascending = (True, False))
        df.reset_index(drop = True, inplace = True)
        return df.loc[0, 'variable']

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        raise NotImplementedError


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
