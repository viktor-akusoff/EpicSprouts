import pygame as pg
from client.entities import PolyLine, Node, Vector

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

if __name__ == "__main__":
    pg.init()
    pg.display.set_caption('Epic Sprouts')
    screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
    Node.generate_field(screen, 15, 100)
    running = True
    line: PolyLine | None = None
    crossing_dot_a = False
    out_node = None
    while running:
        pos = pg.mouse.get_pos()
        over_node = Node.over_nodes(*pos)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif (
                (event.type == pg.MOUSEBUTTONDOWN) and
                (over_node > -1) and
                Node.is_free(over_node)
            ):
                line = PolyLine(5)
                node_vector = Node.get_by_id(over_node).vector
                line.push_vertex(node_vector)
                crossing_dot_a = True
                out_node = over_node
            elif (event.type == pg.MOUSEBUTTONUP) and line:
                line = None
                if out_node is not None:
                    Node.lower_degree(out_node)
                out_node = None
                PolyLine.pop()

        if line:
            if (over_node > -1) and not crossing_dot_a:
                if Node.is_free(over_node):
                    node_vector = Node.get_by_id(over_node).vector
                    line.push_vertex(node_vector)
                    Node.rise_degree(over_node)
                    line.finish()
                    new_node = Node(*line.middle_point.pair)
                    Node.rise_degree(new_node.id, 2)
                    line = None
                else:
                    line = None
                    if out_node is not None:
                        Node.lower_degree(out_node)
                    PolyLine.pop()
            elif (over_node < 0) and crossing_dot_a:
                if out_node is not None:
                    Node.rise_degree(out_node)
                crossing_dot_a = False

        if line and line.is_edge_end(*pos):
            if (over_node < 0) and line.cross_detect(Vector(*pos)):
                line = None
                if out_node is not None:
                    Node.lower_degree(out_node)
                PolyLine.pop()
            else:
                line.push_vertex(Vector(*pos))

        screen.fill((255, 255, 255))

        PolyLine.draw_all(screen)
        Node.draw_all(screen, over_node)

        pg.display.flip()

    pg.quit()
