from numpy import ndarray


class Finger:
    image: ndarray = None
    def __init__(self, coordinates):
        self.box = self.createBox(*coordinates)
        self.isPressed = False

    def vector(self, x, y, x2, y2) -> int:
        return int(((x - x2) ** 2 + (y - y2) ** 2) ** 0.5)

    def createBox(self, x, y, x2, y2):
        global image
        y = int(y * Finger.image.shape[0])
        x = int(x * Finger.image.shape[1])
        y2 = int(y2 * Finger.image.shape[0])
        x2 = int(x2 * Finger.image.shape[1])
        radius = self.vector(x, y, x2, y2)
        height = radius * 2
        width = radius * 2
        x -= radius
        y -= radius
        if x > Finger.image.shape[1] or y > Finger.image.shape[0]:
            return
        if x < 0:
            width = width + x
            x = 0
        if y < 0:
            height = height + y
            y = 0
        if x + width > Finger.image.shape[1]:
            width = Finger.image.shape[1] - x
        if x + height > Finger.image.shape[0]:
            height = Finger.image.shape[0] - y
        return (x, y, width, height)