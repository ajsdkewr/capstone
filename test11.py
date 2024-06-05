# import the necessary packages
from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
from threading import Thread
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2

	
def eye_aspect_ratio(eye):
	# compute the euclidean distances between the two sets of
	# vertical eye landmarks (x, y)-coordinates
	A = dist.euclidean(eye[1], eye[5])
	B = dist.euclidean(eye[2], eye[4])
	# compute the euclidean distance between the horizontal
	# eye landmark (x, y)-coordinates
	C = dist.euclidean(eye[0], eye[3])
	# compute the eye aspect ratio
	ear = (A + B) / (2.0 * C)
	# return the eye aspect ratio
	return ear

def mouth_aspect_ratio(mouth):
	# 입의 가로 길이
	A = dist.euclidean(mouth[0],mouth[6])
	# 입의 세로 길이
	B = dist.euclidean(mouth[3],mouth[9])
	# 입의 세로 가로 비율
	mouth = (B/ A)
	return mouth

def head_aspect_ratio(nose,jaw):
	# 코 길이
	A = dist.euclidean(nose[0],nose[6])
	# 코 부터 턱 길이
	B = dist.euclidean(nose[6],jaw[8])
	# 코 길이 / 코 ~ 턱 길이 비율
	head = (A / B)
	return head


# define two constants, one for the eye aspect ratio to indicate
# blink and then a second constant for the number of consecutive
# frames the eye must be below the threshold for to set off the
# alarm
EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 48
MOUTH_AR_THRESH = 2
MOUTH_AR_CONSEC_FRAMES = 10
HEAD_AR_THRESH = 1.5
HEAD_AR_CONSEC_FRAMES = 10
# initialize the frame counter as well as a boolean used to
# indicate if the alarm is going off
EYE_COUNTER = 0
MOUTH_COUNTER = 0
HEAD_COUNTER = 0
ALARM_ON = False

#하품&고개 변수 초기값 설정
COUNTER = 0
NORMAL_MOUTH = 3
PRE_NORMAL_MOUTH = 0
NORMAL_HEAD = 3
PRE_NORMAL_HEAD = 0



# initialize dlib's face detector (HOG-based) and then create
# the facial landmark predictor
print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("/Users/leblo/Desktop/Faster_facial_landmarks/shape_predictor_68_face_landmarks.dat")

# grab the indexes of the facial landmarks for the left and
# right eye, respectively
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]
(nStart, nEnd) = face_utils.FACIAL_LANDMARKS_IDXS["nose"]
(jStart, jEnd) = face_utils.FACIAL_LANDMARKS_IDXS["jaw"]

