import pygame as pg
from client.entities import PolyLine, Node

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

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
                line.push_vertex(*pos)
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
                    line.push_vertex(*pos)
                    Node.rise_degree(over_node)
                    line.finish()
                    new_node = Node(*line.middle_point)
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
            if (over_node < 0) and line.cross_detect(*pos):
                line = None
                if out_node is not None:
                    Node.lower_degree(out_node)
                PolyLine.pop()
            else:
                line.push_vertex(*pos)

        screen.fill((255, 255, 255))

        PolyLine.draw_all(screen)
        Node.draw_all(screen, over_node)

        pg.display.flip()

    pg.quit()
