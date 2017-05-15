from threading import Thread
import cv2

def onChange(x):
    pass

class SettingThread:
	def __init__(self):
		cv2.namedWindow("settings")
		cv2.resizeWindow("settings", 300, 650)
		cv2.createTrackbar("DP", "settings", 3, 5, onChange)
		cv2.createTrackbar("mindist", "settings", 26, 100, onChange)
		cv2.createTrackbar("cannyValue", "settings", 30, 250, onChange)
		cv2.createTrackbar("threshold", "settings", 50, 75, onChange)
		cv2.createTrackbar("minR", "settings", 13, 100, onChange)
		cv2.createTrackbar("maxR", "settings", 17, 100, onChange)
		self.stopped = False
		
	def start(self):
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, args=())
		t.daemon = True
		t.start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return

			self.dpValue = cv2.getTrackbarPos("DP", "settings")
			self.minDist = cv2.getTrackbarPos("mindist", "settings")
			self.cannyValue = cv2.getTrackbarPos("cannyValue", "settings")
			self.threshold = cv2.getTrackbarPos("threshold", "settings")
			self.minR = cv2.getTrackbarPos("minR", "settings")
			self.maxR = cv2.getTrackbarPos("maxR", "settings")

	def getSettings(self):
		return self.dpValue,self.minDist,self.cannyValue,self.threshold,self.minR,self.maxR

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True



