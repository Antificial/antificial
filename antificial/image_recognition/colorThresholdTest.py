import cv2
import numpy as np

class Settings(object):
    DP = 0
    MinDistance = 0
    CannyValue = 0
    Threshold = 360
    MinRadius = 100
    MaxRadius = 100

    def get(self):
        return self.DP, self.MinDistance, self.CannyValue, self.Threshold, self.MinRadius, self.MaxRadius

    def updateRmin(self, value):
        self.DP = value

    def updateGmin(self, value):
        self.MinDistance = value

    def updateBmin(self, value):
        self.CannyValue = value

    def updateRmax(self, value):
        self.Threshold = value

    def updateGmax(self, value):
        self.MinRadius = value

    def updateBmax(self, value):
        self.MaxRadius = value

def main():
    stream = cv2.VideoCapture(0)
    stream.set(3, 1280)
    stream.set(4, 720)
    
    maxC = np.array([360,100,100])
    minC = np.array([0,0,0])
    SETTINGS = Settings()
    
    cv2.namedWindow("settings")
    cv2.createTrackbar("hmin", "settings", 0, 255, SETTINGS.updateRmin)
    cv2.createTrackbar("smin", "settings", 0, 255, SETTINGS.updateGmin)
    cv2.createTrackbar("vmin", "settings", 0, 255, SETTINGS.updateBmin)
    cv2.createTrackbar("hmax", "settings", 360, 360, SETTINGS.updateRmax)
    cv2.createTrackbar("smax", "settings", 100, 100, SETTINGS.updateGmax)
    cv2.createTrackbar("vmax", "settings", 100, 100, SETTINGS.updateBmax)
    
    
    while 1:
        _, original = stream.read()
        
        rmin, gmin, bmin, rmax, gmax, bmax = SETTINGS.get()
        maxC = np.array([rmax, gmax, bmax])
        minC = np.array([rmin, gmin, bmin])
        original = cv2.cvtColor(original, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(original, minC, maxC)
        colorRange = cv2.bitwise_and(original, original, mask = mask)
        
        cv2.imshow("g", original)
        cv2.imshow("colorRange", colorRange)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    main()