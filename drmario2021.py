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
FRAME_RATE = 30
PILLSIZE = pg.Rect(0, 0, 16, 32) 
HALFPILLSIZE = pg.Rect(0, 0, 16, 16)
BOARD_ROWS = 16
BOARD_COLS = 8
PLAYABLERECT = pg.Rect(96 * SPRITERATIO, 80 * SPRITERATIO, BOARD_COLS * 16, BOARD_ROWS * 16) #pg.Rect(96 * SPRITERATIO, 80 * SPRITERATIO, 64 * SPRITERATIO, 128 * SPRITERATIO)
START_ROW = 0
START_COL = 4
MATCH_COUNT = 4

# animation timers
VIRUS_ANIM_TIMER = 100


# temporary constants (should be configurable)
GAMESPEED = 1000
LEVEL = 0

# generate the game board
gameBoard = [[None for j in range(BOARD_COLS)] for i in range(BOARD_ROWS)]

main_dir = os.path.split(os.path.abspath(__file__))[0]

# Enums

class Colour(Enum):
    RED = 0
    YELLOW = 1
    BLUE = 2

class Orientation(Enum):
    VERTICAL = 0
    HORIZONTAL = 1

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

def isColliding(row, col):
    """checks for pill collision at row,col""" 
    if gameBoard[row][col] != None:
        return True
    return False

def resolveGameBoard():
    matchedPillLocations = []
    """check for horizontal/vertical colour matches"""
    for row in range(0,BOARD_ROWS):
        for col in range(0,BOARD_COLS):
            if gameBoard[row][col] != None:
                # space containing a pill half
                matchColour = gameBoard[row][col].colour
                i = 0
                # continue until we hit the bottom of the board or a non-matching space
                while row+i < BOARD_ROWS and gameBoard[row+i][col] != None and gameBoard[row+i][col].colour == matchColour:
                    i += 1
                # check if we matched a long-enough string of pills 
                if (i >= MATCH_COUNT):
                    logging.info("Vertical match starting at %d,%d", row, col)
                    for m in range(0,i):
                        if ((row+m,col) not in matchedPillLocations):
                            matchedPillLocations.append((row+m,col))                
                i = 0
                # continue until we hit the side of the board or a non-matching space
                while col+i < BOARD_COLS and gameBoard[row][col+i] != None and gameBoard[row][col+i].colour == matchColour:
                    i += 1
                # check if we matched a long-enough string of pills 
                if (i >= MATCH_COUNT):
                    logging.info("Horizontal match starting at %d,%d", row, col)
                    for m in range(0,i):
                        if ((row,col+m) not in matchedPillLocations):
                            matchedPillLocations.append((row,col+m))      
    return matchedPillLocations    

# Classes

