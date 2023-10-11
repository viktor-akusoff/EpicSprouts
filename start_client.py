import pygame as pg
from client.entities import PolyLine

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

if __name__ == "__main__":
    pg.init()
    pg.display.set_caption('Epic Sprouts')
    screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])

    running = True
    line = None
    while running:
        pos = pg.mouse.get_pos()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                line = PolyLine(10)
                line.push_vertex(*pos)
            elif (event.type == pg.MOUSEBUTTONUP) and line:
                line.push_vertex(*pos)
                line.rect_space.finish()
                line = None

        if line and line.is_edge_end(*pos):
            if line.cross_detect(*pos):
                line = None
                PolyLine.pop()
            else:
                line.push_vertex(*pos)

        screen.fill((255, 255, 255))

        for polyline in PolyLine.instances:
            polyline.draw(screen, False)

        pg.display.flip()

    pg.quit()
