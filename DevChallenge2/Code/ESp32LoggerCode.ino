#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <SD.h>
#include <SPI.h>

Adafruit_MPU6050 mpu;
const int chipSelect = 5; 

int startHour = 0;
int startMinute = 0;
int startSecond = 0;
unsigned long startTimeMs = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10); 


  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) delay(10);
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);


  if (!SD.begin(chipSelect)) {
    Serial.println("SD card initialization failed!");
    while (1) delay(10);
  }

  Serial.println("Enter current time in HH:MM:SS format to start logging:");
  while (!Serial.available()) {
    delay(100);
  }
  
  String timeInput = Serial.readStringUntil('\n');
  timeInput.trim();
  
  // Parse HH:MM:SS
  if (timeInput.length() >= 8) {
    startHour = timeInput.substring(0, 2).toInt();
    startMinute = timeInput.substring(3, 5).toInt();
    startSecond = timeInput.substring(6, 8).toInt();
    Serial.println("Time set! Unplug from PC and start your run.");
  } else {
    Serial.println("Invalid format. Defaulting to 00:00:00");
  }

  // Create/Open CSV file and write header
  File dataFile = SD.open("/run_log.csv", FILE_WRITE);
  if (dataFile) {
    dataFile.println("Time,Accel_X,Accel_Y,Accel_Z");
    dataFile.close();
  }
  
  startTimeMs = millis();
}

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);


  unsigned long elapsedMs = millis() - startTimeMs;
  unsigned long totalSeconds = (startHour * 3600) + (startMinute * 60) + startSecond + (elapsedMs / 1000);
  
  int currentHour = (totalSeconds / 3600) % 24;
  int currentMinute = (totalSeconds / 60) % 60;
  int currentSec = totalSeconds % 60;

  // Format time as HH:MM:SS
  char timeString[9];
  sprintf(timeString, "%02d:%02d:%02d", currentHour, currentMinute, currentSec);

  // Log to SD Card
  File dataFile = SD.open("/run_log.csv", FILE_APPEND);
  if (dataFile) {
    dataFile.print(timeString);
    dataFile.print(",");
    dataFile.print(a.acceleration.x);
    dataFile.print(",");
    dataFile.print(a.acceleration.y);
    dataFile.print(",");
    dataFile.println(a.acceleration.z);
    dataFile.close();
  }

  delay(100); 
}