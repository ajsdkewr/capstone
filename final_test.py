import serial
import time
from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
import numpy as np
import imutils
import dlib
import cv2

# Initialize Arduino serial connection
arduino = serial.Serial('COM3', 9600)
time.sleep(2)  # Wait for Arduino to initialize

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def mouth_aspect_ratio(mouth):
    A = dist.euclidean(mouth[0], mouth[6])
    B = dist.euclidean(mouth[3], mouth[9])
    mar = (B / A)
    return mar

def head_aspect_ratio(nose, jaw):
    A = dist.euclidean(nose[0], nose[6])
    B = dist.euclidean(nose[6], jaw[8])
    har = (A / B)
    return har

# Constants
EYE_AR_THRESH = 0.28
EYE_AR_CONSEC_FRAMES = 48
MOUTH_AR_THRESH = 2
MOUTH_AR_CONSEC_FRAMES = 10
HEAD_AR_THRESH = 1.5
HEAD_AR_CONSEC_FRAMES = 10
EYE_COUNTER = 0
MOUTH_COUNTER = 0
HEAD_COUNTER = 0
ALARM_ON = False

COUNTER = 0
NORMAL_MOUTH = 3
PRE_NORMAL_MOUTH = 0
NORMAL_HEAD = 3
PRE_NORMAL_HEAD = 0
DROWN = 0

print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("/Users/leblo/Desktop/Faster_facial_landmarks/shape_predictor_68_face_landmarks.dat")

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]
(nStart, nEnd) = face_utils.FACIAL_LANDMARKS_IDXS["nose"]
(jStart, jEnd) = face_utils.FACIAL_LANDMARKS_IDXS["jaw"]

print("[INFO] starting video stream thread...")
vs = VideoStream(src=0).start()
time.sleep(1.0)

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)
    
    for rect in rects:
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        Mouth = shape[mStart:mEnd]
        Nose = shape[nStart:nEnd]
        Jaw = shape[jStart:jEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        MouthRatio = mouth_aspect_ratio(Mouth)
        HeadRatio = head_aspect_ratio(Nose, Jaw)
        ear = (leftEAR + rightEAR) / 2.0

        if DROWN == 0:
            if MouthRatio > MOUTH_AR_THRESH * NORMAL_MOUTH:
                MOUTH_COUNTER += 1
                if MOUTH_COUNTER >= MOUTH_AR_CONSEC_FRAMES:
                    cv2.putText(frame, "DROWSINESS Forewarning ALERT!", (10, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                MOUTH_COUNTER = 0

            if HeadRatio > HEAD_AR_THRESH * NORMAL_HEAD:
                HEAD_COUNTER += 1
                if HEAD_COUNTER >= HEAD_AR_CONSEC_FRAMES:
                    cv2.putText(frame, "NAP ALERT!", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    arduino.write(b'y')
                    DROWN = 1
            else:
                HEAD_COUNTER = 0

            if ear < EYE_AR_THRESH:
                EYE_COUNTER += 1
                if EYE_COUNTER >= EYE_AR_CONSEC_FRAMES:
                    cv2.putText(frame, "DROWSINESS ALERT!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    arduino.write(b'y')
                    DROWN = 1
            else:
                EYE_COUNTER = 0

            cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "HEAD: {:.2f}".format(HeadRatio), (300, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "P_N_HEAD: {:.2f}".format(PRE_NORMAL_HEAD), (280, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "N_HEAD: {:.2f}".format(NORMAL_HEAD), (300, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if COUNTER < 100:
                if (MouthRatio < 0.7) & (HeadRatio < 0.7):
                    COUNTER += 1
                    PRE_NORMAL_MOUTH += MouthRatio
                    PRE_NORMAL_HEAD += HeadRatio
                    if COUNTER == 100:
                        NORMAL_MOUTH = PRE_NORMAL_MOUTH / COUNTER
                        NORMAL_HEAD = PRE_NORMAL_HEAD / COUNTER
                        COUNTER += 1 
                        print("NORMAL_VALUE READY!")

        else:
            cv2.putText(frame, "IN MISSION", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            if arduino.in_waiting > 0:
                 data = arduino.readline().decode('utf-8').strip()
                 print(data)
                 if data == "Real mission complete":
                     DROWN = 0
                     MOUTH_COUNTER = 0
                     HEAD_COUNTER = 0
                     EYE_COUNTER = 0
            # Here you can add code to read from Arduino and reset DROWN if needed

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cv2.destroyAllWindows()
vs.stop()
