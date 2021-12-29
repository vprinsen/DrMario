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

# temporary constants (should be configurable)
GAMESPEED = 1000
LEVEL = 17

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

def load_level(file):
    file = os.path.join(main_dir, DATAFOLDER, file)
    try:
        levelData = np.genfromtxt(file, delimiter=",")
        logging.info("Successfully loaded ", file)
        logging.info(levelData)
        logging.info(levelData.shape)
        return levelData
    except pg.error:
        logging.warning("Warning, unable to load, %s" % file)
    return None

def load_image_from_spritesheet(spritesheet, rect):
    """loads an image from a specific rectangle"""
    image = pg.Surface(rect.size).convert()
    image.blit(spritesheet, (0, 0), rect)
    return image



# Classes
class Virus(pg.sprite.Sprite):   
    def __init__(self, board, virusEligibleRect):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.frame = 1
        self.animcycle = 2
        self.color = random.choice(['red','yellow','blue'])
        if (self.color == 'red'):
            self.image = self.redVirusImages[self.frame // self.animcycle % 2]
        elif (self.color == 'yellow'):
            self.image = self.yellowVirusImages[self.frame // self.animcycle % 2]
        else:
            self.image = self.blueVirusImages[self.frame // self.animcycle % 2]
        self.rect = self.image.get_rect()

        # spawn virus on the board
        while (1):
            self.rect.top = random.choice(range(virusEligibleRect.top,virusEligibleRect.bottom,16))
            self.rect.left = random.choice(range(virusEligibleRect.left,virusEligibleRect.right,16))
            if not pg.sprite.spritecollideany(self, board):
                break;

    def update(self):
        self.frame += 1
        self.animcycle = 2
        if (self.color == 'red'):
            self.image = self.redVirusImages[self.frame // self.animcycle % 2]
        elif (self.color == 'yellow'):
            self.image = self.yellowVirusImages[self.frame // self.animcycle % 2]
        else:
            self.image = self.blueVirusImages[self.frame // self.animcycle % 2]

class Pill(pg.sprite.Sprite):
    def __init__(self, board):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.build_pill() 
        self.rect = self.image.get_rect()
        self.rect.top = PLAYABLERECT.top
        entryOffset = PILLSIZE.width if bool(random.getrandbits(1)) else 0
        self.rect.left = PLAYABLERECT.left + (PLAYABLERECT.width / 2) - entryOffset

    def build_pill(self):
        pill = pg.Surface(PILLSIZE.size)
        pill.blit(random.choice(self.images), (1,1))
        pill.blit(pg.transform.flip(random.choice(self.images), flip_x=False, flip_y=True), (1,15))
        return pill

    def move_left(self, board):
        initialPosition = copy.copy(self.rect)
        self.rect.move_ip(-MOVEINCREMENT, 0)
        logging.debug("Current position: %s", initialPosition)
        logging.debug("Projected position: %s", self.rect)
        if (self.rect.left < PLAYABLERECT.left or pg.sprite.spritecollideany(self, board)):
            self.rect = initialPosition
            return False
        return True
            
    def move_right(self, board):
        initialPosition = copy.copy(self.rect)
        self.rect.move_ip(MOVEINCREMENT, 0)
        logging.debug("Current position: %s", initialPosition)
        logging.debug("Projected position: %s", self.rect)
        if (self.rect.right > PLAYABLERECT.right or pg.sprite.spritecollideany(self, board)):
            self.rect = initialPosition
            return False
        return True

    def apply_gravity(self, board):
        initialPosition = copy.copy(self.rect)
        self.rect.move_ip(0, MOVEINCREMENT)
        logging.debug("Current position: %s", initialPosition)
        logging.debug("Projected position: %s", self.rect)
        if (self.rect.bottom > PLAYABLERECT.bottom or pg.sprite.spritecollideany(self, board)):
            self.rect = initialPosition
            return False
        return True

    def rotate(self, board):
        logging.debug("Current position: %s", self.rect)
        self.image = pg.transform.rotate(self.image, 90)
        self.rect = self.image.get_rect(bottomleft=self.rect.bottomleft)
        logging.debug("Projected position: %s", self.rect)
        if (pg.sprite.spritecollideany(self, board)):
            self.image = pg.transform.rotate(self.image, -90)
            self.rect = self.image.get_rect(bottomleft=self.rect.bottomleft)
            return False
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
    # (do this before the classes are used, after screen setup)
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

    # Create Some Starting Values
    clock = pg.time.Clock()
    ApplyGravity = pg.USEREVENT + 1 
    pg.time.set_timer(ApplyGravity, 1000)

    # spawn some viruses on the board
    numViruses = min(4 + (LEVEL * 4), 84)
    logging.info("Spawning %d viruses at level %d", numViruses, LEVEL)
    rowsToUse = min(6 + round(LEVEL / 3), 13) 
    logging.info("Using %d rows at level %d", rowsToUse, LEVEL)

    virusEligibleRect = copy.copy(PLAYABLERECT)
    virusEligibleRect.top += (BOARD_ROWS - rowsToUse) * 16  
    virusEligibleRect.height = rowsToUse * 16
    [currentBoard.add(Virus(currentBoard, virusEligibleRect)) for x in range(0,numViruses)]

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
            if event.type == ApplyGravity:
                pg.time.set_timer(ApplyGravity, GAMESPEED)
                if (currentPill.apply_gravity(currentBoard) == False):
                    currentBoard.add(currentPill)
                    currentPill = Pill(currentBoard)
                    if pg.sprite.spritecollideany(currentPill, currentBoard):
                        print("GAME OVER")
                        break;
                    
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