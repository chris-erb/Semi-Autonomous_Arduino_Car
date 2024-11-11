#include <Arduino.h>

#define PIN_Motor_PWMA 5
#define PIN_Motor_PWMB 6
#define PIN_Motor_BIN_1 8
#define PIN_Motor_AIN_1 7
#define PIN_Motor_STBY 3

// Define pins for line tracking sensors
#define PIN_Left_Sensor A0
#define PIN_Middle_Sensor A1
#define PIN_Right_Sensor A2

bool isAutonomousMode = false; // Flag to track autonomous mode status

void setup() {
    Serial.begin(115200); // Start serial communication
    pinMode(PIN_Motor_PWMA, OUTPUT);
    pinMode(PIN_Motor_PWMB, OUTPUT);
    pinMode(PIN_Motor_AIN_1, OUTPUT);
    pinMode(PIN_Motor_BIN_1, OUTPUT);
    pinMode(PIN_Motor_STBY, OUTPUT);
    pinMode(PIN_Left_Sensor, INPUT);
    pinMode(PIN_Middle_Sensor, INPUT);
    pinMode(PIN_Right_Sensor, INPUT);
    digitalWrite(PIN_Motor_STBY, LOW); // Initially keep motors off
}

void loop() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n'); // Read until newline
        command.trim(); // Trim whitespace
        
        if (command == "FORWARD") {
            moveForward();
        } else if (command == "BACKWARD") {
            moveBackward();
        } else if (command == "LEFT") {
            turnLeft();
        } else if (command == "RIGHT") {
            turnRight();
        } else if (command == "STOP") {
            stopMotors();
            isAutonomousMode = false;
        } else if (command == "AUTONOMOUS") {
            autonomousMode(); // Enter line tracking mode
        }
    }
}

void moveForward() {
    digitalWrite(PIN_Motor_STBY, HIGH);
    digitalWrite(PIN_Motor_AIN_1, HIGH);
    analogWrite(PIN_Motor_PWMA, 125); // 255 is full speed
    digitalWrite(PIN_Motor_BIN_1, HIGH);
    analogWrite(PIN_Motor_PWMB, 125);
}

void moveBackward() {
    digitalWrite(PIN_Motor_STBY, HIGH);
    digitalWrite(PIN_Motor_AIN_1, LOW);
    analogWrite(PIN_Motor_PWMA, 125);
    digitalWrite(PIN_Motor_BIN_1, LOW);
    analogWrite(PIN_Motor_PWMB, 125); 
}

void turnLeft() {
    digitalWrite(PIN_Motor_STBY, HIGH);
    digitalWrite(PIN_Motor_AIN_1, LOW);
    analogWrite(PIN_Motor_PWMA, 0);
    digitalWrite(PIN_Motor_BIN_1, HIGH);
    analogWrite(PIN_Motor_PWMB, 125); 
}

void turnRight() {
    digitalWrite(PIN_Motor_STBY, HIGH);
    digitalWrite(PIN_Motor_AIN_1, HIGH);
    analogWrite(PIN_Motor_PWMA, 125); 
    digitalWrite(PIN_Motor_BIN_1, LOW);
    analogWrite(PIN_Motor_PWMB, 0);
}

void stopMotors() {
    digitalWrite(PIN_Motor_STBY, LOW); // Disable motors
}

void autonomousMode() {
    isAutonomousMode = true; // Set the flag for autonomous mode
    while (isAutonomousMode) { // Run indefinitely until stopped
        int leftSensor = digitalRead(PIN_Left_Sensor);
        int middleSensor = digitalRead(PIN_Middle_Sensor);
        int rightSensor = digitalRead(PIN_Right_Sensor);

        if (middleSensor == HIGH) { // On the line
            moveForward();
        } else if (leftSensor == HIGH) { // Turn right
            turnRight();
        } else if (rightSensor == HIGH) { // Turn left
            turnLeft();
        } else { // Stop if off the line
            stopMotors();
        }

        delay(100); // Small delay to stabilize sensor reading

        // Check for stop command
        if (Serial.available()) {
            String command = Serial.readStringUntil('\n'); // Read until newline
            command.trim(); // Trim whitespace
            
            if (command == "STOP") {
                stopMotors(); // Stop the motors
                isAutonomousMode = false; // Exit autonomous mode
            }
        }
    }
}