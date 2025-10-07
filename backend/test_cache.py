import time
import requests

BASE_URL = "http://localhost:8000"
READER_ID = "f5275711-137e-4012-8c0b-097e45bf8474"  # Ganti dengan UUID reader Anda

# Test 1: First request (cache miss)
print("Test 1: First request (cache miss)...")
start = time.time()
response = requests.post(
    f"{BASE_URL}/readers/{READER_ID}/event",
    json={"card_uid": "TEST001", "action": "enter"} 
)
end = time.time()
print(f"Time: {(end-start)*1000:.2f}ms")
print(f"Response: {response.json()}")

# Wait a bit
time.sleep(1)

# Test 2: Second request (cache hit)
print("\nTest 2: Second request (cache hit)...")
start = time.time()
response = requests.post(
    f"{BASE_URL}/readers/{READER_ID}/event",
    json={"card_uid": "TEST001", "action": "enter"}
)
end = time.time()
print(f"Time: {(end-start)*1000:.2f}ms")
print(f"Response: {response.json()}")

# Check cache
print("\nCache contents:")
import redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
cached = r.get("card:TEST001")
print(f"Cached data: {cached}")