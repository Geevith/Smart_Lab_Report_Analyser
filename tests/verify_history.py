import requests
import time
import os

def test_history():
    print("Testing History Integration...")
    
    # 1. Create a dummy test file
    with open("test_history.txt", "w") as f:
        f.write("Hemoglobin: 12.0\n") # Normal value triggers report save
        
    # 2. Upload file to analyze (triggers save_report)
    url_analyze = "http://127.0.0.1:8000/analyze"
    files = {'file': open("test_history.txt", 'rb')}
    
    try:
        print("Sending analysis request...")
        resp = requests.post(url_analyze, files=files)
        if resp.status_code == 200:
            print("Analysis successful.")
        else:
            print(f"Analysis failed: {resp.status_code}")
            return

        # 3. Check history endpoint
        print("Checking history...")
        url_history = "http://127.0.0.1:8000/history"
        resp_hist = requests.get(url_history)
        
        if resp_hist.status_code == 200:
            history = resp_hist.json()
            print(f"History items found: {len(history)}")
            
            # Check if our file is in the latest history
            if history and history[0]['filename'] == "test_history.txt":
                print("SUCCESS: Latest file found in history.")
                print(f"Entry: {history[0]}")
            else:
                print("FAILURE: File not found in latest history.")
                print(f"Latest: {history[0] if history else 'None'}")
        else:
             print(f"History endpoint failed: {resp_hist.status_code}")
             
    except Exception as e:
        print(f"Test Error: {e}")
    finally:
        files['file'].close()
        if os.path.exists("test_history.txt"):
            os.remove("test_history.txt")

if __name__ == "__main__":
    test_history()
