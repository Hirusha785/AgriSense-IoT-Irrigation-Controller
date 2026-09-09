/*
============================================================
 IOT IRRIGATION MONITORING & CONTROLLER SYSTEM
 FINAL AUTO + MANUAL VERSION
============================================================

ARDUINO UNO

DHT11 DATA             -> A0

MODE BUTTON            -> A1
MANUAL PUMP BUTTON     -> A2
SOIL POTENTIOMETER     -> A3
MANUAL FAN BUTTON      -> A4

ESP8266 TX             -> D2
ESP8266 RX             -> D3

L293D:
Pump IN1               -> D7
Pump IN2               -> D6

Fan IN1                -> D5
Fan IN2                -> D4

LCD:
RS                     -> D13
EN                     -> D12
D4                     -> D11
D5                     -> D10
D6                     -> D9
D7                     -> D8


============================================================
 AUTOMATIC MODE
============================================================

Soil <= 35%
    -> DRY
    -> PUMP ON

Soil > 35%
    -> PUMP OFF


Temperature >= 35 C
    -> FAN ON

Temperature < 35 C
    -> FAN OFF


============================================================
 MANUAL MODE
============================================================

A2 button:
Press once -> Pump ON
Press again -> Pump OFF

A4 button:
Press once -> Fan ON
Press again -> Fan OFF


============================================================
 VIRTUAL TERMINAL
============================================================

Status printed every 10 seconds.

Sensor/control check every 1 second.

GMT displayed as simulated runtime:
00:00:00 -> starts when Proteus starts.

============================================================
*/


#include <LiquidCrystal.h>
#include <DHT.h>
#include <SoftwareSerial.h>


// ==========================================================
// DHT11
// ==========================================================

#define DHT_PIN A0
#define DHT_TYPE DHT11

DHT dht(DHT_PIN, DHT_TYPE);


// ==========================================================
// BUTTONS
// ==========================================================

// Existing AUTO / MANUAL mode button
#define MODE_BUTTON_PIN A1

// New buttons
#define PUMP_BUTTON_PIN A2
#define FAN_BUTTON_PIN  A4


// ==========================================================
// SOIL POTENTIOMETER
// ==========================================================

// RV1 wiper -> Arduino A3

#define SOIL_PIN A3

#define SOIL_DRY_LIMIT 35


// ==========================================================
// ESP8266
// ==========================================================

// ESP TXD -> Arduino D2
// Arduino D3 -> ESP RXD

SoftwareSerial ESP8266(2, 3);


// ==========================================================
// L293D
// ==========================================================

// TOP MOTOR = WATER PUMP

#define PUMP_IN1 7
#define PUMP_IN2 6


// BOTTOM MOTOR = COOLING FAN

#define FAN_IN1 5
#define FAN_IN2 4


// ==========================================================
// LCD
// ==========================================================

// RS, EN, D4, D5, D6, D7

LiquidCrystal lcd(
  13,
  12,
  11,
  10,
  9,
  8
);


// ==========================================================
// CONTROL SETTINGS
// ==========================================================

#define FAN_TEMP_LIMIT 35.0


// ==========================================================
// TIMING
// ==========================================================

// Sensors + automatic control every 1 second

const unsigned long SENSOR_INTERVAL = 1000;


// Virtual Terminal every 10 seconds

const unsigned long TERMINAL_INTERVAL = 10000;


// LCD changes page every 2 seconds

const unsigned long LCD_INTERVAL = 2000;


// ==========================================================
// SYSTEM STATES
// ==========================================================

bool automaticMode = true;

bool pumpState = false;

bool fanState = false;


// ==========================================================
// BUTTON STATES
// ==========================================================

bool lastModeButtonState = HIGH;

bool lastPumpButtonState = HIGH;

bool lastFanButtonState = HIGH;


// ==========================================================
// SENSOR DATA
// ==========================================================

float temperature = 0.0;

float humidity = 0.0;

bool dhtOK = false;


int soilRaw = 0;

float soilVoltage = 0.0;

int soilPercent = 0;


// ==========================================================
// TIMERS
// ==========================================================

unsigned long lastSensorRead = 0;

unsigned long lastTerminalPrint = 0;

unsigned long lastLCDUpdate = 0;


