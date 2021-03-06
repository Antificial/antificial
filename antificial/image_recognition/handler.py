#! /usr/bin/env python

import util
import time
import cv2
import numpy as np
import math
from operator import itemgetter

RUNNING = True
GAME_BEGIN = 0
GAME_RUNNING = 1
GAME_END = 2
GAME_STOP = 3
GAME_STATE = GAME_BEGIN
STARTSIGNALSEND = False

XMIN = 25.5
XMAX = 928
XMIDDLE = (XMAX-XMIN)/2
YMIN = 28.5
YMAX = 514.5
SHOW_DEBUG_WINDOWS = True
DEBUG_BALLS_ONLY = False

class Settings(object):
    DP = 2
    MinDistance = 22
    CannyValue = 66
    Threshold = 27
    MinRadius = 10
    MaxRadius = 17

    def get(self):
        return self.DP, self.MinDistance, self.CannyValue, self.Threshold, self.MinRadius, self.MaxRadius

    def updateDP(self, value):
        self.DP = value

    def updateMinDistance(self, value):
        self.MinDistance = value

    def updateCannyValue(self, value):
        self.CannyValue = value

    def updateThreshold(self, value):
        self.Threshold = value

    def updateMinRadius(self, value):
        self.MinRadius = value

    def updateMaxRadius(self, value):
        self.MaxRadius = value

def shutdown():
    print("[IR] Shutting down...")

def handle_action(s):
    s = str(s)
    if s.startswith("[CMD]"):
        cmd = s[6:]
        if cmd == "done":
            print("[IR] Quitting")
            global RUNNING
            RUNNING = False
    elif s.startswith("[GAME_STATE]"):
        global GAME_STATE, STARTSIGNALSEND
        if int(s[12:]) == 0:
            STARTSIGNALSEND = False
        GAME_STATE = int(s[12:])

def handle_commands():
    try:
        input = CC_QUEUE.get(False)
        handle_action(input)
    except:
        pass

def getPointClosestTo(point, pointList):
    x = point[0]
    y = point[1]
    smallestDiff = 1000
    closestPoint = 0
    for actP in pointList:
        actX = actP[0][0]
        actY = actP[0][1]
        diff = abs((x-actX)+(y-actY))
        if diff < smallestDiff:
            smallestDiff = diff
            closestPoint = actP
    return closestPoint

