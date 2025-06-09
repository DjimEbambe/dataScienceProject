#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

#define DHT_PIN 16               // Data pin for the DHT22 sensor
#define DHT_TYPE DHT22           // Sensor type DHT22
#define INTERVAL 300000        // 1800000 Interval of 30 minutes in milliseconds

const char* wifiSSIDs[] = {"ml", "NomDuReseau2", "bitia21"};
const char* wifiPasswords[] = {"Kinshasa", "MotDePasseReseau2", "123123123"};
const char* serverURL = "http://raspberrypi.local/data/";

String local = "LP-XP";


DHT dht(DHT_PIN, DHT_TYPE);
unsigned long previousMillis = 0;
void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  connectToWiFi();
  dht.begin();
}

void loop() {
  unsigned long currentMillis = millis();

  // Check Wi-Fi connection status
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  if (currentMillis - previousMillis >= INTERVAL) {
    previousMillis = currentMillis;
    sendSensorData();
  }
}

void sendSensorData() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Erreur lors de la lecture du capteur DHT !");
    return;
  }

  String data = "humidity=" + String(humidity) + "&temperature=" + String(temperature) + "&local=" +local;
  WiFiClient client;
  HTTPClient http;

  if (http.begin(client, serverURL)) {
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    int httpResponseCode = http.POST(data);

    if (httpResponseCode > 0) {
      Serial.print("Code de réponse HTTP : ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("Erreur lors de la requête HTTP : ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("Impossible de se connecter au serveur !");
  }
}

void connectToWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return; // Already connected
  }

  Serial.println("Tentative de connexion à WiFi...");
  for (int i = 0; i < sizeof(wifiSSIDs) / sizeof(wifiSSIDs[0]); i++) {
    WiFi.begin(wifiSSIDs[i], wifiPasswords[i]);
    if (waitForConnectResult() == WL_CONNECTED) {
      Serial.print("Connecté à ");
      Serial.println(wifiSSIDs[i]);
      return;
    }
  }
  Serial.println("Aucun réseau WiFi disponible. Tentative de reconnexion...");
}

uint8_t waitForConnectResult() {
  Serial.print("Connexion à WiFi");
  unsigned long startTime = millis();
  while (millis() - startTime < 10000) {  // Increased to 20 seconds
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println(" connecté!");
      return WL_CONNECTED;
    }
    delay(1000);
    Serial.print(".");
  }
  Serial.println(" échec!");
  return WiFi.status();
}
