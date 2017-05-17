#! /usr/bin/env python

import util
import time
import cv2
import numpy
import math
from operator import itemgetter

RUNNING = True
GAME_BEGIN = 0
GAME_RUNNING = 1
GAME_END = 2
GAME_STOP = 3
GAME_STATE = GAME_BEGIN

class Settings(object):
	DP = 3
	MinDistance = 26
	CannyValue = 30
	Threshold = 50
	MinRadius = 13
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
		global GAME_STATE
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
	_, thresGray = cv2.threshold(thresGray, 15, 255, cv2.THRESH_BINARY)
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
			m = cv2.getPerspectiveTransform(numpy.float32([TL,BL,BR,TR]), numpy.float32([[0,0],[0,540],[960,540],[960,0]]))
			prevContour = contour
			gameBoardROI = cv2.warpPerspective(original,m,(960,540))
			return gameBoardROI, m, prevContour
	return None, None, None

def processData(ballCenters):
	global RESOLUTION, GRID_SIZE
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
			i = numpy.array(sorted(i[:-1], key = itemgetter(0)))
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
			validPos.append(numpy.array(tempList))
	amountValidBalls = len(validPos)
	sumList = []
	for i in range(idx):
		sumList.append((0,0))
	for i in range(amountValidBalls):
		sumList += validPos[i]
	ballPositions = sumList/amountValidBalls
	return ballPositions

def init():
	global SETTINGS
	SETTINGS = Settings()
	cv2.namedWindow("settings")
	cv2.createTrackbar("DP", "settings", 3, 5, SETTINGS.updateDP)
	cv2.createTrackbar("mindist", "settings", 26, 100, SETTINGS.updateMinDistance)
	cv2.createTrackbar("cannyValue", "settings", 30, 250, SETTINGS.updateCannyValue)
	cv2.createTrackbar("threshold", "settings", 50, 75, SETTINGS.updateThreshold)
	cv2.createTrackbar("minR", "settings", 13, 100, SETTINGS.updateMinRadius)
	cv2.createTrackbar("maxR", "settings", 17, 100, SETTINGS.updateMaxRadius)
	
def getVideoFeed(src=0):
	stream = cv2.VideoCapture(src)
	stream.set(3, 1280)
	stream.set(4, 720)
	return stream

def work():

	isResizing = True
	m = False
	prevContour = None
	FPS = 15.
	FPSCounter = 0
	ballCenters = []
	stream = getVideoFeed()
	
	while RUNNING:
		handle_commands()
		begin = time.time()
		
		if stream.isOpened():
			grabbed, original = stream.read()
			original = cv2.resize(original, (960,540))
			drawOriginal = original.copy()
			grayscaleOriginal = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
			if cv2.countNonZero(grayscaleOriginal) == 0:
				print("Reference is set, black image received. Close other applications that use this camera!")
			
			if GAME_STATE == GAME_BEGIN:
				if isResizing:
					gameBoardROI, m, prevContour = configureBoundaries(grayscaleOriginal, original, m, prevContour)
					
					if gameBoardROI is None:
						print("Failed to establish boundary! Retrying in 5 seconds...")
						time.sleep(5.0)
						continue
						
				cv2.imshow("gameBoardROI", gameBoardROI)
				time.sleep(0.1) # let's not waste too much cpu time, relax for a bit
				begin = time.time()
				
			if GAME_STATE == GAME_RUNNING:
				if gameBoardROI is None:
					print("Game started without correct ROI! Skipping ball detection.")
					time.sleep(5)
					continue
				isResizing = False
				if not isResizing:
					gameBoardROI = cv2.warpPerspective(original,m,(960,540))
					
				gameBoardROIGray = cv2.cvtColor(gameBoardROI, cv2.COLOR_BGR2GRAY)
				gameBoardROIGray = cv2.GaussianBlur(gameBoardROIGray, (3,3),4)
				gameBoardROIGray = cv2.erode(gameBoardROIGray, (20,20))
				gameBoardROIGray = cv2.dilate(gameBoardROIGray, (20,20))
				gameBoardROIGray = cv2.dilate(gameBoardROIGray, (20,20))
				gameBoardROIGray = cv2.erode(gameBoardROIGray, (20,20))
				gameBoardROIGray = cv2.Canny(gameBoardROIGray, 60,80, apertureSize = 3)
				gameBoardROIGray = cv2.GaussianBlur(gameBoardROIGray, (7,7),0)
				
				dpValue, minDist, cannyValue, threshold, minR, maxR = SETTINGS.get()
				circles = cv2.HoughCircles(gameBoardROIGray, cv2.HOUGH_GRADIENT, dpValue, minDist, param1 = cannyValue, param2 = threshold, minRadius = minR, maxRadius = maxR)
				
				if len(circles) > 0:
					ballCenters.append([])
					for i in circles[0,:20]:
						cv2.circle(gameBoardROI,(i[0],i[1]),i[2],(0,255,0),2)
						cv2.circle(gameBoardROI,(i[0],i[1]),2,(0,0,255),3)
						ballCenters[-1].append((i[0],i[1]))
						
					ballCenters[-1].append(len(circles[0]))
					
				cv2.imshow("drawOriginal", drawOriginal)
				cv2.imshow("gameBoardROI", gameBoardROI)
				cv2.imshow("gameBoardROIGray", gameBoardROIGray)
				
				if FPSCounter == FPS-1:
					if len(ballCenters) > 0:
						ballPositions = processData(ballCenters)
						IR_INPUT.send(1)
					else:
						ballPositions = []
					ballCenters = []
					
					if len(ballPositions) != 0:
						for x,y in ballPositions:
							cv2.circle(gameBoardROI,(int(x),int(y)),10,(255,0,0),-1)
						cv2.imshow("gameBoardROIStatic", gameBoardROI)
					else:
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
		else:
			print("No camera detected! Retrying in 5 seconds...")
			time.sleep(5)
			stream = getVideoFeed()
			
	cv2.destroyAllWindows()
	stream.release()

# Run this from other code
def run(cc_queue, ir_input, resolution, grid_size):
	global CC_QUEUE, IR_INPUT, RESOLUTION, GRID_SIZE
	CC_QUEUE = cc_queue
	IR_INPUT = ir_input
	RESOLUTION = resolution
	GRID_SIZE = grid_size
	try:
		print("Running IR module...")
		init()
		work()
	except KeyboardInterrupt as e:
		shutdown()
