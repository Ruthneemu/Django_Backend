import requests
import json
import sys

def revoke_certificate(cert_hash):
    # API endpoint for revocation
    url = f"http://localhost:8000/api/certificates/revoke/{cert_hash}/"

    try:
        print("Sending revocation request to:", url)
        
        # Make the request with debug information
        response = requests.post(
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
    cert_hash = "0x7869c689d7638317fe4d7b1b575a140d53e5213a32dc3cfdd7cdc33f1afe09e8"
    revoke_certificate(cert_hash) 