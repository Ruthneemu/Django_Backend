import requests
import json
import sys

def verify_certificate(cert_hash):
    # API endpoint for verification
    url = f"http://localhost:8000/api/certificates/verify/{cert_hash}/"

    try:
        print("Sending verification request to:", url)
        
        # Make the request with debug information
        response = requests.get(
            url,
            headers={"Content-Type": "application/json"}
        )
        
        print("\nResponse Status Code:", response.status_code)
        print("Response Headers:", dict(response.headers))
        
        try:
            print("Response Body:", json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("Response Body (raw):", response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Is the Django server running?")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Use the cert_hash from the previous issuance response
    cert_hash = "0x7ee5f401621533aedde4960c22b2977ee8fba17420c7fb59845cc1df609c684f"
    verify_certificate(cert_hash) 