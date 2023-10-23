import pygame as pg
from fields.vertexes import VertexField
from fields.nodes import NodesField

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

if __name__ == "__main__":

    pg.init()
    pg.display.set_caption('Epic Sprouts')
    screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])

    vertex_field = VertexField()
    nodes_field = NodesField(vertex_field, screen)

    nodes_field.generate_field(15, 100)

    running = True

    while running:

        pos = pg.mouse.get_pos()
        over_node = nodes_field.over_node(pos)

        screen.fill((255, 255, 255))
        nodes_field.draw(over_node)

        pg.display.flip()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

    pg.quit()
