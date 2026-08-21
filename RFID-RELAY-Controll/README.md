Use the **MFRC522 RFID reader + Arduino Nano + 5V 1-channel relay module** like this:

### 1. RFID → Arduino Nano

| RFID RC522 Pin | Arduino Nano Pin  |
| -------------- | ----------------- |
| **SDA / SS**   | **D10**           |
| **SCK**        | **D13**           |
| **MOSI**       | **D11**           |
| **MISO**       | **D12**           |
| **RST**        | **D9**            |
| **3.3V**       | **3.3V**          |
| **GND**        | **GND**           |
| **IRQ**        | **Not connected** |

### 2. Relay Module → Arduino Nano

| Relay Module Pin | Arduino Nano |
| ---------------- | ------------ |
| **VCC**          | **5V**       |
| **GND**          | **GND**      |
| **IN**           | **D7**       |

### 3. Complete connection

```text
                    ARDUINO NANO
                 +----------------+
                 |                |
       3.3V -----| 3V3            |
       GND ------| GND            |
                 |                |
RC522 SDA -------| D10            |
RC522 SCK -------| D13            |
RC522 MOSI ------| D11            |
RC522 MISO ------| D12            |
RC522 RST -------| D9             |
                 |                |
Relay IN --------| D7             |
Relay GND -------| GND            |
Relay VCC -------| 5V             |
                 +----------------+

       MFRC522                    RELAY
    +----------+              +-----------+
    | 3.3V ----|--------------|           |
    | GND -----|--------------| GND       |
    | SDA -----|---- D10      | IN -------| D7
    | SCK -----|---- D13      | VCC ------| 5V
    | MOSI ----|---- D11      +-----------+
    | MISO ----|---- D12
    | RST -----|---- D9
    +----------+
```

### Relay load connection

Since you want the relay to **default OFF**, use **COM + NO**:

| Relay Terminal | Connect to                     |
| -------------- | ------------------------------ |
| **COM**        | Positive supply for your load  |
| **NO**         | Positive terminal of your load |
| **NC**         | Leave disconnected             |

```text
Power Supply (+)
       |
       v
     COM
   [ RELAY ]
     NO
       |
       v
     LOAD
       |
       v
Power Supply (-)
```

So when the Arduino is powered off, the relay is normally **OFF** because **COM and NO are open**.


---


Use the **MFRC522 library** from Arduino Library Manager. This code does exactly what you described:

* Arduino starts → relay **OFF**
* Scan the authorized RFID card → relay **ON**
* Scan the card again → relay **stays ON**
* Other cards → relay stays OFF
* Power removed → relay returns to its hardware **normally-open/off** state
* When power returns → relay starts OFF

### Arduino Nano code

```cpp
#include <SPI.h>
#include <MFRC522.h>

// ---------------- PIN CONFIGURATION ----------------

#define SS_PIN     10
#define RST_PIN    9
#define RELAY_PIN  7

MFRC522 rfid(SS_PIN, RST_PIN);

// ---------------- AUTHORIZED RFID UID ----------------
// CHANGE THIS TO YOUR CARD'S UID

byte authorizedUID[] = {
  0xDE, 0xAD, 0xBE, 0xEF
};

byte authorizedUIDLength = 4;

// ----------------------------------------------------

bool relayOn = false;

// Most 5V relay modules are ACTIVE LOW.
// If your relay works opposite, change these two.
#define RELAY_ON  LOW
#define RELAY_OFF HIGH


void setup()
{
  Serial.begin(9600);

  // Relay starts OFF
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_OFF);

  // Start SPI
  SPI.begin();

  // Start RFID
  rfid.PCD_Init();

  Serial.println("================================");
  Serial.println("RFID Relay Controller");
  Serial.println("System Started");
  Serial.println("Relay: OFF");
  Serial.println("Scan RFID card...");
  Serial.println("================================");
}


void loop()
{
  // No new RFID card
  if (!rfid.PICC_IsNewCardPresent())
    return;

  // Cannot read card
  if (!rfid.PICC_ReadCardSerial())
    return;

  Serial.println();
  Serial.print("RFID UID: ");

  for (byte i = 0; i < rfid.uid.size; i++)
  {
    if (rfid.uid.uidByte[i] < 0x10)
      Serial.print("0");

    Serial.print(rfid.uid.uidByte[i], HEX);
    Serial.print(" ");
  }

  Serial.println();

  // Check authorization
  if (checkAuthorizedCard())
  {
    Serial.println("AUTHORIZED CARD");

    if (!relayOn)
    {
      relayOn = true;
      digitalWrite(RELAY_PIN, RELAY_ON);

      Serial.println("RELAY: ON");
    }
    else
    {
      // Already ON, do nothing
      Serial.println("RELAY ALREADY ON");
    }
  }
  else
  {
    Serial.println("UNAUTHORIZED CARD");
    Serial.println("RELAY: OFF");
  }

  // Stop communication with card
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(500);
}


// ----------------------------------------------------
// CHECK RFID UID
// ----------------------------------------------------

bool checkAuthorizedCard()
{
  if (rfid.uid.size != authorizedUIDLength)
    return false;

  for (byte i = 0; i < authorizedUIDLength; i++)
  {
    if (rfid.uid.uidByte[i] != authorizedUID[i])
      return false;
  }

  return true;
}
```

