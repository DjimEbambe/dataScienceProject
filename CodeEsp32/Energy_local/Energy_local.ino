#include <WiFi.h>
#include <HTTPClient.h>
#include <PZEM004Tv30.h>
#include <cmath> 

#define WIFI_SSID "ml"
#define WIFI_PASSWORD "Kinshasa"
const char* wifiSSIDs[] = {"ml", "Airtel 4G Router_2C32", "bitia21"};
const char* wifiPasswords[] = {"Kinshasa", "KxA4T736", "123123123"};

HardwareSerial hwSerial1(0);
PZEM004Tv30 pzem1(hwSerial1, 3, 1); // TX, RX


const char* serverURL = "http://raspberrypi.local/data/";
const int interval = 5 * 60 * 1000;  // Interval of 1 minute in milliseconds
String local = "LOGETTE";

unsigned long previousMillis = 0;

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  connectToWiFi();

  hwSerial1.begin(9600, SERIAL_8N1, 3, 1);

  pzem1.setAddress(1);

  sendData();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    sendData();
  }
}

void sendData() {

   // Retrieve data and replace NaN with zero
  float voltage = isnan(pzem1.voltage()) ? 0.0 : pzem1.voltage();
  float current = isnan(pzem1.current()) ? 0.0 : pzem1.current();
  float energy = isnan(pzem1.energy()) ? 0.0 : pzem1.energy();


  Serial.println("Sensor 1:");
  Serial.println("Voltage: " + String(voltage, 2) + " V");
  Serial.println("Current: " + String(current, 3) + " A");
  Serial.println("Energy: " + String(energy, 2) + " kWh");



  if (isnan(voltage) || isnan(current) || isnan(energy)) {
    Serial.println("Failed to read from PZEM004T sensors!");
    return;
  }

  String data = "voltage=" + String(voltage, 2) + "&current=" + String(current, 3) +
                "&power=0&energy=" + String(energy, 2) + "&local=" + local;

  if (sendDataToServer(serverURL, data)) {
    Serial.println("Data sent successfully.");
    Serial.println(data);
  } else {
    Serial.println("Failed to send data.");
    Serial.println(data);
  }
}

bool sendDataToServer(const char* server, const String& data) {
  WiFiClient client;
  HTTPClient http;
  bool success = false;

  if (http.begin(client, server)) {
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    int httpResponseCode = http.POST(data);
    if (httpResponseCode > 0) {
      Serial.print("HTTP Response Code: ");
      Serial.println(httpResponseCode);
      success = true;
    } else {
      Serial.print("HTTP Request failed, code: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("Unable to connect to the server!");
  }
  return success;
}

void connectToWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.println("Attempting to connect to WiFi...");
  for (int i = 0; i < sizeof(wifiSSIDs) / sizeof(wifiSSIDs[0]); i++) {
    WiFi.begin(wifiSSIDs[i], wifiPasswords[i]);
    if (waitForConnectResult() == WL_CONNECTED) {
      Serial.print("Connected to ");
      Serial.println(wifiSSIDs[i]);
      return;
    }
  }
  Serial.println("No WiFi network available. Retrying...");
}

uint8_t waitForConnectResult() {
  Serial.print("Connecting to WiFi");
  unsigned long startTime = millis();
  while (millis() - startTime < 10000) {
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println(" connected!");
      return WL_CONNECTED;
    }
    delay(1000);
    Serial.print(".");
  }
  Serial.println(" failed!");
  return WiFi.status();
}