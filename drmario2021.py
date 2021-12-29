#!/usr/bin/env python
""" 

                                                                                          
,------.              ,--.   ,--.               ,--.            ,---.   ,--.  ,---.  ,--. 
|  .-.  | ,--.--.     |   `.'   | ,--,--.,--.--.`--' ,---.     '.-.  | /    |'.-.  |/   | 
|  |  |  :|  .--'     |  |'.'|  |' ,-.  ||  .--',--.| .-. |     .-' .'|  ()  |.-' .'`|  | 
|  '--'  /|  |.--.    |  |   |  || '-'  ||  |   |  |' '-' '    /   '-. |    //   '-. |  | 
`-------' `--''--'    `--'   `--' `--`--'`--'   `--' `---'     '-----'  `--' '-----' `--' 
                                                                                          

Dr Mario 2021

"""

import random
import os
import copy
import numpy as np
from enum import Enum

# import basic pygame modules
import pygame as pg

# setup logging
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', encoding='utf-8', level=logging.INFO)

# see if we can load more than standard BMP
if not pg.image.get_extended():
    raise SystemExit("Sorry, extended image module required")

# game constants
DATAFOLDER = "data_drm"
SCREENRECT = pg.Rect(0, 0, 512, 480)
NESRECT = pg.Rect(0, 0, 256, 240)
SPRITERATIO = 2
MOVEINCREMENT = 16
#PILLRECT = pg.Rect(0, 0, 8, 8)
PILLSIZE = pg.Rect(0, 0, 16, 32) 
BOARD_ROWS = 16
BOARD_COLS = 8
PLAYABLERECT = pg.Rect(96 * SPRITERATIO, 80 * SPRITERATIO, BOARD_COLS * 16, BOARD_ROWS * 16) #pg.Rect(96 * SPRITERATIO, 80 * SPRITERATIO, 64 * SPRITERATIO, 128 * SPRITERATIO)
START_ROW = 0
START_COL = 4
MATCH_COUNT = 4

# temporary constants (should be configurable)
GAMESPEED = 1000
LEVEL = 0

# generate the game board
gameBoard = np.zeros((16,8))

main_dir = os.path.split(os.path.abspath(__file__))[0]

# Shared functions

def load_image(file):
    """loads an image, prepares it for play"""
    file = os.path.join(main_dir, DATAFOLDER, file)
    try:
        surface = pg.image.load(file)
    except pg.error:
        raise SystemExit('Could not load image "%s" %s' % (file, pg.get_error()))
    return surface.convert()

def load_image_from_spritesheet(spritesheet, rect):
    """loads an image from a specific rectangle"""
    image = pg.Surface(rect.size).convert()
    image.blit(spritesheet, (0, 0), rect)
    return image

def isColliding(row, col, orient):
    """checks for pill collision at row,col""" 
    if gameBoard[row][col] != 0:
        return True
    if orient == Orientation.VERTICAL and gameBoard[row+1][col] != 0:
        return True
    if orient == Orientation.HORIZONTAL and gameBoard[row][col+1] != 0:
        return True
    return False

def resolveGameBoard():
    """check for horizontal/vertical color matches"""
    for row in range(0,BOARD_ROWS-MATCH_COUNT+1):
        for col in range(0,BOARD_COLS):
            if gameBoard[row][col] != 0 and gameBoard[row][col] == gameBoard[row+1][col] and gameBoard[row][col] == gameBoard[row+2][col] and gameBoard[row][col] == gameBoard[row+3][col]:
                logging.info("Vertical match starting at %d,%d", row, col) 
    for row in range(0,BOARD_ROWS):
        for col in range(0,BOARD_COLS-MATCH_COUNT+1):
            if gameBoard[row][col] != 0 and gameBoard[row][col] == gameBoard[row][col+1] and gameBoard[row][col] == gameBoard[row][col+2] and gameBoard[row][col] == gameBoard[row][col+3]:
                logging.info("Horizontal match starting at %d,%d", row, col) 

