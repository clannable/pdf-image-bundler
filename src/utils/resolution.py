from enum import Enum
from PIL.Image import Image     

class Orientation(Enum):
    PORTRAIT = 0
    LANDSCAPE = 1
    SQUARE = 2

class Resolution(object):
    width: float
    height: float

    def getOrientation(self) -> Orientation:
        pass
    
class Resolution(object):
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def getOrientation(self) -> Orientation:
        if self.width < self.height:
            return Orientation.PORTRAIT
        elif self.width > self.height:
            return Orientation.LANDSCAPE
        else:
            return Orientation.SQUARE
    
    def __iter__(self):
        return tuple((self.width, self.height))
    
    def toTuple(self):
        return (round(self.width, 2), round(self.height, 2))
    
    @staticmethod
    def fromImage(im: Image):
        (width, height) = im.size
        (dpiW, dpiH)= im.info["dpi"]
        return Resolution(float((width / dpiW)), float((height / dpiH)))

    def normalize(self, width: float, height: float) -> Resolution:
        scale = 1
        orientation = self.getOrientation()
        if orientation == Orientation.PORTRAIT: #portrait
            if self.width != width:
                scale = float(width / self.width)
                
        elif orientation == Orientation.LANDSCAPE: #landscape
            if self.height != height:
                scale = float(height / self.height)
        
        else:
            scale = float(min(height, width) / self.width)
            
        return self.scale(scale)
    
    def scale(self, scale: float) -> Resolution:
        return Resolution(self.width * scale, self.height * scale)
    