# start the video stream thread
print("[INFO] starting video stream thread...")
vs = VideoStream(src=0).start()
time.sleep(1.0)
# loop over frames from the video stream
while True:
	# grab the frame from the threaded video file stream, resize            
	# it, and convert it to grayscale
	# channels)
	frame = vs.read()
	frame = imutils.resize(frame, width=450)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	# detect faces in the grayscale frame
	rects = detector(gray, 0)
	
		# loop over the face detections
	for rect in rects:
		# determine the facial landmarks for the face region, then
		# convert the facial landmark (x, y)-coordinates to a NumPy
		# array
		shape = predictor(gray, rect)
		shape = face_utils.shape_to_np(shape)
		# extract the left and right eye coordinates, then use the
		# coordinates to compute the eye aspect ratio for both eyes
		leftEye = shape[lStart:lEnd]
		rightEye = shape[rStart:rEnd]
		Mouth = shape[mStart:mEnd]
		Nose = shape[nStart:nEnd]
		Jaw = shape[jStart:jEnd]
		leftEAR = eye_aspect_ratio(leftEye)
		rightEAR = eye_aspect_ratio(rightEye)
		MouthRatio = mouth_aspect_ratio(Mouth)
		HeadRatio = head_aspect_ratio(Nose,Jaw)
		# average the eye aspect ratio together for both eyes
		ear = (leftEAR + rightEAR) / 2.0
		
		# compute the convex hull for the left and right eye, then
		# visualize each of the eyes
		leftEyeHull = cv2.convexHull(leftEye)
		rightEyeHull = cv2.convexHull(rightEye)
		#mouthHull = cv2.convexHull(Mouth)
		#headHull = cv2.convexHull(Nose)
		#jawHull = cv2.convexHull(Jaw)
		#cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
		#cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
		#cv2.drawContours(frame, [mouthHull], -1, (0, 255, 0), 1)
		#cv2.drawContours(frame, [headHull], -1, (0, 255, 0), 1)
		#cv2.drawContours(frame, [jawHull], -1, (0, 255, 0), 1)
				# check to see if the eye aspect ratio is below the blink
		# threshold, and if so, increment the blink frame counter

		# 평소 입의 2배 크기이면 검출
		if MouthRatio > MOUTH_AR_THRESH * NORMAL_MOUTH:
			MOUTH_COUNTER += 1
			# if the eyes were closed for a sufficient number of
			# then sound the alarm
			if MOUTH_COUNTER >= MOUTH_AR_CONSEC_FRAMES:
				cv2.putText(frame, "DROWSINESS Forewarning  ALERT!", (10, 300),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
				
		# otherwise, the eye aspect ratio is not below the blink
		# threshold, so reset the counter and alarm
		else:
			MOUTH_COUNTER = 0
			
			
        # 평소 입의 2배 크기이면 검출
		if HeadRatio > HEAD_AR_THRESH * NORMAL_HEAD:
			HEAD_COUNTER += 1
			# if the eyes were closed for a sufficient number of
			# then sound the alarm
			if HEAD_COUNTER >= HEAD_AR_CONSEC_FRAMES:
				# if the alarm is not on, turn it on
				cv2.putText(frame, "NAP  ALERT!", (10, 150),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
		# otherwise, the eye aspect ratio is not below the blink
		# threshold, so reset the counter and alarm
		else:
			HEAD_COUNTER = 0


		if ear < EYE_AR_THRESH:
			EYE_COUNTER += 1
			# if the eyes were closed for a sufficient number of
			# then sound the alarm
			if EYE_COUNTER >= EYE_AR_CONSEC_FRAMES:
				# # draw an alarm on the frame
				cv2.putText(frame, "DROWSINESS ALERT!", (10, 30),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
		# otherwise, the eye aspect ratio is not below the blink
		# threshold, so reset the counter and alarm
		else:
			EYE_COUNTER = 0
			
		# draw the computed eye aspect ratio on the frame to help
		# with debugging and setting the correct eye aspect ratio
		# thresholds and frame counters
		cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
        # draw the computed eye aspect ratio on the frame to help
		# with debugging and setting the correct eye aspect ratio
		# thresholds and frame counters
		cv2.putText(frame, "HEAD: {:.2f}".format(HeadRatio), (300, 150),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
		
        # draw the computed eye aspect ratio on the frame to help
		# with debugging and setting the correct eye aspect ratio
		# thresholds and frame counters
		cv2.putText(frame, "P_N_HEAD: {:.2f}".format(PRE_NORMAL_HEAD), (280, 200),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
		
        # draw the computed eye aspect ratio on the frame to help
		# with debugging and setting the correct eye aspect ratio
		# thresholds and frame counters
		cv2.putText(frame, "N_HEAD: {:.2f}".format(NORMAL_HEAD), (300, 250),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
		
		# 100 프레임 동안 평소의 입 크기 평균 계산 후 판단 기준으로 설정
		if COUNTER < 100:
			if (MouthRatio < 0.7) & (HeadRatio < 0.7):
				COUNTER += 1
				PRE_NORMAL_MOUTH += MouthRatio
				PRE_NORMAL_HEAD += HeadRatio
				if COUNTER == 100:
					NORMAL_MOUTH = PRE_NORMAL_MOUTH/COUNTER
					NORMAL_HEAD = PRE_NORMAL_HEAD/COUNTER
					COUNTER += 1 
					cv2.putText(frame, "!!!!!!!!!!!!!!!!", (280, 200),
						cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
					

	# show the frame
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
 
	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break
# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()