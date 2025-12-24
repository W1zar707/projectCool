from numpy import ndarray
import commands
import cv2
class Finger:
    image: ndarray = None
    def __init__(self, icon,command):
        self.visualBox = None
        self.collisionBox = None
        self.isPressed = False
        self.command = command
        self._icon = icon

    @property
    def icon(self):
        if self._icon:
            return getattr(self._icon[0], f"{self._icon[1]}")  # всегда свежее!
        return None

    def vector(self, x, y, x2, y2) -> int:
        return abs(int(((x - x2) ** 2 + (y - y2) ** 2) ** 0.5))
    def createBoxes(self,x,y,x2,y2):
        self.createCollisionBox(x,y,x2,y2)
        if self._icon:
            self.createVisualBox(x,y,x2,y2)
    def createCollisionBox(self, x, y, x2, y2):
        y = int(y * Finger.image.shape[0])
        x = int(x * Finger.image.shape[1])
        y2 = int(y2 * Finger.image.shape[0])
        x2 = int(x2 * Finger.image.shape[1])
        radius = self.vector(x, y, x2, y2)
        height = radius*2
        width = radius*2
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
        if y + height > Finger.image.shape[0]:
            height = Finger.image.shape[0] - y
        self.collisionBox = (x, y, width, height)

    def createVisualBox(self, x, y, x2, y2):
        global image
        y = int(y * Finger.image.shape[0])
        x = int(x * Finger.image.shape[1])
        y2 = int(y2 * Finger.image.shape[0])
        x2 = int(x2 * Finger.image.shape[1])
        radius = self.vector(x, y, x2, y2)
        self.visualBox = self.icon
        height = radius * 2
        width = radius * 2
        self.visualBox = cv2.resize(self.visualBox, (width, height))
        x -= radius
        y -= radius
        if x > Finger.image.shape[1] or y > Finger.image.shape[0]:
            self.visualBox = None
            return
        if x < 0:
            width = width + x
            self.visualBox = self.visualBox[:,-width:]
            x = 0
        if y < 0:
            height = height + y
            self.visualBox = self.visualBox[-height:,:]
            y = 0
        if x + width > Finger.image.shape[1]:
            width = Finger.image.shape[1] - x
            self.visualBox = self.visualBox[:,:width]
        if y + height > Finger.image.shape[0]:
            height = Finger.image.shape[0] - y
            self.visualBox = self.visualBox[:height,:]
        if height <=0 or width <= 0:
            self.visualBox = None
            return