def configureBoundaries(grayscale, original, m, prevContour):
    thresGray = cv2.GaussianBlur(grayscale, (7,7), 0)
    _, thresGray = cv2.threshold(thresGray, 20, 255, cv2.THRESH_BINARY)
    cv2.imshow("thres", thresGray)
    thresGray = cv2.dilate(thresGray,(5,5), iterations = 3)
    thresGray = cv2.blur(thresGray,(7,7))
    _, contours, _ = cv2.findContours(thresGray.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:
        contour = sorted(contours, key = cv2.contourArea, reverse = True)[:1][0]
        epsilon = 0.1*cv2.arcLength(contour,True)
        approx = cv2.approxPolyDP(contour,epsilon,True)
        if len(approx) == 4:
            TL = getPointClosestTo((0,0), approx)
            BL = getPointClosestTo((0,500), approx)
            BR = getPointClosestTo((900,900), approx)
            TR = getPointClosestTo((900,0), approx)
            TL = [(TL[0][0]-10,TL[0][1]-10)]
            BL = [(BL[0][0]-10,BL[0][1]+10)]
            BR = [(BR[0][0]+10,BR[0][1]+10)]
            TR = [(TR[0][0]+10,TR[0][1]-10)]
            m = cv2.getPerspectiveTransform(np.float32([TL,BL,BR,TR]), np.float32([[0,0],[0,540],[960,540],[960,0]]))
            prevContour = contour
            gameBoardROI = cv2.warpPerspective(original,m,(960,540))
            return gameBoardROI, m, prevContour
    return None, None, None

def processData(ballCenters):
    ballAmounts = []
    distinctAmounts = []
    for i in ballCenters:
        ballAmounts.append(i[-1])
    distinctAmounts = set(ballAmounts)
    highAmount = 0
    idx = 0
    for dis in distinctAmounts:
        count = ballAmounts.count(dis)
        if count > highAmount:
            highAmount = count
            idx = dis
    selectedCenters = []
    for i in ballCenters:
        if i[-1] == idx:
            i = np.array(sorted(i[:-1], key = itemgetter(0)))
            selectedCenters.append(i)
    snapshot = selectedCenters[0]
    amountBalls = len(selectedCenters)
    validPos = []
    for x in range(amountBalls):
        current = selectedCenters[x]
        tempList = []
        for y in range(idx):
            cx,cy = current[y]
            sx,sy = snapshot[y]
            if sx*0.95 < cx < sx*1.05 and sy*0.95 < cy < sy*1.05:
                tempList.append((cx,cy))
        if len(tempList) == idx:
            validPos.append(np.array(tempList))
    amountValidBalls = len(validPos)
    sumList = []
    for i in range(idx):
        sumList.append((0,0))
    for i in range(amountValidBalls):
        sumList += validPos[i]
    ballPositions = sumList/amountValidBalls
    return ballPositions

def convertToGameWorldCoordinates(ballPositions, player):
    global GRID_RESOLUTION, XMAX, XMIN, YMIN, YMAX, XMIDDLE
    grid_width = GRID_RESOLUTION[0]
    grid_heigth = GRID_RESOLUTION[1]

    gameCoordinates = []
    for (x,y) in ballPositions:
        x -=  (x-XMIDDLE)/45
        newX = int((x-XMIN)*(grid_width-1)/(XMAX-XMIN))
        newY = int((y-YMIN)*(grid_heigth-1)/(YMAX-YMIN))

        if newX == 0:
           newX = 1

        if newX == (grid_width - 1):
           newX = grid_width - 2

        if newY == 0:
           newY = 1

        if newY == (grid_heigth - 1):
           newY = grid_heigth - 2

        for currentX in range(newX - 1, newX + 2):
            for currentY in range(newY - 1, newY + 2):
                if currentY < grid_heigth/2:
                    gameCoordinates.append((currentX, currentY+2, player))
                else:
                    gameCoordinates.append((currentX, currentY, player))

    return gameCoordinates

def init():
    global SETTINGS, SHOW_DEBUG_WINDOWS
    SETTINGS = Settings()

    if SHOW_DEBUG_WINDOWS:
        cv2.namedWindow("settings")
        cv2.createTrackbar("DP", "settings", 2, 5, SETTINGS.updateDP)
        cv2.createTrackbar("mindist", "settings", 22, 100, SETTINGS.updateMinDistance)
        cv2.createTrackbar("cannyValue", "settings", 66, 250, SETTINGS.updateCannyValue)
        cv2.createTrackbar("threshold", "settings", 27, 75, SETTINGS.updateThreshold)
        cv2.createTrackbar("minR", "settings", 10, 100, SETTINGS.updateMinRadius)
        cv2.createTrackbar("maxR", "settings", 17, 100, SETTINGS.updateMaxRadius)

def getVideoFeed(src=0):
    stream = cv2.VideoCapture(src)
    stream.set(3, 1280)
    stream.set(4, 720)
    return stream

def add_debug_ball(coordinates, x, y, player):
    coordinates.append([x - 1, y - 1, player])
    coordinates.append([x    , y - 1, player])
    coordinates.append([x + 1, y - 1, player])
    coordinates.append([x - 1, y    , player])
    coordinates.append([x    , y    , player])
    coordinates.append([x + 1, y    , player])
    coordinates.append([x - 1, y + 1, player])
    coordinates.append([x    , y + 1, player])
    coordinates.append([x + 1, y + 1, player])
    return coordinates

def work():
    isResizing = True
    m = False
    prevContour = None
    FPS = 15.
    FPSCounter = 0
    stableBoundariesC = 0
    redBallCenters = []
    greenBallCenters = []
    stream = getVideoFeed()
    numDefects = {6}
    minimunRedHSV = np.array([144,0,41])
    maximumRedHSV = np.array([255,255,255])
    minimunGreenHSV = np.array([0,121,29])
    maximumGreenHSV = np.array([100,255,150])

    minimunRedBGR = np.array([0,0,96])
    maximumRedBGR = np.array([64,78,255])
    minimunGreenBGR = np.array([59,75,0])
    maximumGreenBGR = np.array([132,255,75])

    global STARTSIGNALSEND
    # For recording
    #fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #out.write(gameBoardROI)
    #out = cv2.VideoWriter('output.avi',fourcc, 20.0, (960,540))
    while RUNNING:
        handle_commands()
        begin = time.time()

        if DEBUG_BALLS_ONLY:
            debug_ball_coordinates = []
            debug_ball_coordinates = add_debug_ball(debug_ball_coordinates, 50, 60, 0)
            # debug_ball_coordinates = add_debug_ball(debug_ball_coordinates, 90, 10, 0)
            debug_ball_coordinates = add_debug_ball(debug_ball_coordinates, 70, 60, 1)
            IR_INPUT.send(debug_ball_coordinates)
            # cv2.destroyAllWindows()
            # stream.release()
            # return
            time.sleep(1)
            continue

        if not stream.isOpened():
            print("No camera detected! Retrying in 5 seconds...")
            time.sleep(5)
            stream = getVideoFeed()
            continue

        grabbed, original = stream.read()
        original = cv2.resize(original, (960,540))
        drawOriginal = original.copy()
        grayscaleOriginal = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        if cv2.countNonZero(grayscaleOriginal) == 0:
            print("Reference is set, black image received. Close other applications that use this camera!")

        if GAME_STATE == GAME_BEGIN:
            if isResizing:
                gameBoardROI, m, prevContour = configureBoundaries(grayscaleOriginal, original, m, prevContour)
                cv2.imshow("game", grayscaleOriginal)
                cv2.waitKey(1)
                if gameBoardROI is None:
                    print("Failed to establish boundary! Retrying in 5 seconds...")
                    time.sleep(5.0)
                    continue

                if stableBoundariesC == 20:
                    isResizing = False
                stableBoundariesC += 1
                continue

            gameBoardROI = cv2.warpPerspective(original,m,(960,540))
            # startROI1 = gameBoardROI[20:160, 360:600]
            # startROI2 = gameBoardROI[380:520, 360:600]
            # s1g = cv2.cvtColor(startROI1, cv2.COLOR_BGR2GRAY)
            # s2g = cv2.cvtColor(startROI2, cv2.COLOR_BGR2GRAY)


            # s1g = cv2.GaussianBlur(s1g, (9,9), 9)
            # s2g = cv2.GaussianBlur(s2g, (9,9), 9)

            # #thres1 = cv2.adaptiveThreshold(s1g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 17, 2)
            # #thres2 = cv2.adaptiveThreshold(s2g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 17, 2)

            # _, thres1 = cv2.threshold(s1g, 70, 255, cv2.THRESH_BINARY_INV)
            # _, thres2 = cv2.threshold(s2g, 70, 255, cv2.THRESH_BINARY_INV)

            # #thres1 = cv2.GaussianBlur(thres1, (11,11), 0)
            # #thres2 = cv2.GaussianBlur(thres2, (11,11), 0)

            # _, s1Contours,_ = cv2.findContours(thres1.copy(),cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            # _, s2Contours,_ = cv2.findContours(thres2.copy(),cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

            # s1Contours = sorted(s1Contours, key = cv2.contourArea, reverse = True)[:1]
            # s2Contours = sorted(s2Contours, key = cv2.contourArea, reverse = True)[:1]

            # cv2.drawContours(startROI1, s1Contours, -1, (0,0,255))
            # cv2.drawContours(startROI2, s2Contours, -1, (0,0,255))




            # if not STARTSIGNALSEND:
                # if len(s1Contours) > 0:
                    # hull = cv2.convexHull(s1Contours[0], returnPoints = False)
                    # hulld = cv2.convexHull(s1Contours[0], returnPoints = True)

                    # if len(hull) > 0:
                        # cv2.drawContours(startROI1, [hulld], 0, (0,255,0))
                        # defects = cv2.convexityDefects(s1Contours[0],hull)
                        # if defects is not None:
                            # for i in range(defects.shape[0]):
                               # s,e,f,d = defects[i,0]
                               # start = tuple(s1Contours[0][s][0])
                               # end = tuple(s1Contours[0][e][0])
                               # far = tuple(s1Contours[0][f][0])
                               # cv2.line(startROI1,start,end,[0,255,0],2)
                               # cv2.circle(startROI1,far,5,[0,0,255],-1)
                            # if len(defects) in numDefects:
                                # print("Virtual spacebar" + str(len(defects)))
                                # IR_INPUT.send("[KEY] 32") # Virtual spacebar
                                # STARTSIGNALSEND = True

                # if len(s2Contours) > 0:
                    # hull = cv2.convexHull(s2Contours[0], returnPoints = False)
                    # hulld = cv2.convexHull(s2Contours[0], returnPoints = True)
                    # if len(hull) > 0:
                        # cv2.drawContours(startROI2, [hulld], 0, (0,255,0))
                        # defects = cv2.convexityDefects(s2Contours[0],hull)
                        # if defects is not None:
                            # for i in range(defects.shape[0]):
                               # s,e,f,d = defects[i,0]
                               # start = tuple(s2Contours[0][s][0])
                               # end = tuple(s2Contours[0][e][0])
                               # far = tuple(s2Contours[0][f][0])
                               # cv2.line(startROI2,start,end,[0,255,0],2)
                               # cv2.circle(startROI2,far,5,[0,0,255],-1)
                            # if len(defects) in numDefects:
                                # print("Virtual spacebar" + str(len(defects)))
                                # IR_INPUT.send("[KEY] 32") # Virtual spacebar
                                # STARTSIGNALSEND = True


            # if SHOW_DEBUG_WINDOWS:
                # cv2.imshow("startROI1", s1g)
                # cv2.imshow("startROI2", s2g)
                # cv2.imshow("thres1", thres1)
                # cv2.imshow("thres2", thres2)
                # cv2.imshow("gameBoardROI", gameBoardROI)

            time.sleep(0.2) # let's not waste too much cpu time, relax for a bit
            begin = time.time()

        if GAME_STATE == GAME_RUNNING:

            if gameBoardROI is None:
                print("Game started without correct ROI! Skipping ball detection.")
                time.sleep(5)
                continue

            if not isResizing:
                gameBoardROI = cv2.warpPerspective(original,m,(960,540))

            gameBoardROI = cv2.cvtColor(gameBoardROI, cv2.COLOR_BGR2HSV)

            redMask = cv2.inRange(gameBoardROI, minimunRedHSV, maximumRedHSV)
            redFilter = cv2.bitwise_and(gameBoardROI, gameBoardROI, mask = redMask)

            greenMask = cv2.inRange(gameBoardROI, minimunGreenHSV, maximumGreenHSV)
            greenFilter = cv2.bitwise_and(gameBoardROI, gameBoardROI, mask = greenMask)


            gameBoardROIGray = cv2.cvtColor(redFilter, cv2.COLOR_BGR2GRAY)
            redCircleImage = cv2.GaussianBlur(gameBoardROIGray, (5,5),4)

            gameBoardROIGray = cv2.cvtColor(greenFilter, cv2.COLOR_BGR2GRAY)
            greenCircleImage = cv2.GaussianBlur(gameBoardROIGray, (5,5),4)

            #gameBoardROIGray = cv2.erode(gameBoardROIGray, (20,20))
            #gameBoardROIGray = cv2.dilate(gameBoardROIGray, (20,20))
            #gameBoardROIGray = cv2.dilate(gameBoardROIGray, (20,20))
            #gameBoardROIGray = cv2.erode(gameBoardROIGray, (20,20))
            gameBoardROIGray = cv2.Canny(gameBoardROIGray, 60,80, apertureSize = 3)
            gameBoardROIGray = cv2.GaussianBlur(gameBoardROIGray, (3,3),0)

            dpValue, minDist, cannyValue, threshold, minR, maxR = SETTINGS.get()
            redCircles = cv2.HoughCircles(redCircleImage, cv2.HOUGH_GRADIENT, dpValue, minDist, param1 = cannyValue, param2 = threshold, minRadius = minR, maxRadius = maxR)
            greenCircles = cv2.HoughCircles(greenCircleImage, cv2.HOUGH_GRADIENT, dpValue, minDist, param1 = cannyValue, param2 = threshold, minRadius = minR, maxRadius = maxR)

            if redCircles is not None:
                redCircles = redCircles[0,:16]
                redBallCenters.append([])
                for i in redCircles:
                    cv2.circle(gameBoardROI,(i[0],i[1]),i[2],(0,0,255),2)
                    cv2.circle(gameBoardROI,(i[0],i[1]),2,(0,0,255),3)
                    redBallCenters[-1].append((i[0],i[1]))

                redBallCenters[-1].append(len(redCircles))

            if greenCircles is not None:
                greenCircles = greenCircles[0,:16]
                greenBallCenters.append([])
                for i in greenCircles:
                    cv2.circle(gameBoardROI,(i[0],i[1]),i[2],(0,255,0),2)
                    cv2.circle(gameBoardROI,(i[0],i[1]),2,(0,255,0),3)
                    greenBallCenters[-1].append((i[0],i[1]))

                greenBallCenters[-1].append(len(greenCircles))

            if SHOW_DEBUG_WINDOWS:
                cv2.imshow("drawOriginal", drawOriginal)
                cv2.imshow("gameBoardROI", gameBoardROI)
                cv2.imshow("gameBoardROIGray", gameBoardROIGray)
                cv2.imshow("redFilter", redFilter)
                cv2.imshow("greenFilter", greenFilter)


            mergedList = []
            redBalls = []
            greenBalls = []
            if FPSCounter == FPS-1:
                if len(redBallCenters) > 0:
                    redBalls = processData(redBallCenters)
                    redBallCoordinates = convertToGameWorldCoordinates(redBalls, 0)
                    mergedList += redBallCoordinates
                else:
                    redBalls = []
                if len(greenBallCenters) > 0:
                    greenBalls = processData(greenBallCenters)
                    greenBallCoordinates = convertToGameWorldCoordinates(greenBalls, 1)
                    mergedList += greenBallCoordinates
                else:
                    greenBalls = []
                IR_INPUT.send(mergedList)
                redBallCenters = []
                greenBallCenters = []

                if SHOW_DEBUG_WINDOWS:
                    if len(redBalls) != 0:
                        for x,y in redBalls:
                            cv2.circle(gameBoardROI,(int(x),int(y)),10,(255,0,0),-1)
                    if len(greenBalls) != 0:
                        for x,y in greenBalls:
                            cv2.circle(gameBoardROI,(int(x),int(y)),10,(255,0,0),-1)

                    cv2.imshow("gameBoardROIStatic", gameBoardROI)

        if GAME_STATE == GAME_END:
            cv2.destroyAllWindows()
            time.sleep(1)

        end = time.time()
        duration = end - begin
        wait = ((1 / FPS) - duration) * 1000
        wait = int(math.ceil(wait))
        if wait <= 0:
            print("Computation is impeding framerate, dipping below %d FPS..." % FPS)
            wait = 1
        key = cv2.waitKey(wait) & 0xFF
        FPSCounter = (FPSCounter + 1) % FPS
        if key == ord("r"):
            isResizing = not isResizing
            print("%s Resize." % ("Enabled" if isResizing else "Disabled"))
        if key == ord("q"):
            cv2.destroyAllWindows()
            stream.release()
            break

    cv2.destroyAllWindows()
    stream.release()

# Run this from other code
def run(cc_queue, ir_input, grid_resolution):
    global CC_QUEUE, IR_INPUT, GRID_RESOLUTION
    CC_QUEUE = cc_queue
    IR_INPUT = ir_input
    GRID_RESOLUTION = grid_resolution
    try:
        print("Running IR module...")
        init()
        work()
    except KeyboardInterrupt as e:
        shutdown()
