import sys

from crossword import *

structure = 'data/structure3.txt'
words = 'data/words0.txt'
output = 'output.png'

crossword = Crossword(structure, words)
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

creator = CrosswordCreator(crossword)

assignment = {
		Variable(0, 1, 'across', 3) : 'SIX',
		Variable(0, 1, 'down', 5) : 'SEVEN'
	}

letters = [[None for _ in range(creator.crossword.width)]for _ in range(creator.crossword.height)]

for variable, word in assignment.items():
    direction = variable.direction
    print(variable.direction)
    for k in range(len(word)):
        i = variable.i + (k if direction == Variable.DOWN else 0)
        j = variable.j + (k if direction == Variable.ACROSS else 0)
        letters[i][j] = word[k]
        print(word[k])
print(letters)

for i in range(creator.crossword.height):
    for j in range(creator.crossword.width):
        if creator.crossword.structure[i][j]:
            print(letters[i][j] or " ", end="")
        else:
            print("█", end="")
    print()

from PIL import Image, ImageDraw, ImageFont
cell_size = 100
cell_border = 2
interior_size = cell_size - 2 * cell_border

# Create a blank canvas
img = Image.new(
    "RGBA",
    (creator.crossword.width * cell_size,
        creator.crossword.height * cell_size),
    "black"
)
font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
draw = ImageDraw.Draw(img)

for i in range(creator.crossword.height):
    for j in range(creator.crossword.width):

        rect = [
            (j * cell_size + cell_border,
                i * cell_size + cell_border),
            ((j + 1) * cell_size - cell_border,
                (i + 1) * cell_size - cell_border)
        ]
        if creator.crossword.structure[i][j]:
            draw.rectangle(rect, fill="white")
            if letters[i][j]:
                w, h = draw.textsize(letters[i][j], font=font)
                draw.text(
                    (rect[0][0] + ((interior_size - w) / 2),
                        rect[0][1] + ((interior_size - h) / 2) - 10),
                    letters[i][j], fill="black", font=font
                )

img.save('filename.png')