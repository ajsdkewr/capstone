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

# 각 부위별 길이 계산한 뒤 비율을 결과로 내놓는 코드 (eyetracking 코드 설명 참조)
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

# 각 부위별 기준 프레임, 기준 배수 (워드 파일 참조)
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

# 운전자의 고개 비율, 입 비율 설정을 위한 상수 (워드파일 참조) 
COUNTER = 0
NORMAL_MOUTH = 3
PRE_NORMAL_MOUTH = 0
NORMAL_HEAD = 3
PRE_NORMAL_HEAD = 0
DROWN = 0

# 얼굴 감지 랜드마크 불러오기
print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("/Users/leblo/Desktop/Faster_facial_landmarks/shape_predictor_68_face_landmarks.dat")

# 불러온 랜드마크에서 부위별 점들 모아서 저장
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]
(nStart, nEnd) = face_utils.FACIAL_LANDMARKS_IDXS["nose"]
(jStart, jEnd) = face_utils.FACIAL_LANDMARKS_IDXS["jaw"]

# 비디오 시작작
print("[INFO] starting video stream thread...")
vs = VideoStream(src=0).start()
time.sleep(1.0)

# 여기서부터 작동 코드
while True:
    # 화면에 나오도록 세팅 코드
    frame = vs.read()
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)
    
    for rect in rects:
        # 화면에 인식 부위 띄우기 위한 코드임, 상관없는 코드이므로 안 써도 됨
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        Mouth = shape[mStart:mEnd]
        Nose = shape[nStart:nEnd]
        Jaw = shape[jStart:jEnd]

        # 맨 앞에서 정의한 함수를 통해 각 변수에 비율 저장
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        MouthRatio = mouth_aspect_ratio(Mouth)
        HeadRatio = head_aspect_ratio(Nose, Jaw)

        # ear 값은 왼쪽 ear값, 오른쪽 ear값의 평균으로 계산
        ear = (leftEAR + rightEAR) / 2.0

        # DROWN가 0 일때는 졸음이 감지되지 않은 상태 졸음 감지 시 DROWN는 1로 바뀌어서 아래 코드가 실행되지 않음
        # 아래 if 문 안에 있는 3가지의 if 문은 각각 앞서 설정한 기준 상수를 통해 졸음을 감지
        # 졸음 감지 시 cv2.putText 함수로 카메라 창에 감지되었음을 알림, 또한 아두이노로 'y'라는 신호를 보내 미션 시작 신호를 보냄, Drown = 1이므로 이후 아래 코드 실행 X
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

            # 현재 ear, head ratio 등 변수 출력 함수 (보고서에 안써도 됨)
            cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "HEAD: {:.2f}".format(HeadRatio), (300, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "P_N_HEAD: {:.2f}".format(PRE_NORMAL_HEAD), (280, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "N_HEAD: {:.2f}".format(NORMAL_HEAD), (300, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # 운전자에 따라 입크기와 얼굴 비율이 다르기 때문에 각 운전자의 정상상태의 입크기와 얼굴 비율을 구하는 코드
            if COUNTER < 100:
                # 정상상태라고 판단되는 상황을 입비율 0.7 이하, 고개 비율 0.7 이하라고 가정해서 이 때만 pre_normal 변수에 비율을 저장함
                if (MouthRatio < 0.7) & (HeadRatio < 0.7):
                    COUNTER += 1
                    PRE_NORMAL_MOUTH += MouthRatio
                    PRE_NORMAL_HEAD += HeadRatio
                    # 100프레임이 되면 저장한 값을 평균을 내어 normal 변수에 저장 (이제 이 변수를 기준으로 졸음 판별 시작)
                    if COUNTER == 100:
                        NORMAL_MOUTH = PRE_NORMAL_MOUTH / COUNTER
                        NORMAL_HEAD = PRE_NORMAL_HEAD / COUNTER
                        COUNTER += 1 
                        print("NORMAL_VALUE READY!")
                        
            # 아두이노에서 신호를 받으면 아래 코드 실행
            # 만약 아두이노에서 보낸 신호가 "n"이면 졸음 감지 기준 강화
            if arduino.in_waiting > 0:
                data = arduino.readline().decode('utf-8').strip()
                 if data == "n":
                     EYE_AR_THRESH = 0.25
                     EYE_AR_CONSEC_FRAMES = 24
                     MOUTH_AR_THRESH = 1.8
                     MOUTH_AR_CONSEC_FRAMES = 8
                     HEAD_AR_THRESH = 1.4
                     HEAD_AR_CONSEC_FRAMES = 8
                        
        # else 문은 drown = 0에 대한 else 문으로 졸음이 감지되었을 때만 시작
        else:
            # 카메라 창에 "IN MISSION"이라는 표시를 나오게 함
            cv2.putText(frame, "IN MISSION", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            # 아두이노가 신호를 주면 IF 문 실행
            if arduino.in_waiting > 0:
                # 아두이노가 보낸 신호를 data에 저장하고 data가 "Real mission complete"일 경우, 다시 졸음 감지가 작동하도록 Drown, counter 변수들 0으로 설정
                 data = arduino.readline().decode('utf-8').strip()
                 print(data)
                 if data == "Real mission complete":
                     DROWN = 0
                     MOUTH_COUNTER = 0
                     HEAD_COUNTER = 0
                     EYE_COUNTER = 0
            # Here you can add code to read from Arduino and reset DROWN if needed

    # 끝내는 코드 (필요 X)
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cv2.destroyAllWindows()
vs.stop()
