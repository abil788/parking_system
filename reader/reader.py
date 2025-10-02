"""
RFID/NFC Reader Script for Raspberry Pi
Simulates card reading and sends events to backend server

Usage:
    python reader.py --reader-id=<UUID> --server=http://localhost:8000 --action=enter

For real RFID implementation, install: pip install mfrc522
"""
import argparse
import httpx
import sys
import time
from datetime import datetime


class CardReader:
    def __init__(self, reader_id: str, server_url: str, action: str = "enter"):
        self.reader_id = reader_id
        self.server_url = server_url.rstrip('/')
        self.action = action
        self.endpoint = f"{self.server_url}/readers/{self.reader_id}/event"
        
    def send_event(self, card_uid: str) -> dict:
        """Send access event to server"""
        try:
            response = httpx.post(
                self.endpoint,
                json={
                    "card_uid": card_uid,
                    "action": self.action
                },
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "result": "error",
                "message": f"Connection error: {str(e)}"
            }
        except Exception as e:
            return {
                "result": "error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    def display_result(self, result: dict):
        """Display access result with colors"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if result.get("result") == "granted":
            print(f"\n{'='*60}")
            print(f"[{timestamp}] ✓ ACCESS GRANTED")
            print(f"{'='*60}")
            print(f"Owner: {result.get('owner_name', 'N/A')}")
            print(f"Vehicle: {result.get('vehicle_plate', 'N/A')}")
            print(f"Message: {result.get('message', '')}")
            print(f"{'='*60}\n")
        elif result.get("result") == "denied":
            print(f"\n{'='*60}")
            print(f"[{timestamp}] ✗ ACCESS DENIED")
            print(f"{'='*60}")
            print(f"Reason: {result.get('reason', 'unknown')}")
            print(f"Message: {result.get('message', '')}")
            if result.get('owner_name'):
                print(f"Owner: {result.get('owner_name')}")
            print(f"{'='*60}\n")
        else:
            print(f"\n[{timestamp}] ⚠ ERROR: {result.get('message', 'Unknown error')}\n")
    
    def simulate_scan(self):
        """Simulate card scanning with manual input"""
        print(f"\n{'*'*60}")
        print(f"  RFID/NFC Reader - {self.action.upper()} Gate")
        print(f"  Reader ID: {self.reader_id}")
        print(f"  Server: {self.server_url}")
        print(f"{'*'*60}\n")
        print("Ready to scan cards. Type 'exit' to quit.\n")
        
        while True:
            try:
                card_uid = input("Scan card (enter UID): ").strip()
                
                if card_uid.lower() == 'exit':
                    print("\nExiting reader...")
                    break
                
                if not card_uid:
                    continue
                
                print(f"\nProcessing card: {card_uid}...")
                result = self.send_event(card_uid)
                self.display_result(result)
                
            except KeyboardInterrupt:
                print("\n\nExiting reader...")
                break
            except Exception as e:
                print(f"\nError: {e}")
    
    def read_hardware_rfid(self):
        """
        Read from actual RFID hardware (MFRC522)
        Requires: pip install mfrc522
        Uncomment this method to use with real hardware
        """
        try:
            from mfrc522 import SimpleMFRC522
            import RPi.GPIO as GPIO
            
            reader = SimpleMFRC522()
            
            print(f"\n{'*'*60}")
            print(f"  RFID Reader - {self.action.upper()} Gate")
            print(f"  Reader ID: {self.reader_id}")
            print(f"  Server: {self.server_url}")
            print(f"{'*'*60}\n")
            print("Ready to scan RFID cards. Press Ctrl+C to exit.\n")
            
            while True:
                try:
                    print("Waiting for card...")
                    card_id, text = reader.read()
                    card_uid = str(card_id)
                    
                    print(f"\nCard detected: {card_uid}")
                    result = self.send_event(card_uid)
                    self.display_result(result)
                    
                    time.sleep(2)  # Prevent multiple reads
                    
                except KeyboardInterrupt:
                    print("\n\nExiting reader...")
                    GPIO.cleanup()
                    break
                    
        except ImportError:
            print("Error: mfrc522 library not installed.")
            print("Install with: pip install mfrc522")
            print("Falling back to simulation mode...")
            self.simulate_scan()
        except Exception as e:
            print(f"Hardware error: {e}")
            print("Falling back to simulation mode...")
            self.simulate_scan()


def main():
    parser = argparse.ArgumentParser(description="RFID/NFC Reader Client")
    parser.add_argument(
        "--reader-id",
        required=True,
        help="UUID of the reader device"
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Backend server URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--action",
        choices=["enter", "exit"],
        default="enter",
        help="Action type: enter or exit (default: enter)"
    )
    parser.add_argument(
        "--hardware",
        action="store_true",
        help="Use hardware RFID reader (MFRC522)"
    )
    
    args = parser.parse_args()
    
    reader = CardReader(
        reader_id=args.reader_id,
        server_url=args.server,
        action=args.action
    )
    
    if args.hardware:
        reader.read_hardware_rfid()
    else:
        reader.simulate_scan()


if __name__ == "__main__":
    main()