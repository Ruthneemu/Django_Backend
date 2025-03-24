import requests
import json
import sys

def test_certificate_issuance():
    # Test data with snake_case field names as expected by the API
    certificate_data = {
        "student_name": "John Doe",
        "course": "Blockchain Development",
        "institution": "Tech University",
        "issue_date": "2024-03-15T12:00:00Z"
    }

    # API endpoint (now using the correct URL)
    url = "http://localhost:8000/api/certificates/issue/"

    try:
        print("Sending request to:", url)
        print("Request data:", json.dumps(certificate_data, indent=2))
        
        # Make the request with debug information
        response = requests.post(
            url,
            json=certificate_data,
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
    test_certificate_issuance() 