byte lcdPage = 0;


// ==========================================================
// SETUP
// ==========================================================

void setup()
{

  // ========================================================
  // VIRTUAL TERMINAL
  // ========================================================

  Serial.begin(9600);


  // ========================================================
  // ESP8266
  // ========================================================

  ESP8266.begin(9600);


  // ========================================================
  // DHT11
  // ========================================================

  dht.begin();


  // ========================================================
  // SOIL
  // ========================================================

  pinMode(
    SOIL_PIN,
    INPUT
  );


  // ========================================================
  // MODE BUTTON
  // ========================================================

  /*
     Existing circuit:

     A1 ---- button ---- GND

     with external pull-up resistor.

     Released = HIGH
     Pressed  = LOW
  */

  pinMode(
    MODE_BUTTON_PIN,
    INPUT
  );


  // ========================================================
  // MANUAL CONTROL BUTTONS
  // ========================================================

  /*
     Simply connect:

     A2 ---- button ---- GND
     A4 ---- button ---- GND

     Internal pull-up is used.
  */

  pinMode(
    PUMP_BUTTON_PIN,
    INPUT_PULLUP
  );


  pinMode(
    FAN_BUTTON_PIN,
    INPUT_PULLUP
  );


  // ========================================================
  // PUMP
  // ========================================================

  pinMode(
    PUMP_IN1,
    OUTPUT
  );


  pinMode(
    PUMP_IN2,
    OUTPUT
  );


  // ========================================================
  // FAN
  // ========================================================

  pinMode(
    FAN_IN1,
    OUTPUT
  );


  pinMode(
    FAN_IN2,
    OUTPUT
  );


  // ========================================================
  // SAFE START
  // ========================================================

  pumpOFF();

  fanOFF();


  // ========================================================
  // LCD
  // ========================================================

  lcd.begin(
    16,
    2
  );


  lcd.clear();


  lcd.setCursor(
    0,
    0
  );

  lcd.print(
    "IoT Irrigation"
  );


  lcd.setCursor(
    0,
    1
  );

  lcd.print(
    "Starting..."
  );


  // ========================================================
  // TERMINAL STARTUP
  // ========================================================

  Serial.println();

  Serial.println(
    "========================================"
  );

  Serial.println(
    " IOT IRRIGATION MONITORING SYSTEM"
  );

  Serial.println(
    "========================================"
  );

  Serial.println(
    "AUTO + MANUAL CONTROL ENABLED"
  );

  Serial.println(
    "Terminal Update : 10 Seconds"
  );

  Serial.println(
    "Time Format     : GMT HH:MM:SS"
  );

  Serial.println(
    "========================================"
  );


  delay(1500);


  lcd.clear();


  // ========================================================
  // INITIAL SENSOR READING
  // ========================================================

  readSensors();


  // Apply AUTO logic immediately

  controlAutomatic();


  // Print initial status

  printSystemData();

}


// ==========================================================
// MAIN LOOP
// ==========================================================

void loop()
{

  unsigned long currentMillis =
    millis();


  // ========================================================
  // MODE BUTTON
  // ========================================================

  checkModeButton();


  // ========================================================
  // MANUAL BUTTONS
  // ========================================================

  if (!automaticMode)
  {

    checkManualPumpButton();

    checkManualFanButton();

  }


  // ========================================================
  // SENSOR READING
  // EVERY 1 SECOND
  // ========================================================

  if (
    currentMillis - lastSensorRead
    >= SENSOR_INTERVAL
  )
  {

    lastSensorRead =
      currentMillis;


    readSensors();


    // Automatic output control only in AUTO mode

    if (automaticMode)
    {

      controlAutomatic();

    }

  }


  // ========================================================
  // LCD
  // EVERY 2 SECONDS
  // ========================================================

  if (
    currentMillis - lastLCDUpdate
    >= LCD_INTERVAL
  )
  {

    lastLCDUpdate =
      currentMillis;


    updateLCD();

  }


  // ========================================================
  // VIRTUAL TERMINAL
  // EVERY 10 SECONDS
  // ========================================================

  if (
    currentMillis - lastTerminalPrint
    >= TERMINAL_INTERVAL
  )
  {

    lastTerminalPrint =
      currentMillis;


    printSystemData();

  }


  // ========================================================
  // ESP8266 RESPONSE
  // ========================================================

  while (
    ESP8266.available()
  )
  {

    Serial.write(
      ESP8266.read()
    );

  }

}