### First, find your RFID card UID

The code currently has:

```cpp
byte authorizedUID[] = {
  0xDE, 0xAD, 0xBE, 0xEF
};
```

That's only an example.

Upload the code, open:

**Arduino IDE → Serial Monitor → 9600 baud**

Scan your RFID card.

You'll see something like:

```text
RFID UID: 53 A7 21 19
AUTHORIZED CARD
RELAY: ON
```

Then change:

```cpp
byte authorizedUID[] = {
  0xDE, 0xAD, 0xBE, 0xEF
};
```

to your actual UID:

```cpp
byte authorizedUID[] = {
  0x53, 0xA7, 0x21, 0x19
};
```

### Important relay behavior

Your relay should be connected using **COM + NO**:

```text
                 RELAY
              +---------+
Supply + ---->| COM     |
              |         |
              |   NO ---|---- Load +
              +---------+
                            |
                         Load
                            |
Supply - -------------------+
```

That gives you the fail-safe behavior you requested:

```text
Arduino OFF / Power failure
        ↓
Relay coil OFF
        ↓
COM ──X── NO
        ↓
Load OFF
```

One thing to check: **some relay modules are active-HIGH instead of active-LOW**. If your relay turns ON when it should be OFF, swap:

```cpp
#define RELAY_ON  LOW
#define RELAY_OFF HIGH
```

to:

```cpp
#define RELAY_ON  HIGH
#define RELAY_OFF LOW
```

Also, if this relay is controlling **230V mains**, don't put the mains wiring on a breadboard; use an enclosed, appropriately rated relay setup.

---


For **Arduino Nano + MFRC522**, this simple code scans the card and prints its RFID data/UID in the **Serial Monitor**.

```cpp
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10
#define RST_PIN 9

MFRC522 rfid(SS_PIN, RST_PIN);

void setup()
{
  Serial.begin(9600);

  SPI.begin();
  rfid.PCD_Init();

  Serial.println("RFID Scanner Ready");
  Serial.println("Place your RFID card/tag...");
}

void loop()
{
  // Check for a new card
  if (!rfid.PICC_IsNewCardPresent())
    return;

  // Read the card
  if (!rfid.PICC_ReadCardSerial())
    return;

  Serial.println();
  Serial.println("===== RFID CARD DETECTED =====");

  // Print UID
  Serial.print("UID: ");

  for (byte i = 0; i < rfid.uid.size; i++)
  {
    if (rfid.uid.uidByte[i] < 0x10)
      Serial.print("0");

    Serial.print(rfid.uid.uidByte[i], HEX);

    if (i < rfid.uid.size - 1)
      Serial.print(":");
  }

  Serial.println();

  // Print UID in decimal
  Serial.print("UID Decimal: ");

  for (byte i = 0; i < rfid.uid.size; i++)
  {
    Serial.print(rfid.uid.uidByte[i]);

    if (i < rfid.uid.size - 1)
      Serial.print(" ");
  }

  Serial.println();

  // Print card type
  MFRC522::PICC_Type cardType = rfid.PICC_GetType(rfid.uid.sak);

  Serial.print("Card Type: ");
  Serial.println(rfid.PICC_GetTypeName(cardType));

  Serial.print("UID Size: ");
  Serial.print(rfid.uid.size);
  Serial.println(" bytes");

  Serial.println("==============================");

  // Stop communication with card
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(1000);
}
```

### Serial Monitor

Set the Serial Monitor to **9600 baud**.

Example output:

```text
RFID Scanner Ready
Place your RFID card/tag...

===== RFID CARD DETECTED =====
UID: 53:A7:21:19
UID Decimal: 83 167 33 25
Card Type: MIFARE 1KB
UID Size: 4 bytes
==============================
```

This is a good first test before adding the relay. Once you know the UID, you can put that UID into the relay-control program.
