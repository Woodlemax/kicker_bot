#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
 
const char* ssid = "Nexign-pub";
const char* password = "Nexign-Systems1!";
const int keyPin = 14;
const int ledPin =  2;

WiFiServer server(80);

int keyState = 0;
int count = 0;
int oldstat = 0;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);      
  pinMode(keyPin, INPUT);     
  Serial.begin(115200);  
  
  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);  

  WiFi.begin(ssid, password);
 
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
 
  // Start the server
  server.begin();
  Serial.println("Server started");
 
  // Print the IP address
  Serial.print("Use this URL to connect: ");
  Serial.print("http://");
  Serial.print(WiFi.localIP());
  Serial.println("/");
}

void loop(){
  HTTPClient http;
  int httpCode;
  int kick_count = 0;
  Serial.println("Hi");
  do {
    String body = "ping value=1";
    Serial.println(body);
    http.begin("http://172.19.176.89:8086/write?db=kicker&u=kicker&p=4kicker_send");
    http.addHeader("Content-Type", "text/plain");
    httpCode = http.POST(body);
    Serial.println(httpCode);
      
    oldstat = digitalRead(keyPin);
    int flag_k = 0;
    int count_k = 0;
    while (count_k < 100) {
      keyState = digitalRead(keyPin); 
      if (keyState != oldstat) {     
        flag_k = 1;
        oldstat = keyState;
      }  
      ++count_k;
      delay(100);
    }
    if (flag_k == 0) {
      kick_count = 0;
    } else {
      kick_count++;
      body = "kick value=" + String(kick_count);
      Serial.println(body);
      http.begin("http://172.19.176.89:8086/write?db=kicker&u=kicker&p=4kicker_send");
      http.addHeader("Content-Type", "text/plain");
      httpCode = http.POST(body);
      Serial.println(httpCode);
    }
    Serial.print("Kick Count = ");
    Serial.println(kick_count);
  } while (kick_count >= 1);
}
