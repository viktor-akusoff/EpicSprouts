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
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    vertex_field = VertexField()
    nodes_field = NodesField(vertex_field, screen)
    polyline_field = PolylinesField(screen, vertex_field, nodes_field)

    nodes_field.generate_field(16, 100)

    clock = pg.time.Clock()

    running = True
    drawing = False
    left_starting_node = False
    intersection = False
    force_move = False

    start_node = 0

    while running:
        ms = clock.tick()
        pos = pg.mouse.get_pos()
        over_node = nodes_field.over_node(pos)
        screen.fill((255, 255, 255))
        polyline_field.draw()
        nodes_field.draw(over_node)

        pg.display.flip()

        mouse = pg.mouse.get_pressed()

        if mouse[2] and vertex_field._vertexes is not None:
            force_move = True
            polyline_field.force_update(1, ms)
        elif force_move:
            force_move = False
            polyline_field.rebuild_trees()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif (
                (event.type == pg.MOUSEBUTTONDOWN) and
                (over_node > -1) and
                (nodes_field.get_degree(over_node) < 3)
            ):
                index = nodes_field.get_index(over_node)
                polyline_field.start_polyline(index)
                start_node = over_node
                nodes_field.rise_degree(start_node)
                drawing = True
                intersection = False
                left_starting_node = False
            elif (
                intersection or
                (left_starting_node and over_node > -1) or
                (event.type == pg.MOUSEBUTTONUP)
            ) and drawing:
                if (
                    intersection or
                    not left_starting_node or
                    (over_node < 0) or
                    (nodes_field.get_degree(over_node) > 2)
                ):
                    polyline_field.pop()
                    nodes_field.lower_degree(start_node)
                else:
                    index = nodes_field.get_index(over_node)
                    polyline_field.end_polyline(index)
                    polyline_field.build_tree(-1)
                    nodes_field.rise_degree(over_node)
                    last_polyline = polyline_field.get_polyline(-1)
                    if last_polyline:
                        index = last_polyline.middle_point
                        nodes_field.push_node_by_index(index)
                drawing = False
                intersection = False

        if not left_starting_node and (over_node < 0):
            left_starting_node = True

        if drawing:
            if left_starting_node:
                intersection = polyline_field.check_intersection(pos)
            polyline_field.push_vertex(pos, SEGMENT_STEP)

    pg.quit()
