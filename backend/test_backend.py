import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_chat(message, agent_id=None, user_id="test_user"):
    url = f"{BASE_URL}/api/chat"
    payload = {
        "message": message,
        "userId": user_id,
        "agentId": agent_id
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def run_tests():
    print("Waiting for server to start...")
    time.sleep(5)
    
    print("\n--- Test 1: Math Agent Routing ---")
    res = test_chat("What is 25 * 4?")
    if res:
        print(f"Agent: {res.get('agentName')}")
        print(f"Reply: {res.get('reply')}")
        if res.get('agentName') == 'math':
            print("✅ PASS: Correctly routed to Math Agent")
        else:
            print("❌ FAIL: Incorrect agent")

    print("\n--- Test 2: Memory (Set Context) ---")
    res = test_chat("My name is Antigravity.", user_id="memory_user")
    if res:
        print(f"Reply: {res.get('reply')}")

    print("\n--- Test 3: Memory (Retrieve Context) ---")
    res = test_chat("What is my name?", user_id="memory_user")
    if res:
        print(f"Reply: {res.get('reply')}")
        if "Antigravity" in res.get('reply', ''):
            print("✅ PASS: Memory successfully retrieved")
        else:
            print("❌ FAIL: Memory not retrieved")

if __name__ == "__main__":
    run_tests()
