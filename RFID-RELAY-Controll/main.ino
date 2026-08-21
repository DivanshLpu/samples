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