// ==========================================================
// READ SENSORS
// ==========================================================

void readSensors()
{

  // ========================================================
  // DHT11
  // ========================================================

  float tempRead =
    dht.readTemperature();


  float humidityRead =
    dht.readHumidity();


  if (
    isnan(tempRead) ||
    isnan(humidityRead)
  )
  {

    dhtOK = false;

  }

  else
  {

    dhtOK = true;


    temperature =
      tempRead;


    humidity =
      humidityRead;

  }


  // ========================================================
  // SOIL POTENTIOMETER
  // ========================================================

  soilRaw =
    analogRead(
      SOIL_PIN
    );


  // Convert ADC to voltage

  soilVoltage =
    soilRaw *
    (5.0 / 1023.0);


  // Convert ADC to percentage

  soilPercent =
    map(
      soilRaw,
      0,
      1023,
      0,
      100
    );


  soilPercent =
    constrain(
      soilPercent,
      0,
      100
    );

}


// ==========================================================
// AUTOMATIC CONTROL
// ==========================================================

void controlAutomatic()
{

  // ========================================================
  // AUTOMATIC PUMP
  // ========================================================

  if (
    soilPercent <=
    SOIL_DRY_LIMIT
  )
  {

    pumpON();

  }

  else
  {

    pumpOFF();

  }


  // ========================================================
  // AUTOMATIC FAN
  // ========================================================

  if (dhtOK)
  {

    if (
      temperature >=
      FAN_TEMP_LIMIT
    )
    {

      fanON();

    }

    else
    {

      fanOFF();

    }

  }

  else
  {

    fanOFF();

  }

}


// ==========================================================
// PUMP ON
// ==========================================================

void pumpON()
{

  digitalWrite(
    PUMP_IN1,
    HIGH
  );


  digitalWrite(
    PUMP_IN2,
    LOW
  );


  pumpState = true;

}


// ==========================================================
// PUMP OFF
// ==========================================================

void pumpOFF()
{

  digitalWrite(
    PUMP_IN1,
    LOW
  );


  digitalWrite(
    PUMP_IN2,
    LOW
  );


  pumpState = false;

}


// ==========================================================
// FAN ON
// ==========================================================

void fanON()
{

  digitalWrite(
    FAN_IN1,
    HIGH
  );


  digitalWrite(
    FAN_IN2,
    LOW
  );


  fanState = true;

}


// ==========================================================
// FAN OFF
// ==========================================================

void fanOFF()
{

  digitalWrite(
    FAN_IN1,
    LOW
  );


  digitalWrite(
    FAN_IN2,
    LOW
  );


  fanState = false;

}


// ==========================================================
// MODE BUTTON
// ==========================================================

void checkModeButton()
{

  bool currentState =
    digitalRead(
      MODE_BUTTON_PIN
    );


  // Detect new press

  if (
    currentState == LOW &&
    lastModeButtonState == HIGH
  )
  {

    delay(40);


    if (
      digitalRead(
        MODE_BUTTON_PIN
      ) == LOW
    )
    {

      automaticMode =
        !automaticMode;


      // ====================================================
      // AUTO MODE
      // ====================================================

      if (automaticMode)
      {

        Serial.println();

        Serial.println(
          ">>> MODE CHANGED TO AUTOMATIC"
        );


        // Sensors immediately take control

        readSensors();

        controlAutomatic();

      }


      // ====================================================
      // MANUAL MODE
      // ====================================================

      else
      {

        Serial.println();

        Serial.println(
          ">>> MODE CHANGED TO MANUAL"
        );


        // Safe starting condition

        pumpOFF();

        fanOFF();

      }

    }

  }


  lastModeButtonState =
    currentState;

}


// ==========================================================
// MANUAL PUMP BUTTON
// ==========================================================

