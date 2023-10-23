import pygame as pg
from fields.polylines import PolylinesField
from fields.vertexes import VertexField
from fields.nodes import NodesField

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SEGMENT_STEP = 5

if __name__ == "__main__":

    pg.init()
    pg.display.set_caption('Epic Sprouts')
    screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])

    vertex_field = VertexField()
    nodes_field = NodesField(vertex_field, screen)
    polyline_field = PolylinesField(vertex_field, screen)

    nodes_field.generate_field(15, 100)

    running = True
    drawing = False

    start_node = 0

    while running:

        pos = pg.mouse.get_pos()
        over_node = nodes_field.over_node(pos)

        screen.fill((255, 255, 255))
        polyline_field.draw()
        nodes_field.draw(over_node)

        pg.display.flip()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif (
                (event.type == pg.MOUSEBUTTONDOWN) and
                (over_node > -1) and
                (nodes_field.get_degree(over_node) < 3)
            ):
                polyline_field.start_polyline()
                polyline_field.push_vertex(pos, SEGMENT_STEP)
                start_node = over_node
                nodes_field.rise_degree(start_node)
                drawing = True
            elif event.type == pg.MOUSEBUTTONUP and drawing:
                if (over_node < 0) or (nodes_field.get_degree(over_node) > 2):
                    polyline_field.pop()
                    nodes_field.lower_degree(start_node)
                else:
                    nodes_field.rise_degree(over_node)
                drawing = False

        if drawing:
            polyline_field.push_vertex(pos, SEGMENT_STEP)

    pg.quit()
