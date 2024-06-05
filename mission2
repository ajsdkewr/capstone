#include <Arduino.h>
#include <SoftwareSerial.h>
#include <DFRobotDFPlayerMini.h>

// 핀 정의
const int blueLEDPin = 10;
const int redLEDPin = 9;
const int pressureSensor1Pin = A1;
const int pressureSensor2Pin = A0;
const int bluePiezoPin = 6; // 첫 번째 피에조 스피커 핀
const int redPiezoPin = 7; 

// 시간 상수
const unsigned long missionDuration = 3000; // 미션 시간: 3초
const unsigned long cycleTime = 2000; // 미션 주기: 2초
const unsigned long minLEDOnDelay = 500; // LED가 켜지기 전 최소 지연시간: 0.5초
const unsigned long maxLEDOnDelay = 1500; // LED가 켜지기 전 최대 지연시간: 1.5초
const unsigned long initialDelay = 5000; // 초기 지연 시간: 5초

const int lowerThreshold = 300; // 압력 하한 임계값
const int upperThreshold = 500; // 압력 상한 임계값
const int checkInterval = 50; // 체크 주기 (ms)
const int numSamples = missionDuration / checkInterval; // 3초 동안의 샘플 개수

unsigned long lastUpdateTime = 0;
unsigned long nextLEDOnTime = 0;
unsigned long missionStartTime = 0;
bool ledIsOn = false;
bool missionInProgress = false;
bool missionStarted = false; // 미션 시작 플래그
bool realMissionComplete = false; // 실제 미션 완료 플래그
bool initialDelayPassed = false; // 초기 지연 시간 경과 여부
int consecutiveSuccessCount = 0; // 연속된 성공 횟수
int consecutiveFailCount = 0; // 연속된 실패 횟수
int counter = 0;


SoftwareSerial MP3Module(2, 3);
DFRobotDFPlayerMini MP3Player;

void setup() {
  // 시리얼 모니터 초기화
  Serial.begin(9600);

  // MP3 모듈 초기화
  MP3Module.begin(9600);
  if (!MP3Player.begin(MP3Module)) { // MP3 모듈을 초기화합니다. 초기화에 실패하면 오류를 발생시킵니다.
    Serial.println(F("Unable to begin:"));
    Serial.println(F("1.Please recheck the connection!"));
    Serial.println(F("2.Please insert the SD card!"));
    while (true);
  }
  delay(1);
  MP3Player.volume(15);  // 볼륨을 조절합니다. 0~30까지 설정이 가능합니다.

  // LED 핀을 출력으로 설정
  pinMode(blueLEDPin, OUTPUT);
  pinMode(redLEDPin, OUTPUT);
  pinMode(bluePiezoPin, OUTPUT); // 피에조 스피커 핀을 출력으로 설정
  pinMode(redPiezoPin, OUTPUT); // 피에조 스피커 핀을 출력으로 설정

  // 초기에는 LED 끄기
  digitalWrite(blueLEDPin, LOW);
  digitalWrite(redLEDPin, LOW);
  noTone(bluePiezoPin); // 피에조 스피커 소리 끄기
  noTone(redPiezoPin); // 피에조 스피커 소리 끄기

  // 미션 시작 전에 1번 MP3 파일 재생
  missionStartTime = millis(); // 현재 시간 저장
}

void loop() {
  

  // Python으로부터 미션 시작 신호를 받았는지 확인
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == 'y') {
      MP3Player.play(3);
      counter++;
      delay(3000);
    }
  }

  if (counter > 0) {
      executeMission();
    }
}
  

void executeMission()  {
  unsigned long currentTime = millis();
  // 초기 지연 시간이 지나지 않았으면 대기
  if (!initialDelayPassed) {
    if (currentTime - missionStartTime >= initialDelay) {
      initialDelayPassed = true; // 초기 지연 시간 경과 플래그 설정
      lastUpdateTime = currentTime; // 미션 주기 타이머 초기화
    } else {
      return; // 초기 지연 시간 동안 아무 작업도 하지 않음
    }
  }

  // 실제 미션이 완료된 경우, 모든 미션을 종료
  if (realMissionComplete) {

    lastUpdateTime = 0;
    nextLEDOnTime = 0;
   missionStartTime = 0;
    ledIsOn = false;
    missionInProgress = false;
   missionStarted = false; // 미션 시작 플래그
    realMissionComplete = false; // 실제 미션 완료 플래그
   initialDelayPassed = false; // 초기 지연 시간 경과 여부
    consecutiveSuccessCount = 0; // 연속된 성공 횟수
   consecutiveFailCount = 0; // 연속된 실패 횟수
   counter = 0;
    return;
  }

  // 새로운 미션 주기를 시작할 시간인지 확인
  if (currentTime - lastUpdateTime >= cycleTime) {
    lastUpdateTime = currentTime;
    missionInProgress = true;
    ledIsOn = false;
    missionStarted = true; // 미션이 시작되었음을 표시
    // LED를 0.5초에서 1.5초 사이의 무작위 지연 시간 후에 켜도록 예약
    nextLEDOnTime = currentTime + random(minLEDOnDelay, maxLEDOnDelay + 1);
  }

  // 미션 중 예약된 시간에 LED를 켜기
  if (missionInProgress && !ledIsOn && currentTime >= nextLEDOnTime) {
    startMission();
    ledIsOn = true;
    missionStartTime = currentTime; // 센서를 누르는 시간을 초기화
  }

  // 미션과 LED가 활성화된 경우 센서 입력 처리
  if (missionInProgress && ledIsOn) {
    checkMission(currentTime);
  }
}