class Virus(pg.sprite.Sprite):   
    def __init__(self, virusEligibleRect):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.frame = 1
        self.animcycle = 2
        self.animTimer = 0
        self.colour = random.choice(list(Colour))
        if (self.colour == Colour.RED):
            self.image = self.redVirusImages[self.frame // self.animcycle % 2]
        elif (self.colour == Colour.YELLOW):
            self.image = self.yellowVirusImages[self.frame // self.animcycle % 2]
        elif (self.colour == Colour.BLUE):
            self.image = self.blueVirusImages[self.frame // self.animcycle % 2]
        else:
            logging.error("Virus init returned an invalid colour")

        # spawn virus on the board
        while (1):
            row = random.randint(virusEligibleRect.x, virusEligibleRect.x + virusEligibleRect.height - 1) 
            col = random.randint(0,virusEligibleRect.width - 1)
            if gameBoard[row][col] == None:
                gameBoard[row][col] = self
                break;
        
        self.rect = self.image.get_rect()
        self.rect.top = PLAYABLERECT.y + (row * 16)
        self.rect.left = PLAYABLERECT.x + (col * 16)

    def update(self, timeDelta):
        # animate virus sprites
        self.animTimer += timeDelta
        if (self.animTimer > VIRUS_ANIM_TIMER):
            self.animTimer = 0
            self.frame += 1
            self.animcycle = 2
            if (self.colour == Colour.RED):
                self.image = self.redVirusImages[self.frame // self.animcycle % 2]
            elif (self.colour == Colour.YELLOW):
                self.image = self.yellowVirusImages[self.frame // self.animcycle % 2]
            elif (self.colour == Colour.BLUE):
                self.image = self.blueVirusImages[self.frame // self.animcycle % 2]
            else:
                logging.error("Virus update returned an invalid colour")

class Pill():
    """a pill is composed of two halves"""
    def __init__(self):
        self.orient = Orientation.HORIZONTAL
        self.one = HalfPill(self.orient)
        self.two = HalfPill(self.orient, self.one)
        self.one.setPartner(self.two)
    def moveLeft(self):
        """check for collision on the left and move the pill halves"""
        if (self.orient == Orientation.VERTICAL):
            if (self.one.col > 0 and not isColliding(self.one.row,self.one.col-1) and not isColliding(self.two.row,self.two.col-1)):
                self.one.moveLeft()
                self.two.moveLeft()
                return True
            return False
        elif (self.orient == Orientation.HORIZONTAL):
            leftHalf = self.getLeftHalf()
            if (leftHalf != None and leftHalf.col > 0 and not isColliding(leftHalf.row,leftHalf.col-1)):
                self.one.moveLeft()
                self.two.moveLeft()
                return True
            return False
    def getLeftHalf(self):
        if self.orient == Orientation.VERTICAL:
            logging.error("Called getRightHalf but pill is in vertical orientation!")
            return None
        return self.one if (self.one.col < self.two.col) else self.two
    def moveRight(self):
        """check for collision on the right and move the pill halves"""
        if (self.orient == Orientation.VERTICAL):
            if (self.one.col < BOARD_COLS - 1 and not isColliding(self.one.row,self.one.col+1) and not isColliding(self.two.row,self.two.col+1)):
                self.one.moveRight()
                self.two.moveRight()
                return True
                self.one.moveRight()
                self.two.moveRight()
                return True
            return False
        elif (self.orient == Orientation.HORIZONTAL):
            rightHalf = self.getRightHalf()
            if (rightHalf != None and rightHalf.col < BOARD_COLS - 1 and not isColliding(rightHalf.row,rightHalf.col+1)):
                self.one.moveRight()
                self.two.moveRight()
                return True
            return False
    def getRightHalf(self):
        if (self.orient == Orientation.VERTICAL):
            logging.error("Called getRightHalf but pill is in vertical orientation!")
            return None
        return self.one if (self.one.col > self.two.col) else self.two
    def applyGravity(self):
        """check for collision below and move the pill halves"""
        if (self.orient == Orientation.VERTICAL):
            bottomHalf = self.getBottomHalf()
            if (bottomHalf and bottomHalf.row < BOARD_ROWS - 1 and not isColliding(bottomHalf.row+1,bottomHalf.col)):
                self.one.applyGravity()
                self.two.applyGravity()
                return True
            return False
        elif (self.orient == Orientation.HORIZONTAL):
            if (self.one.row < BOARD_ROWS - 1 and not isColliding(self.one.row+1,self.one.col) and not isColliding(self.two.row+1,self.two.col)):
                self.one.applyGravity()
                self.two.applyGravity()
                return True
            return False
    def getTopHalf(self):
        if (self.orient == Orientation.HORIZONTAL):
            logging.error("Called getTopHalf but pill is in horizontal orientation!")
            return None
        return self.one if (self.one.row < self.two.row) else self.two 
    def getBottomHalf(self):
        if (self.orient == Orientation.HORIZONTAL):
            logging.error("Called getBottomHalf but pill is in horizontal orientation!")
            return None
        return self.one if (self.one.row > self.two.row) else self.two
    def settle(self, currentBoard, settledPills):
        """called when the pill can't fall any further and must lock in place"""
        currentBoard.add(self.one)
        currentBoard.add(self.two)
        self.one.settle()
        self.two.settle()
        settledPills.add(self.one)
        settledPills.add(self.two)
    def rotate(self):
        """rotate the pill 90 degrees"""
        if (self.orient == Orientation.HORIZONTAL):
            """right-hand side always rotates up"""
            rightHalf = self.getRightHalf()
            if not isColliding(rightHalf.row-1, rightHalf.col-1):
                rightHalf.setPosition(rightHalf.row-1,rightHalf.col-1)
                self.one.flipOrientation()
                self.two.flipOrientation()
                self.orient = Orientation.VERTICAL
                return True
            return False
        else:
            """rotate into the bottom half's row"""
            topHalf = self.getTopHalf()
            bottomHalf = self.getBottomHalf()
            if not isColliding(bottomHalf.row,bottomHalf.col+1):
                topHalf.setPosition(bottomHalf.row, bottomHalf.col)
                bottomHalf.setPosition(bottomHalf.row, bottomHalf.col+1)
                self.one.flipOrientation()
                self.two.flipOrientation()
                self.orient = Orientation.HORIZONTAL
                return True
            return False
    def isColliding(self):
        """check if the pill is colliding with anything in its current position"""
        return isColliding(self.one.row, self.one.col) or isColliding(self.two.row, self.two.col)

class HalfPill(pg.sprite.Sprite):
    def __init__(self, pillOrientation, partner = None):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.partner = partner
        self.orient = pillOrientation
        self.colour = random.choice(list(Colour))
        self.image = self.buildPill() 
        self.rect = self.image.get_rect()
        self.row = START_ROW if (self.partner == None or self.orient == Orientation.HORIZONTAL) else START_ROW + 1
        self.col = START_COL if (self.partner == None or self.orient == Orientation.VERTICAL) else START_COL - 1
    def splitFromPartner(self):
        if (self.partner != None):
            self.partner.partner = None
            self.partner = None
    def setPartner(self, partnerHalf):
        self.partner = partnerHalf
    def setPosition(self, row, col):
        self.row = row
        self.col = col
    def flipOrientation(self):
        self.orient = Orientation.VERTICAL if (self.orient == Orientation.HORIZONTAL) else Orientation.HORIZONTAL
    def update(self, timeDelta):
        self.image = self.buildPill()
        self.rect.top = (self.row * 16) + PLAYABLERECT.y 
        self.rect.left = (self.col * 16) + PLAYABLERECT.x
    def buildPill(self):
        halfPillImage = pg.Surface(HALFPILLSIZE.size)
        halfPillImage.blit(self.images[self.colour.value], (1,1))
        halfPillImage.blit(pg.transform.flip(self.images[self.colour.value], flip_x=False, flip_y=True), (1,15))
        return halfPillImage
    def moveLeft(self):
        self.col -= 1
    def moveRight(self):
        self.col += 1
    def applyGravity(self):
        if (self.partner is not None):
            self.row += 1
        if (self.partner == None and self.row < BOARD_ROWS - 1 and not isColliding(self.row+1,self.col)):
            gameBoard[self.row][self.col] = None
            self.row += 1
            gameBoard[self.row][self.col] = self
    def settle(self):
        """called when the pill can't fall any further and must lock in place"""
        gameBoard[self.row][self.col] = self
    def print_position(self):
        logging.debug("Position: (%d,%d)", self.row, self.col)


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

    # Pill images
    pillImages = []
    for y_pos in (0, 8, 16):
        pillImages.append(load_image_from_spritesheet(gamesprites, pg.Rect(y_pos, 40, 7, 7)))
    HalfPill.images = [pg.transform.scale(pillImage, (14, 14)) for pillImage in pillImages]

    # Virus images
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
    settledPills = pg.sprite.Group()
    currentBoard = pg.sprite.Group()
    all = pg.sprite.RenderUpdates()

    # assign default groups to each sprite class
    Virus.containers = all
    HalfPill.containers = all

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
    currentPill = Pill()

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
                if event.key == pg.K_LEFT:
                   currentPill.moveLeft()
                if event.key == pg.K_RIGHT:
                    currentPill.moveRight()
                # if event.key == pg.K_DOWN:
                #     currentPill.applyGravity()
                if event.key == pg.K_SPACE:
                    currentPill.rotate()
            if event.type == ApplyGravity and pause == False:
                pg.time.set_timer(ApplyGravity, GAMESPEED)
                if (currentPill.applyGravity() == False):
                    # add the current pill to the fixed board and spawn a new pill
                    currentPill.settle(currentBoard, settledPills)
                    # check for matches
                    matchedPillLocations = resolveGameBoard()
                    # clear matches
                    for pill in settledPills:
                        if (pill.row,pill.col) in matchedPillLocations:
                            pill.splitFromPartner()
                            settledPills.remove(pill)
                            currentBoard.remove(pill)
                            pill.kill()
                            gameBoard[pill.row][pill.col] = None
                            matchedPillLocations.remove((pill.row,pill.col))
                    # if (pill.partner == None):
                        # pill.applyGravity()
                    # generate a new pill
                    currentPill = Pill()
                    # if our newly-spawned pill is colliding, the board is full and we lost
                    if currentPill.isColliding():
                        print("GAME OVER")
                        gameOver = True
                        break;
               
        if (pause):
            continue
        if (gameOver):
            # TODO  game over handling
            clock.tick(2000)
            break

        # get continuous keystrokes
        keystate = pg.key.get_pressed()
        if keystate[pg.K_DOWN]:
            currentPill.applyGravity()

        # clear/erase the last drawn sprites
        all.clear(screen, background)

        # update all the sprites
        all.update(clock.get_time())

        # draw the scene
        dirty = all.draw(screen)
        pg.display.update(dirty)

        # cap the framerate 
        clock.tick(FRAME_RATE)


# call the "main" function if running this script
if __name__ == "__main__":
    main()
    pg.quit()