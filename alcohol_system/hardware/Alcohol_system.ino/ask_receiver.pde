/*
  Alcohol Detection System with Face Recognition
  For Keyestudio KS0397 - INVERTED LOGIC VERSION
*/

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Pin definitions
const int ALCOHOL_SENSOR_PIN = A0;
const int RED_LED_PIN = 6;      // Red LED on D6 (NOT GRANTED)
const int BLUE_LED_PIN = 5;     // Blue LED on D5 (GRANTED)
const int START_BUTTON_PIN = 7;  // Button on D7

// Alcohol threshold - since sensor REVERSED (low value = alcohol)
// Clean air = 1000+, Alcohol = 50-54
// So if reading is BELOW 500, it means alcohol detected
const int ALCOHOL_THRESHOLD = 500;  // Below 500 = alcohol detected

// LCD setup
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(9600);
  
  pinMode(ALCOHOL_SENSOR_PIN, INPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BLUE_LED_PIN, OUTPUT);
  pinMode(START_BUTTON_PIN, INPUT_PULLUP);
  
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(BLUE_LED_PIN, LOW);
  
  lcd.init();
  lcd.backlight();
  
  // Warm up MQ-3 sensor
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Alcohol System");
  lcd.setCursor(0, 1);
  lcd.print("Warming up...");
  delay(30000);
  
  lcd.clear();
  lcd.print("System Ready!");
  delay(1000);
  lcd.clear();
}

void loop() {
  // STEP 1: Wait for button press
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Scan face first");
  lcd.setCursor(0, 1);
  lcd.print("Press button");
  
  while (digitalRead(START_BUTTON_PIN) == HIGH) {
    delay(50);
  }
  
  // STEP 2: Request face scan
  lcd.clear();
  lcd.print("Sending request");
  lcd.setCursor(0, 1);
  lcd.print("to computer...");
  delay(500);
  
  Serial.println("FACE_SCAN_REQUEST");
  
  bool faceVerified = false;
  unsigned long startTime = millis();
  
  while (millis() - startTime < 10000) {
    if (Serial.available()) {
      char response = Serial.read();
      if (response == 'V') {
        faceVerified = true;
        break;
      }
    }
  }
  
  if (!faceVerified) {
    lcd.clear();
    lcd.print("Face NOT");
    lcd.setCursor(0, 1);
    lcd.print("recognized!");
    digitalWrite(RED_LED_PIN, HIGH);
    delay(2000);
    digitalWrite(RED_LED_PIN, LOW);
    lcd.clear();
    return;
  }
  
  // STEP 3: Face verified - Ask to blow
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Face Verified!");
  lcd.setCursor(0, 1);
  lcd.print("Press to blow");
  
  // Wait for button press to test alcohol
  while (digitalRead(START_BUTTON_PIN) == HIGH) {
    delay(50);
  }
  
  // STEP 4: Test alcohol
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Testing...");
  lcd.setCursor(0, 1);
  lcd.print("Blow into sensor");
  
  Serial.println("TESTING - BLOW NOW");
  
  delay(1000);  // Give time to blow
  
  int sensorValue = analogRead(ALCOHOL_SENSOR_PIN);
  
  // Calculate percentage - REVERSED LOGIC
  // Clean air = 1000+ = 0% alcohol
  // Alcohol = 50 = 100% alcohol
  int percentage;
  if (sensorValue >= 900) {
    percentage = 0;
  } else if (sensorValue <= 100) {
    percentage = 100;
  } else {
    // Map reversed: 900 to 100 becomes 0% to 100%
    percentage = map(sensorValue, 900, 100, 0, 100);
    if (percentage < 0) percentage = 0;
    if (percentage > 100) percentage = 100;
  }
  
  // Show reading on LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Raw: ");
  lcd.print(sensorValue);
  lcd.print("   ");
  lcd.setCursor(0, 1);
  lcd.print("Alcohol: ");
  lcd.print(percentage);
  lcd.print("%");
  
  Serial.print("Sensor: ");
  Serial.print(sensorValue);
  Serial.print(" | Alcohol: ");
  Serial.print(percentage);
  Serial.println("%");
  Serial.print("Threshold: ");
  Serial.println(ALCOHOL_THRESHOLD);
  
  delay(1500);
  
  // STEP 5: Show result with LED
  lcd.clear();
  
  // INVERTED LOGIC: If sensor value is BELOW threshold, alcohol detected
  if (sensorValue < ALCOHOL_THRESHOLD) {
    // ALCOHOL DETECTED - RED LED (NOT GRANTED)
    lcd.setCursor(0, 0);
    lcd.print("NOT GRANTED");
    lcd.setCursor(0, 1);
    lcd.print("Alcohol found!");
    digitalWrite(RED_LED_PIN, HIGH);
    digitalWrite(BLUE_LED_PIN, LOW);
    Serial.println("RESULT: NOT GRANTED - RED LED");
  } else {
    // NO ALCOHOL - BLUE LED (GRANTED)
    lcd.setCursor(0, 0);
    lcd.print("GRANTED");
    lcd.setCursor(0, 1);
    lcd.print("You are sober");
    digitalWrite(RED_LED_PIN, LOW);
    digitalWrite(BLUE_LED_PIN, HIGH);
    Serial.println("RESULT: GRANTED - BLUE LED");
  }
  
  delay(3000);
  
  // Turn off LEDs
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(BLUE_LED_PIN, LOW);
  
  lcd.clear();
}