# Classes
class Virus(pg.sprite.Sprite):   
    def __init__(self, virusEligibleRect):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.frame = 1
        self.animcycle = 2
        self.color = random.choice(list(Colour))
        if (self.color == Colour.RED):
            self.image = self.redVirusImages[self.frame // self.animcycle % 2]
        elif (self.color == Colour.YELLOW):
            self.image = self.yellowVirusImages[self.frame // self.animcycle % 2]
        elif (self.color == Colour.BLUE):
            self.image = self.blueVirusImages[self.frame // self.animcycle % 2]
        else:
            logging.warning("Virus init returned an invalid colour")

        # spawn virus on the board
        while (1):
            row = random.randint(virusEligibleRect.x, virusEligibleRect.x + virusEligibleRect.height - 1) 
            col = random.randint(0,virusEligibleRect.width - 1)
            if gameBoard[row][col] == 0:
                gameBoard[row][col] = self.color.value + 1
                break;
        
        self.rect = self.image.get_rect()
        self.rect.top = PLAYABLERECT.y + (row * 16)
        self.rect.left = PLAYABLERECT.x + (col * 16)

    def update(self):
        self.frame += 1
        self.animcycle = 2
        if (self.color == Colour.RED):
            self.image = self.redVirusImages[self.frame // self.animcycle % 2]
        elif (self.color == Colour.YELLOW):
            self.image = self.yellowVirusImages[self.frame // self.animcycle % 2]
        elif (self.color == Colour.BLUE):
            self.image = self.blueVirusImages[self.frame // self.animcycle % 2]
        else:
            logging.warning("Virus update returned an invalid colour")

class Colour(Enum):
    RED = 0
    YELLOW = 1
    BLUE = 2

class Orientation(Enum):
    VERTICAL = 0
    HORIZONTAL = 1

class Pill(pg.sprite.Sprite):
    def __init__(self, board):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.color1 = random.choice(list(Colour))
        self.color2 = random.choice(list(Colour))
        self.image = self.build_pill() 
        self.rect = self.image.get_rect()
        self.row = START_ROW
        self.col = START_COL
        self.orient = Orientation.VERTICAL

    def update(self):
        self.rect.top = (self.row * 16) + PLAYABLERECT.y 
        self.rect.left = (self.col * 16) + PLAYABLERECT.x
        
    def build_pill(self):
        pill = pg.Surface(PILLSIZE.size)
        pill.blit(self.images[self.color1.value], (1,1))
        pill.blit(pg.transform.flip(self.images[self.color2.value], flip_x=False, flip_y=True), (1,15))
        return pill

    def move_left(self, board):
        logging.debug("Current position: (%d,%d)", self.row, self.col)
        if (self.col > 0 and not isColliding(self.row,self.col-1,self.orient)):
            self.col -= 1
            logging.debug("New position: (%d,%d)", self.row, self.col)
            return True
        return False
    
    def move_right(self, board):
        logging.debug("Current position: (%d,%d)", self.row, self.col)
        if (self.col < BOARD_COLS - 1 - self.orient.value and not isColliding(self.row,self.col+1,self.orient)):
            self.col += 1
            logging.debug("New position: (%d,%d)", self.row, self.col)
            return True
        return False

    def apply_gravity(self, board):
        logging.debug("Current position: (%d,%d)", self.row, self.col)
        if (self.row < BOARD_ROWS - 2 + self.orient.value and not isColliding(self.row+1,self.col,self.orient)):
            self.row += 1
            logging.debug("New position: (%d,%d)", self.row, self.col)
            return True
        return False

    def rotate(self, board):
        logging.debug("Current position: (%d,%d)", self.row, self.col)
        if (self.orient == Orientation.VERTICAL and self.col + 1 < BOARD_COLS and gameBoard[self.row][self.col+1] == 0):
            self.image = pg.transform.rotate(self.image, 90)
            self.orient = Orientation.HORIZONTAL
        elif (self.orient == Orientation.HORIZONTAL and self.row + 1 < BOARD_ROWS and gameBoard[self.row+1][self.col] == 0):
            self.image = pg.transform.rotate(self.image, 90)
            self.orient = Orientation.VERTICAL
            """swap colours as we've now inverted the pill vertically"""
            temp = self.color1
            self.color1 = self.color2
            self.color2 = temp
        else:
            return False
        return True

    def settle(self):
        """called when the pill can't fall any further and must lock in place"""
        gameBoard[self.row][self.col] = self.color1.value + 1
        if self.orient == Orientation.VERTICAL:
            gameBoard[self.row+1][self.col] = self.color2.value + 1
        else:
            gameBoard[self.row][self.col+1] = self.color2.value + 1
        # TODO check for clear
        resolveGameBoard()
        return True


def main(winstyle=0):
    # Initialize pygame
    if pg.get_sdl_version()[0] == 2:
        pg.mixer.pre_init(44100, 32, 2, 1024)
    pg.init()
    if pg.mixer and not pg.mixer.get_init():
        print("Warning, no sound")
        pg.mixer = None

    # Set the display mode
    fullscreen = False
    winstyle = 0  # |FULLSCREEN
    bestdepth = pg.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pg.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    # Load images, assign to sprite classes
    gamesprites = load_image("NES - Dr Mario - Characters.png")
    pillImages = []
    for y_pos in (0, 8, 16):
        pillImages.append(load_image_from_spritesheet(gamesprites, pg.Rect(y_pos, 8, 7, 7)))
    Pill.images = [pg.transform.scale(pillImage, (14, 14)) for pillImage in pillImages]

    redVirusImages = []
    for x_pos in (88, 96):
        redVirusImages.append(load_image_from_spritesheet(gamesprites, pg.Rect(0, x_pos, 7, 7)))
    yellowVirusImages = []
    for x_pos in (112, 120):
        yellowVirusImages.append(load_image_from_spritesheet(gamesprites, pg.Rect(0, x_pos, 7, 7)))
    blueVirusImages = []
    for x_pos in (136, 144):
        blueVirusImages.append(load_image_from_spritesheet(gamesprites, pg.Rect(0, x_pos, 7, 7)))
    Virus.redVirusImages = [pg.transform.scale(img, (14, 14)) for img in redVirusImages]
    Virus.yellowVirusImages = [pg.transform.scale(img, (14, 14)) for img in yellowVirusImages]
    Virus.blueVirusImages = [pg.transform.scale(img, (14, 14)) for img in blueVirusImages]

    # decorate the game window
    icon = pg.transform.scale(blueVirusImages[1], (32, 32))
    pg.display.set_icon(icon)
    pg.display.set_caption("Pygame: Dr. Mario 2021")
    pg.mouse.set_visible(0)

    # load the background from the sprite sheet
    bgdfields = load_image("NES - Dr Mario - Fields.png")
    background = pg.Surface(NESRECT.size)
    background.blit(bgdfields, (0,0), (0, 0, NESRECT.width, NESRECT.height))
    background = pg.transform.scale(background, SCREENRECT.size)

    # debug playable areas
    # virusEligibleRect = copy.copy(PLAYABLERECT)
    # virusEligibleRect.top += (BOARD_ROWS / 2) * 8  
    # virusEligibleRect.height /= 2
    # pg.draw.rect(background,(255,0,0),virusEligibleRect)
    # pg.draw.rect(background,(255,0,0),PLAYABLERECT)

    # scale up the background
    screen.blit(background, (0, 0))
    pg.display.flip()

    # Initialize Game Groups
    currentBoard = pg.sprite.Group()
    all = pg.sprite.RenderUpdates()

    # assign default groups to each sprite class
    Virus.containers = all
    Pill.containers = all

    # Initialize starting values
    clock = pg.time.Clock()
    ApplyGravity = pg.USEREVENT + 1 
    pg.time.set_timer(ApplyGravity, 1000)
    pause = False
    gameOver = False

    # spawn some viruses on the board
    numViruses = min(4 + (LEVEL * 4), 84)
    logging.info("Spawning %d viruses at level %d", numViruses, LEVEL)
    rowsToUse = min(6 + round(LEVEL / 3), 13) 
    logging.info("Using %d rows at level %d", rowsToUse, LEVEL)
    virusEligibleRect = pg.Rect(BOARD_ROWS - rowsToUse,0,8,rowsToUse)   
    [currentBoard.add(Virus(virusEligibleRect)) for x in range(0,numViruses)]

#    print(gameBoard)

    # spawn our first pill
    currentPill = Pill(currentBoard)

    # start game loop
    while (1):
        # get input
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_f:
                    if not fullscreen:
                        print("Changing to FULLSCREEN")
                        screen_backup = screen.copy()
                        screen = pg.display.set_mode(
                            SCREENRECT.size, winstyle | pg.FULLSCREEN, bestdepth
                        )
                        screen.blit(screen_backup, (0, 0))
                    else:
                        print("Changing to windowed mode")
                        screen_backup = screen.copy()
                        screen = pg.display.set_mode(
                            SCREENRECT.size, winstyle, bestdepth
                        )
                        screen.blit(screen_backup, (0, 0))
                    pg.display.flip()
                    fullscreen = not fullscreen
                if event.key == pg.K_p:
                    pause = not pause
            if event.type == ApplyGravity and pause == False:
                pg.time.set_timer(ApplyGravity, GAMESPEED)
                if (currentPill.apply_gravity(currentBoard) == False):
                    currentBoard.add(currentPill)
                    currentPill.settle()
                    currentPill = Pill(currentBoard)
                    if isColliding(currentPill.row, currentPill.col, currentPill.orient):
                        print("GAME OVER")
                        gameOver = True
                        break;
               
        if (pause):
            continue
        if (gameOver):
            # TODO  game over handling
            clock.tick(2000)
            break

        # get keystrokes
        keystate = pg.key.get_pressed()
        if keystate[pg.K_LEFT]:
            currentPill.move_left(currentBoard)
        elif keystate[pg.K_RIGHT]:
            currentPill.move_right(currentBoard)
        elif keystate[pg.K_DOWN]:
            currentPill.apply_gravity(currentBoard)
        elif keystate[pg.K_SPACE]:
            currentPill.rotate(currentBoard)

        # clear/erase the last drawn sprites
        all.clear(screen, background)

        # update all the sprites
        all.update()

        # draw the scene
        dirty = all.draw(screen)
        pg.display.update(dirty)

        # cap the framerate at 30fps
        clock.tick(10)


# call the "main" function if running this script
if __name__ == "__main__":
    main()
    pg.quit()