/**
 * wifi_client
 * 
 * This was written for the CS427 class at the University of Portland - Internet of Things.
 * The ESP32 has a built-in Wi-Fi module that is vital in creating an IoT device.
 * This project sets up a basis for connecting to a Wi-Fi network using the ESP32 and retrieving
 * data from a common webpage.
 */

// include libraries - WiFi.h
#include <WiFi.h>

// include the DHT library
#include <DHT.h>

// include servo library files
#include <ESP32Servo.h>

// define the DHT sensor
#define DHT_PIN 14
#define DHT_TYPE DHT11

// define the optical rain sensor (ORS) pin
#define ORS_PIN 32

// define the servo motor pin
#define SERVO_PIN 33

// create a DHT object to represent data from the sensor
DHT dht_sensor(DHT_PIN, DHT_TYPE);

// SSID - the Wi-Fi network's name
// Password - the Wi-Fi network's password
const char* ssid     = "UPIoT";
const char* password = "";

// host - the main URL of the webpage you want to connect to; you can use the IP address of a Flask app
const char host[] = "http://192.168.68.109:8080"; // change this to the private network IP listed when starting the Flask app
const byte flaskappip[4] = {192, 168, 68, 109}; // change these numbers as well, but put the IP address as four integers 

// port - the port of the flask app
const int port = 8080; // change this to the port the Flask app is running on; should be port 8080

// device information - to send to Flask App
const String name = "shileyrooftop"; // change this to make it easier to identify - ENSURE THIS IS UNIQUE
String macaddress = "";
String status = "";
float temp = 0.0;
float hum = 0.0;

// rain data - isRaining should match rainSensor; if it doesn't, a change in rain events occurred
int isRaining = 0;
int rainSensor = 0;

void setup() {
    // startup delay
    delay(3000);
  
    // initialize Serial communication
    Serial.begin(115200);
    
    // begin the Wi-Fi connection
    WiFi.begin(ssid, password);

    // device information for startup phase
    macaddress = WiFi.macAddress();
    status = "Starting+up...";

    // pending Wi-Fi connection...
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
    }

    // notify the Serial monitor when the Wi-Fi connection is a success
    // display the device's IP address
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    
    // Wi-Fi Client
    WiFiClient client;
    
    // connect to the client using the IP address and Port of the Flask App
    // set these values above - they can be found when running the Flask application
    if(client.connect(flaskappip, port)){
        // success message
        Serial.println("Connected!");

        // construct a URL to send setup data to Flask App
        String url = "/inputdata/misc/" + String(name) + "/" + String(macaddress) +
                        "/" + String(status) + "/" + String(temp) + "/" + String(hum);

        // send an HTTPS GET request
        client.print(String("GET ") + url + " HTTP/1.1\r\n" +
              "Host: " + host + "\r\n" +
              "Connection: close\r\n\r\n");

        // construct another URL for the rain data
        url = "/inputdata/rain/" + String(name) + "/" + String(isRaining);

        // send an HTTPS GET request
        client.print(String("GET ") + url + " HTTP/1.1\r\n" +
              "Host: " + host + "\r\n" +
              "Connection: close\r\n\r\n");
    }else{
        // failure message
        Serial.println("Failed to connect... (setup)");
    }

    // start the DHT sensory
    dht_sensor.begin();

    // initialize the timers and other servo configurations (from ESP32Servo.h)
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);
    servo.setPeriodHertz(50);
    servo.attach(SERVO_PIN);
    
    // initialize the pin for the optical rain sensor (ORS) as an input
    pinMode(ORS_PIN, INPUT);
}

void loop() {
    // status message
    status = "No+errors";

    // read temperature and humidity data
    // read humidity
    float humi  = dht_sensor.readHumidity();
    // read temperature in Celsius
    float tempC = dht_sensor.readTemperature();

    // check whether the reading is successful or not
    if( isnan(tempC) || isnan(humi) ){
        // if any of the data received is nan (failed), print error message
        Serial.println("Failed to read from DHT sensor!");
        status = "Error reading DHT11";
    }else{
        // if all of the data is successfully read, print to Serial monitor
        Serial.print("Humidity: ");
        Serial.print(humi);
        Serial.print("%");

        Serial.print("  |  ");

        Serial.print("Temperature: ");
        Serial.print(tempC);
        Serial.println("°C");
    }

    // set temperature and humidity data
    temp = tempC;
    hum = humi;
    
    // Wi-Fi Client
    WiFiClient client;
    
    // connect to the client using the IP address and Port of the Flask App
    // set these values above - they can be found when running the Flask application
    if(client.connect(flaskappip, port)){
        // success message
        Serial.println("Connected!");

        // construct a URL to send miscellaneous data to Flask App
        String url = "/inputdata/misc/" + String(name) + "/" + String(macaddress) +
                        "/" + String(status) + "/" + String(temp) + "/" + String(hum);

        // send an HTTPS GET request
        client.print(String("GET ") + url + " HTTP/1.1\r\n" +
               "Host: " + host + "\r\n" +
               "Connection: close\r\n\r\n");

        // construct another URL for the rain data
        url = "/inputdata/rain/" + String(name) + "/" + String(isRaining);

        // send an HTTPS GET request
        client.print(String("GET ") + url + " HTTP/1.1\r\n" +
              "Host: " + host + "\r\n" +
              "Connection: close\r\n\r\n");
    }else{
        // failure message
        Serial.println("Failed to connect... (misc)");
    }

    // timeout loop
    unsigned long timeout = millis();
    while (client.available() == 0) {
        // if 5 seconds pass, stop the client due to timeout issue
        if (millis() - timeout > 5000) {
            Serial.println(">>> Client Timeout !");
            client.stop();
            return;
        }
    }

    // while the client is available, print out the returned data
    while (client.available()) {
        String line = client.readStringUntil('\r');
        Serial.print(line);
    }

    // delay for a minute
    // in the meantime, if a change in the rain sensor's value occurs, send another HTTP request
    unsigned long misc_delay = millis();
    while (millis() - misc_delay < 60000){
        // read the rain sensor value - HIGH is when it's raining
        rainSensor = digitalRead(ORS_PIN);

        // detect a change in precipitation events
        if(isRaining != rainSensor){
            // when a rain event change occurs, turn the servo motor
            // if rain sensor is not reading rain and rainSensor is 0, degree should be 0
            // if rain sensor is reading rain and rainSensor is 1, degree should be 180
            // due to the servo motor's control interface, the range of values a servo can
            // change is between 0 and 180. However, due to the gear ratios in the servo
            // itself, it's actual range of motion is 0 to 270 degrees.
            servo.write(180 * rainSensor);

            // update the isRaining value with the rain sensor's value
            isRaining = rainSensor;

            // connect to the client using the IP address and Port of the Flask App
            // set these values above - they can be found when running the Flask application
            if(client.connect(flaskappip, port)){
                // success message
                Serial.println("Connected!");

                // construct a URL to send miscellaneous data to Flask App
                String url = "/inputdata/rain/" + String(name) + "/" + String(isRaining);

                // send an HTTPS GET request
                client.print(String("GET ") + url + " HTTP/1.1\r\n" +
                    "Host: " + host + "\r\n" +
                    "Connection: close\r\n\r\n");
            }else{
                // failure message
                Serial.println("Failed to connect... (rain)");
            }
        }

        delay(1000);
    }
}