void checkManualPumpButton()
{

  bool currentState =
    digitalRead(
      PUMP_BUTTON_PIN
    );


  if (
    currentState == LOW &&
    lastPumpButtonState == HIGH
  )
  {

    delay(40);


    if (
      digitalRead(
        PUMP_BUTTON_PIN
      ) == LOW
    )
    {

      // Toggle pump

      if (pumpState)
      {

        pumpOFF();


        Serial.println(
          ">>> MANUAL PUMP -> OFF"
        );

      }

      else
      {

        pumpON();


        Serial.println(
          ">>> MANUAL PUMP -> ON"
        );

      }

    }

  }


  lastPumpButtonState =
    currentState;

}


// ==========================================================
// MANUAL FAN BUTTON
// ==========================================================

void checkManualFanButton()
{

  bool currentState =
    digitalRead(
      FAN_BUTTON_PIN
    );


  if (
    currentState == LOW &&
    lastFanButtonState == HIGH
  )
  {

    delay(40);


    if (
      digitalRead(
        FAN_BUTTON_PIN
      ) == LOW
    )
    {

      // Toggle fan

      if (fanState)
      {

        fanOFF();


        Serial.println(
          ">>> MANUAL FAN -> OFF"
        );

      }

      else
      {

        fanON();


        Serial.println(
          ">>> MANUAL FAN -> ON"
        );

      }

    }

  }


  lastFanButtonState =
    currentState;

}


// ==========================================================
// PRINT GMT TIME
// ==========================================================

void printGMTTime()
{

  /*
     Simulated GMT time.

     Starts from:

     00:00:00 GMT

     when Proteus simulation starts.
  */


  unsigned long totalSeconds =
    millis() / 1000;


  unsigned int hours =
    (totalSeconds / 3600) % 24;


  unsigned int minutes =
    (totalSeconds / 60) % 60;


  unsigned int seconds =
    totalSeconds % 60;


  Serial.print(
    "Time (GMT)      : "
  );


  // HOURS

  if (hours < 10)
  {

    Serial.print("0");

  }


  Serial.print(hours);


  Serial.print(":");


  // MINUTES

  if (minutes < 10)
  {

    Serial.print("0");

  }


  Serial.print(minutes);


  Serial.print(":");


  // SECONDS

  if (seconds < 10)
  {

    Serial.print("0");

  }


  Serial.println(seconds);

}


// ==========================================================
// VIRTUAL TERMINAL OUTPUT
// ==========================================================

void printSystemData()
{

  Serial.println();

  Serial.println(
    "========================================"
  );


  // ========================================================
  // GMT TIME
  // ========================================================

  printGMTTime();


  Serial.println(
    "----------------------------------------"
  );


  // ========================================================
  // TEMPERATURE / HUMIDITY
  // ========================================================

  if (dhtOK)
  {

    Serial.print(
      "Temperature     : "
    );


    Serial.print(
      temperature,
      1
    );


    Serial.println(
      " C"
    );


    Serial.print(
      "Humidity        : "
    );


    Serial.print(
      humidity,
      1
    );


    Serial.println(
      " %"
    );

  }

  else
  {

    Serial.println(
      "Temperature     : ERROR"
    );


    Serial.println(
      "Humidity        : ERROR"
    );

  }


  // ========================================================
  // SOIL RAW
  // ========================================================

  Serial.print(
    "Soil RAW        : "
  );


  Serial.println(
    soilRaw
  );


  // ========================================================
  // SOIL VOLTAGE
  // ========================================================

  Serial.print(
    "Soil Voltage    : "
  );


  Serial.print(
    soilVoltage,
    2
  );


  Serial.println(
    " V"
  );


  // ========================================================
  // SOIL MOISTURE %
  // ========================================================

  Serial.print(
    "Soil Moisture   : "
  );


  Serial.print(
    soilPercent
  );


  Serial.println(
    " %"
  );


  // ========================================================
  // SOIL STATUS
  // ========================================================

  Serial.print(
    "Soil Status     : "
  );


  if (
    soilPercent <= 35
  )
  {

    Serial.println(
      "DRY"
    );

  }

  else if (
    soilPercent <= 70
  )
  {

    Serial.println(
      "MOIST"
    );

  }

  else
  {

    Serial.println(
      "WET"
    );

  }


  // ========================================================
  // PUMP
  // ========================================================

  Serial.print(
    "Water Pump      : "
  );


  if (pumpState)
  {

    Serial.println(
      "ON"
    );

  }

  else
  {

    Serial.println(
      "OFF"
    );

  }


  // ========================================================
  // FAN
  // ========================================================

  Serial.print(
    "Cooling Fan     : "
  );


  if (fanState)
  {

    Serial.println(
      "ON"
    );

  }

  else
  {

    Serial.println(
      "OFF"
    );

  }


  // ========================================================
  // MODE
  // ========================================================

  Serial.print(
    "Mode            : "
  );


  if (automaticMode)
  {

    Serial.println(
      "AUTO"
    );

  }

  else
  {

    Serial.println(
      "MANUAL"
    );

  }


  // ========================================================
  // CONTROL INFORMATION
  // ========================================================

  Serial.println(
    "----------------------------------------"
  );


  if (automaticMode)
  {

    Serial.println(
      "AUTO CONTROL:"
    );


    Serial.println(
      "Soil <= 35% -> PUMP ON"
    );


    Serial.println(
      "Soil >  35% -> PUMP OFF"
    );


    Serial.println(
      "Temp >=35C  -> FAN ON"
    );


    Serial.println(
      "Temp < 35C  -> FAN OFF"
    );

  }

  else
  {

    Serial.println(
      "MANUAL CONTROL:"
    );


    Serial.println(
      "A2 Button -> Toggle Pump"
    );


    Serial.println(
      "A4 Button -> Toggle Fan"
    );

  }


  Serial.println(
    "========================================"
  );

}