void startMission() {
  // 무작위로 LED 선택
  bool lightBlue = random(2) > 0; // 0 또는 1을 무작위로 반환

  if (lightBlue) {
    digitalWrite(blueLEDPin, HIGH);
    digitalWrite(redLEDPin, LOW);
  } else {
    digitalWrite(redLEDPin, HIGH);
    digitalWrite(blueLEDPin, LOW);
  }
}

void checkMission(unsigned long currentTime) {
  int pressureSum1 = 0; // 첫 번째 압력 센서 값 합계
  int pressureSum2 = 0; // 두 번째 압력 센서 값 합계
  bool ledOn = false; // LED 상태

  // 3초 동안 압력 센서 값을 측정하여 합산
  for (int i = 0; i < numSamples; ++i) {
    int pressure1 = analogRead(pressureSensor1Pin);
    int pressure2 = analogRead(pressureSensor2Pin);
    pressureSum1 += pressure1;
    pressureSum2 += pressure2;

    // 두 압력 센서의 값이 200에서 300 사이면 LED를 켬
    if (pressure1 > lowerThreshold && pressure1 < upperThreshold && pressure2 > lowerThreshold && pressure2 < upperThreshold) {
      if (!ledOn) {
        digitalWrite(blueLEDPin, HIGH);
        digitalWrite(redLEDPin, HIGH);
        ledOn = true;
          // 피에조 스피커에서 1000Hz 소리를 재생
      }
      tone(redPiezoPin, 1000);
    }

    else {
      noTone(redPiezoPin);
    }

    delay(checkInterval);
  }

  // 평균 압력 계산
  int averagePressure1 = pressureSum1 / numSamples;
  int averagePressure2 = pressureSum2 / numSamples;

  // 평균 압력 출력 (디버깅용)
  Serial.print("Average Pressure 1: ");
  Serial.print(averagePressure1);
  Serial.print("  Average Pressure 2: ");
  Serial.println(averagePressure2);

  // 양쪽 압력 센서의 평균 값이 200에서 300 사이인지 확인
  if (averagePressure1 > lowerThreshold && averagePressure1 < upperThreshold && averagePressure2 > lowerThreshold && averagePressure2 < upperThreshold) {
    Serial.println("Mission Success"); // 시리얼 모니터에 "Mission Success" 출력
    noTone(redPiezoPin);
    // 파랑색 LED를 깜빡임
    blinkLED(blueLEDPin);
    MP3Player.play(4);
    delay(1000);
    consecutiveSuccessCount++;
    
    if (consecutiveSuccessCount >= 3) { // 10회 이상의 연속 성공이 발생한 경우
      noTone(redPiezoPin);
      Serial.println("Real mission complete");
      consecutiveSuccessCount = 0; // 연속 성공 횟수 초기화
      blinkLED(blueLEDPin); // 파란 LED 깜빡이기
      MP3Player.play(1); // "Real Mission Complete" 시 2번 MP3 파일 재생
      realMissionComplete = true; // 모든 미션 종료
    }
    consecutiveFailCount = 0; // 연속 실패 횟수 초기화
  } else {
    Serial.println("Mission Failed"); // 시리얼 모니터에 "Mission Failed" 출력
    noTone(redPiezoPin);
    // 빨강색 LED를 깜빡임
    blinkLED(redLEDPin);
    consecutiveFailCount++;
    if (consecutiveFailCount >= 3) { // 3회 이상의 연속 실패가 발생한 경우
      Serial.println("Real Mission Failed");
      consecutiveFailCount = 0; // 연속 실패 횟수 초기화
      consecutiveSuccessCount = 0; // 연속 성공 횟수 초기화
      blinkLED(redLEDPin); // 빨간 LED 깜빡이기
    }
  }

  missionInProgress = false;
  digitalWrite(blueLEDPin, LOW);
  digitalWrite(redLEDPin, LOW);
}

void blinkLED(int pin) {
  for (int i = 0; i < 5; i++) {
    digitalWrite(pin, HIGH);
    delay(100);
    digitalWrite(pin, LOW);
    delay(100);
  }
}
