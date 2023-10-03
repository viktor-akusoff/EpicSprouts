import pygame as pg
from client.entities import Node

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

if __name__ == "__main__":
    pg.init()
    pg.display.set_caption('Epic Sprouts')
    screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])

    running = True
    while running:

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                pos = pg.mouse.get_pos()
                Node(*pos)

        screen.fill((255, 255, 255))

        for node in Node.instances:
            pg.draw.circle(screen, (0, 0, 0), (node.x, node.y), 5)

        pg.display.flip()

    pg.quit()
