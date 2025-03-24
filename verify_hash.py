"""
Script to verify a certificate by its hash.
"""
import os
import django
from web3 import Web3
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'certificate_backend.settings')
django.setup()

from certificates.models import Certificate
from certificates.blockchain import verify_certificate_on_chain, contract, web3, issue_certificate

def verify_by_hash(cert_hash):
    """Verify a certificate directly by its hash"""
    print(f"\nAttempting to verify certificate with hash: {cert_hash}")
    
    # Check if certificate exists in the database
    try:
        print("\nChecking database...")
        certificate = Certificate.objects.filter(cert_hash=cert_hash).first()
        if certificate:
            print(f"Found in database: {certificate.student_name} - {certificate.course}")
            print(f"Issue Date: {certificate.issue_date}")
            print(f"Is Revoked: {certificate.is_revoked}")
        else:
            print("Certificate not found in database")
    except Exception as e:
        print(f"Database error: {str(e)}")
    
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
        hash_no_prefix = cert_hash
        if cert_hash.startswith('0x'):
            hash_no_prefix = cert_hash[2:]
            
        cert_hash_bytes = Web3.to_bytes(hexstr=hash_no_prefix)
        print(f"Calling contract.certificates with hash: {cert_hash_bytes.hex()}")
        result = contract.functions.certificates(cert_hash_bytes).call()
        print(f"Certificate data from contract: {result}")
        
        # Try to reconstruct the hash
        student_name = result[0]
        course = result[1]
        institution = result[2]
        issue_date = result[3]
        
        # Generate the hash from the blockchain data
        reconstructed_hash = '0x' + Web3.solidity_keccak(
            ['string', 'string', 'string', 'uint256'],
            [student_name, course, institution, issue_date]
        ).hex()
        
        print(f"\nReconstructed hash from blockchain data: {reconstructed_hash}")
        print(f"Does it match the provided hash? {reconstructed_hash == cert_hash}")
        
    except Exception as e:
        print(f"Error calling contract directly: {str(e)}")

def list_accounts():
    """List all accounts in Ganache"""
    print("\nAvailable accounts in Ganache:")
    for i, account in enumerate(web3.eth.accounts):
        balance = web3.eth.get_balance(account)
        print(f"{i+1}. {account} - Balance: {web3.from_wei(balance, 'ether')} ETH")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cert_hash = sys.argv[1]
    else:
        cert_hash = input("Enter certificate hash to verify: ")
        
    verify_by_hash(cert_hash)
    list_accounts() 