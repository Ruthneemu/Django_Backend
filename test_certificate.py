"""
Script to test issuing and verifying a certificate directly.
"""
import os
import django
import time
from web3 import Web3
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'certificate_backend.settings')
django.setup()

from certificates.blockchain import issue_certificate, verify_certificate_on_chain
from certificates.models import Certificate
from django.utils import timezone
from datetime import datetime

def test_issue_and_verify():
    """Test issuing and immediately verifying a certificate"""
    # Certificate data
    student_name = "Test Student"
    course = "Test Course"
    institution = "Test University"
    issue_date = int(time.time())  # Current timestamp
    
    try:
        print("\n----- ISSUING NEW CERTIFICATE -----")
        # Issue certificate
        result = issue_certificate(student_name, course, institution, issue_date)
        cert_hash = result['cert_hash']
        tx_hash = result.get('transaction_hash')
        
        print(f"Certificate issued with hash: {cert_hash}")
        print(f"Transaction hash: {tx_hash}")
        
        # Create database record
        issue_date_datetime = datetime.fromtimestamp(issue_date)
        certificate = Certificate.objects.create(
            student_name=student_name,
            course=course,
            institution=institution,
            issue_date=issue_date_datetime,
            cert_hash=cert_hash
        )
        print(f"Certificate created in database with ID: {certificate.id}")
        
        # Wait a moment for the transaction to be mined
        print("\nWaiting 2 seconds for transaction to be mined...")
        time.sleep(2)
        
        print("\n----- VERIFYING CERTIFICATE -----")
        # Try to verify the certificate
        try:
            blockchain_result = verify_certificate_on_chain(cert_hash)
            if blockchain_result:
                is_valid = blockchain_result[0]
                print(f"Blockchain verification result: {blockchain_result}")
                print(f"Certificate is valid on blockchain: {is_valid}")
            else:
                print("Blockchain verification returned None")
        except Exception as e:
            print(f"Error during verification: {str(e)}")
        
        # Verify using direct contract call - just for testing
        from certificates.blockchain import web3, contract
        
        print("\n----- DIRECT CONTRACT CALL -----")
        if cert_hash.startswith('0x'):
            cert_hash = cert_hash[2:]
            
        try:
            cert_hash_bytes = Web3.to_bytes(hexstr=cert_hash)
            print(f"Calling contract directly with hash: {cert_hash_bytes.hex()}")
            result = contract.functions.certificates(cert_hash_bytes).call()
            print(f"Certificate data from contract: {result}")
        except Exception as e:
            print(f"Error calling contract directly: {str(e)}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_issue_and_verify()
    print("\nTest completed!") 