// ==========================================================
// LCD
// ==========================================================

void updateLCD()
{

  lcd.clear();


  // ========================================================
  // PAGE 1
  // TEMPERATURE
  // ========================================================

  if (
    lcdPage == 0
  )
  {

    lcd.setCursor(
      0,
      0
    );


    if (dhtOK)
    {

      lcd.print(
        "T:"
      );


      lcd.print(
        temperature,
        1
      );


      lcd.print(
        (char)223
      );


      lcd.print(
        "C"
      );

    }

    else
    {

      lcd.print(
        "DHT ERROR"
      );

    }


    lcd.setCursor(
      0,
      1
    );


    if (dhtOK)
    {

      lcd.print(
        "Humidity:"
      );


      lcd.print(
        humidity,
        0
      );


      lcd.print(
        "%"
      );

    }

  }


  // ========================================================
  // PAGE 2
  // SOIL
  // ========================================================

  else if (
    lcdPage == 1
  )
  {

    lcd.setCursor(
      0,
      0
    );


    lcd.print(
      "Soil:"
    );


    lcd.print(
      soilPercent
    );


    lcd.print(
      "%"
    );


    lcd.setCursor(
      0,
      1
    );


    if (
      soilPercent <= 35
    )
    {

      lcd.print(
        "Status: DRY"
      );

    }

    else if (
      soilPercent <= 70
    )
    {

      lcd.print(
        "Status: MOIST"
      );

    }

    else
    {

      lcd.print(
        "Status: WET"
      );

    }

  }


  // ========================================================
  // PAGE 3
  // PUMP + FAN
  // ========================================================

  else if (
    lcdPage == 2
  )
  {

    lcd.setCursor(
      0,
      0
    );


    lcd.print(
      "Pump:"
    );


    if (pumpState)
    {

      lcd.print(
        "ON"
      );

    }

    else
    {

      lcd.print(
        "OFF"
      );

    }


    lcd.setCursor(
      0,
      1
    );


    lcd.print(
      "Fan:"
    );


    if (fanState)
    {

      lcd.print(
        "ON"
      );

    }

    else
    {

      lcd.print(
        "OFF"
      );

    }

  }


  // ========================================================
  // PAGE 4
  // MODE
  // ========================================================

  else
  {

    lcd.setCursor(
      0,
      0
    );


    lcd.print(
      "System Mode"
    );


    lcd.setCursor(
      0,
      1
    );


    if (automaticMode)
    {

      lcd.print(
        "AUTOMATIC"
      );

    }

    else
    {

      lcd.print(
        "MANUAL"
      );

    }

  }


  // ========================================================
  // NEXT LCD PAGE
  // ========================================================

  lcdPage++;


  if (
    lcdPage > 3
  )
  {

    lcdPage = 0;

  }

}