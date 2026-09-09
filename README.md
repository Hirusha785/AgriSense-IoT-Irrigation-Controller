# 🌱💧 AgriSense IoT Smart Irrigation Monitoring & Control System

![Arduino](https://img.shields.io/badge/Arduino-UNO-00979D?style=for-the-badge&logo=arduino)
![Proteus](https://img.shields.io/badge/Simulation-Proteus-blue?style=for-the-badge)
![IoT](https://img.shields.io/badge/Technology-IoT-orange?style=for-the-badge)
![Web Dashboard](https://img.shields.io/badge/Dashboard-Web%20Application-purple?style=for-the-badge)

---

## 🌿 Project Overview

**AgriSense IoT Smart Irrigation Monitoring & Control System** is an intelligent agriculture automation solution designed to monitor plant environmental conditions and automatically control irrigation and cooling systems.

The system combines:

🌱 Embedded hardware simulation  
🤖 Arduino-based control logic  
🌡️ Environmental monitoring  
💧 Automated irrigation management  
📡 IoT communication architecture  
🖥️ Real-time web dashboard visualization  

The project is developed using **Proteus Simulation** with Arduino UNO and includes a modern smart agriculture dashboard for monitoring system conditions.

---

# ✨ Key Features

## 🌱 Smart Irrigation Automation

The system monitors soil moisture conditions and automatically controls the water pump.

Features:

✅ Real-time soil moisture monitoring  
✅ Automatic watering decision  
✅ Dry soil detection  
✅ Pump ON/OFF control  
✅ Prevention of overwatering  


---

## 🌡️ Environmental Monitoring

The system continuously monitors:

🌡️ Temperature  
💧 Air Humidity  
🌱 Soil Moisture  


Sensor values are displayed through:

- LCD Display 📟
- Virtual Terminal 🖥️
- Web Dashboard 📊


---

# 🤖 Operating Modes

## 🔄 Automatic Mode

The system automatically controls actuators according to sensor readings.


### 💧 Water Pump Logic


Soil Moisture <= 35%

    ↓

  DRY SOIL

    ↓

Water Pump ON 💧



Soil Moisture > 35%

    ↓

MOIST / WET SOIL

    ↓

Water Pump OFF 🛑


---

### ❄️ Cooling Fan Logic



Temperature >= 35°C

    ↓

 Fan ON ❄️



Temperature < 35°C

    ↓

 Fan OFF

---

# 🎮 Manual Control Mode

The system supports manual user control.

Users can independently control:

💧 Water Pump  
❄️ Cooling Fan  


Manual controls are available through:

- Physical push buttons
- Web dashboard interface


---

# 🖥️ Smart Agriculture Web Dashboard

The project includes a modern real-time monitoring dashboard designed for smart farming applications.

Dashboard capabilities:

## 📊 Live Monitoring

Displays:

🌡️ Temperature

💧 Air Humidity

🌱 Soil Moisture


Example:


Temperature : 33.5 °C

Humidity : 79 %

Soil Moisture : 49 %



---

## 📈 Real-Time Data Visualization

The dashboard provides:

📊 Live sensor graphs

📉 Historical variations

⏱️ Time-based monitoring


Displayed parameters:

- Temperature variation
- Humidity variation
- Soil moisture variation


---

## ⚙️ System Control Panel

The dashboard displays actuator status:

### 💧 Water Pump

Shows:

- Current state
- Automatic trigger condition
- ON/OFF status


Example:


Water Pump

Turns ON when soil <= 35%



---

### ❄️ Cooling Fan

Shows:

- Cooling system activity
- Current ON/OFF state
- Temperature-based activation


Example:


Cooling Fan

ACTIVE - Cooling system



---

# 🏗️ System Architecture


             🌡️ Sensors
                |
                |
                ↓

          🤖 Arduino UNO

                |
    ----------------------------

    |            |             |

    ↓            ↓             ↓

 📟 LCD      ⚙️ L293D      📡 ESP8266

                |

    --------------------

    |                  |

    ↓                  ↓

 💧 Pump          ❄️ Fan


                |

                ↓

        🖥️ Web Dashboard

---

# 🔧 Hardware Components

| Component | Purpose |
|-----------|---------|
| 🤖 Arduino UNO | Main processing controller |
| 🌡️ DHT11 | Temperature and humidity sensing |
| 🌱 Soil Moisture Sensor / Potentiometer | Soil condition simulation |
| ⚙️ L293D | Motor driver |
| 💧 DC Motor | Water pump simulation |
| ❄️ DC Motor | Cooling fan simulation |
| 📟 LCD 16x2 | Local display |
| 📡 ESP8266 | IoT communication module |
| 🔘 Push Buttons | Manual control |

---

# 📌 Arduino Pin Configuration

| Component | Arduino Pin |
|-----------|-------------|
| DHT11 Data | A0 |
| Auto/Manual Button | A1 |
| Manual Pump Button | A2 |
| Soil Moisture Input | A3 |
| Manual Fan Button | A4 |
| ESP8266 TX | D2 |
| ESP8266 RX | D3 |
| Fan Driver | D4, D5 |
| Pump Driver | D6, D7 |
| LCD Display | D8-D13 |

---

# 🖥️ Simulation Environment

## Proteus Simulation

Used for:

✅ Circuit design  
✅ Arduino simulation  
✅ Sensor testing  
✅ Motor control validation  
✅ Embedded system verification  


## Arduino IDE

Used for:

✅ Microcontroller programming  
✅ Firmware development  
✅ Embedded logic implementation  


---

# 📊 Virtual Terminal Monitoring

The system provides detailed runtime information:



================================

Time (GMT): 00:00:10

Temperature : 31.0 C

Humidity : 89 %

Soil RAW : 717

Soil Voltage: 3.50 V

Soil Moisture: 70 %

Soil Status : MOIST

Water Pump : OFF

Cooling Fan : OFF

Mode : AUTO

================================


---

# 🚀 Future Improvements

Future hardware deployment can include:


📡 Real ESP8266/ESP32 communication

☁️ Cloud IoT platform integration

📱 Mobile application

🌦️ Weather API integration

💧 Water level monitoring

🔔 Smart notifications

🤖 AI-based irrigation prediction

🔋 Solar-powered irrigation system


---

# 🌾 Applications

Suitable for:

🌱 Smart agriculture

🏡 Home gardening

🏭 Greenhouses

🌿 Plant monitoring systems

🚜 Precision farming


---

# 👨‍💻 Author

**FERNANDO S.M.H.G.**


---

# 📜 License

This project is developed for educational and research purposes.

Feel free to explore, modify and improve the system. 🌱🚀
