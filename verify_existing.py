"""
Script to verify an existing certificate.
"""
import os
import django
from web3 import Web3

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'certificate_backend.settings')
django.setup()

from certificates.models import Certificate
from certificates.blockchain import verify_certificate_on_chain, contract

def list_certificates():
    """List all certificates in the database"""
    certificates = Certificate.objects.all()
    print(f"Found {len(certificates)} certificates in the database:")
    
    for i, cert in enumerate(certificates, 1):
        print(f"{i}. ID: {cert.id}, Name: {cert.student_name}, Hash: {cert.cert_hash}")

def verify_certificate(cert_id):
    """Verify a certificate by its database ID"""
    try:
        # Get the certificate from the database
        certificate = Certificate.objects.get(id=cert_id)
        print(f"\nFound certificate: {certificate.student_name} - {certificate.course}")
        
        cert_hash = certificate.cert_hash
        print(f"Certificate hash: {cert_hash}")
        
        # Try to verify on blockchain
        print("\nVerifying on blockchain...")
        try:
            blockchain_result = verify_certificate_on_chain(cert_hash)
            print(f"Blockchain verification result: {blockchain_result}")
            
            if blockchain_result:
                is_valid = blockchain_result[0]
                print(f"Certificate valid on blockchain: {is_valid}")
                print(f"Student Name: {blockchain_result[1]}")
                print(f"Course: {blockchain_result[2]}")
                print(f"Institution: {blockchain_result[3]}")
                print(f"Issue Date: {blockchain_result[4]}")
            else:
                print("Blockchain verification returned None")
                
        except Exception as e:
            print(f"Error during blockchain verification: {str(e)}")
            
        # Direct contract call
        print("\nDirect contract call...")
        try:
            # Convert hash to bytes32
            if cert_hash.startswith('0x'):
                cert_hash = cert_hash[2:]
                
            cert_hash_bytes = Web3.to_bytes(hexstr=cert_hash)
            print(f"Calling contract.certificates with hash: {cert_hash_bytes.hex()}")
            result = contract.functions.certificates(cert_hash_bytes).call()
            print(f"Certificate data from contract: {result}")
        except Exception as e:
            print(f"Error calling contract directly: {str(e)}")
            
    except Certificate.DoesNotExist:
        print(f"No certificate found with ID {cert_id}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    list_certificates()
    cert_id = int(input("\nEnter the ID of the certificate to verify: "))
    verify_certificate(cert_id) 