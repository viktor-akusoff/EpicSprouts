import pygame as pg
from client.entities import PolyLine, Node

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

if __name__ == "__main__":
    pg.init()
    pg.display.set_caption('Epic Sprouts')
    screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
    Node.generate_field(screen, 15)
    running = True
    line = None
    while running:
        pos = pg.mouse.get_pos()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                if Node.belongs_to_nodes(*pos) > -1:
                    line = PolyLine(5)
                    line.push_vertex(*pos)
            elif (event.type == pg.MOUSEBUTTONUP) and line:
                if (Node.belongs_to_nodes(*pos) < 0):
                    PolyLine.pop()
                else:
                    line.push_vertex(*pos)
                    line.rect_space.finish()
                line = None

        if line and line.is_edge_end(*pos):
            if (Node.belongs_to_nodes(*pos) < 0) and line.cross_detect(*pos):
                line = None
                PolyLine.pop()
            else:
                line.push_vertex(*pos)

        screen.fill((255, 255, 255))

        PolyLine.draw_all(screen)
        Node.draw_all(screen, *pos)

        pg.display.flip()

    pg.quit()
