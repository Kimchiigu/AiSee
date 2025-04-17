#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <WiFi.h>
#include <WebServer.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define I2C_SCL 22
#define I2C_SDA 21
#define LED_PIN 5

const char *ssid = ""; // Your wifi SSID (name)
const char *password = ""; // Your wifi password

Adafruit_SSD1306 oled(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
WebServer server(80);

String verificationStatus = "idle";  // idle, success, fail

void handleRoot() {
  if (server.hasArg("verify")) {
    verificationStatus = server.arg("verify");
    Serial.println("Received verification status: " + verificationStatus);
  }
  server.send(200, "text/plain", "Status received");
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  Wire.begin(I2C_SDA, I2C_SCL);

  if (!oled.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED init failed");
    while (1);
  }
  oled.clearDisplay();
  oled.display();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());

  server.on("/", HTTP_POST, handleRoot);
  server.begin();
}

void loop() {
  server.handleClient();

  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(WHITE);
  oled.setCursor(10, 10);

  if (verificationStatus == "success") {
    digitalWrite(LED_PIN, HIGH);
    oled.println("Verification");
    oled.setCursor(10, 25);
    oled.println("Successful");
    delay(500);
  } else if (verificationStatus == "fail") {
    digitalWrite(LED_PIN, LOW);
    oled.println("Verification");
    oled.setCursor(10, 25);
    oled.println("Failed");
    delay(500);
  } else {
    digitalWrite(LED_PIN, LOW);
    oled.println("Waiting for");
    oled.setCursor(10, 25);
    oled.println("Verification...");
  }

  verificationStatus = "idle";

  oled.display();
  delay(5000);
}