from enum import Enum


class Direction(Enum):
    UP = 1,
    DOWN = 2,
    LEFT = 3
    RIGHT = 4


def direction_to_str(direction):
    if direction == Direction.UP:
        return 'UP'
    if direction == Direction.RIGHT:
        return 'DOWN'
    if direction == Direction.DOWN:
        return 'LEFT'
    if direction == Direction.LEFT:
        return 'RIGHT'


def get_direction(coords1, coords2):
    # x coord same - up or down
    if coords1[0] == coords2[0]:
        if coords1[1] < coords2[1]:
            return Direction.UP
        else:
            return Direction.DOWN
    # y coord same - left of right
    else:
        if coords1[0] < coords2[0]:
            return Direction.RIGHT
        else:
            return Direction.LEFT


def get_target_direction(position):
    return get_direction(position, [0, 0])


def rotate_right(direction):
    if direction == Direction.UP:
        return Direction.RIGHT
    if direction == Direction.RIGHT:
        return Direction.DOWN
    if direction == Direction.DOWN:
        return Direction.LEFT
    if direction == Direction.LEFT:
        return Direction.UP
