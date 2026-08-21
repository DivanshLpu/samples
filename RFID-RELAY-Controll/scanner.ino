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