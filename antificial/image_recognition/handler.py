#! /usr/bin/env python

import util
import time
import cv2
import numpy as np
import math
from .settingThread import SettingThread
from .webcamvideostream import WebcamVideoStream
from operator import itemgetter


RUNNING = True
GAME_BEGIN = 0
GAME_RUNNING = 1
GAME_END = 2
GAME_STOP = 3
GAME_STATE = GAME_BEGIN

def shutdown():
	print("[IR] Shutting down...")

def handle_action(s):
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

			m = cv2.getPerspectiveTransform(np.float32([TL,BL,BR,TR]), np.float32([[0,0],[0,540],[960,540],[960,0]]))
			prevContour = contour
			
			gameBoardROI = cv2.warpPerspective(original,m,(960,540))

	return gameBoardROI, m, prevContour

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

def work():

	# Grab reference to the camera
	cap = WebcamVideoStream(src=0).start()
	settings = SettingThread().start()
	# Pre define global variables
	m = False
	prevContour = None
	isResizing = True
	FPS = 15.
	FPSCounter = 0
	ballCenters = []
	global GAME_STATE
	# Main loop for image processing
	while RUNNING:
		begin = time.time()
		handle_commands()
		# Grab next frame from the camera
		original = cap.read()

		# Scale down for quicker processing
		original = cv2.resize(original, (960,540))

		# Get a copy to draw on without ruining the original image
		drawOriginal = original.copy()
		grayscaleOriginal = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
		cv2.imshow("drawOriginal", drawOriginal)
		if GAME_STATE == GAME_BEGIN:
			if isResizing:
				gameBoardROI, m, prevContour = configureBoundaries(grayscaleOriginal, original, m, prevContour)
			
		if GAME_STATE == GAME_RUNNING:
			print("running")
			isResizing = False
			
			if not isResizing:
				gameBoardROI = cv2.warpPerspective(original,m,(960,540))



			gameBoardROIGray = cv2.cvtColor(gameBoardROI, cv2.COLOR_BGR2GRAY)
			gameBoardROIGray = cv2.GaussianBlur(gameBoardROIGray, (3,3),4)
			gameBoardROIGray = cv2.erode(gameBoardROIGray, (20,20), iterations = 1)
			gameBoardROIGray = cv2.dilate(gameBoardROIGray, (20,20), iterations = 1)
			gameBoardROIGray = cv2.dilate(gameBoardROIGray, (20,20), iterations = 1)
			gameBoardROIGray = cv2.erode(gameBoardROIGray, (20,20), iterations = 1)
			gameBoardROIGray = cv2.Canny(gameBoardROIGray, 60,80, apertureSize = 3)
			gameBoardROIGray = cv2.GaussianBlur(gameBoardROIGray, (7,7),0)


			dpValue, minDist, cannyValue, threshold, minR, maxR = settings.getSettings()
			circles = cv2.HoughCircles(gameBoardROIGray, cv2.HOUGH_GRADIENT, dpValue, minDist, param1 = cannyValue, param2 = threshold, minRadius = minR, maxRadius = maxR)


			if len(circles) > 0:
				ballCenters.append([])
				for i in circles[0,:20]:
					# draw the outer circle
					cv2.circle(gameBoardROI,(i[0],i[1]),i[2],(0,255,0),2)
					# draw the center of the circle
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
			settings.stop()
			cap.release()
			cap.stop()
			

		end = time.time()
		duration = end-begin
		##		print(duration)
		wait = (1/FPS)-duration
		wait *= 1000
		wait = int(math.ceil(wait))
		if wait <= 0:
			print("script takes longer")
			wait = 1
		key = cv2.waitKey(wait) & 0xFF
		FPSCounter = (FPSCounter+1)%FPS

		

		if key == ord("r"):
			isResizing = (isResizing+1)%2
			toggled = "Enabled" if isResizing == 1 else "Disabled"
			print("Toggled resize, resizing is now "+toggled)
		if key == ord("q"):
			cv2.destroyAllWindows()
			settings.stop()
			cap.release()
			cap.stop()
			break
			
	cv2.destroyAllWindows()
	settings.stop()
	cap.release()
	cap.stop()
			
		


# Run this from other code
def run(cc_queue, ir_input, resolution, grid_size):
	global CC_QUEUE, IR_INPUT, RESOLUTION, GRID_SIZE
	CC_QUEUE = cc_queue
	IR_INPUT = ir_input
	RESOLUTION = resolution
	GRID_SIZE = grid_size
	
	try:
		print("Running IR module...")
		work()
	except KeyboardInterrupt as e:
		shutdown()
