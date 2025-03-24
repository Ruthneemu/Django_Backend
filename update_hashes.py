"""
Script to update certificate hashes in the database to match the blockchain hash generation method.
"""
import os
import django
from django.db import transaction
from web3 import Web3

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'certificate_backend.settings')
django.setup()

from certificates.models import Certificate

def generate_blockchain_hash(student_name, course, institution, issue_date):
    """Generate hash in the same way as the blockchain contract"""
    return '0x' + Web3.solidity_keccak(
        ['string', 'string', 'string', 'uint256'],
        [student_name, course, institution, int(issue_date.timestamp())]
    ).hex()

def update_certificate_hashes():
    """Update all certificate hashes in the database"""
    certificates = Certificate.objects.all()
    print(f"Found {len(certificates)} certificates to update")
    
    updated_count = 0
    with transaction.atomic():
        for cert in certificates:
            old_hash = cert.cert_hash
            new_hash = generate_blockchain_hash(
                cert.student_name,
                cert.course,
                cert.institution,
                cert.issue_date
            )
            
            print(f"Certificate ID: {cert.id}")
            print(f"Old hash: {old_hash}")
            print(f"New hash: {new_hash}")
            print("---")
            
            cert.cert_hash = new_hash
            cert.save()
            updated_count += 1
    
    print(f"Updated {updated_count} certificate hashes")

if __name__ == "__main__":
    update_certificate_hashes()
    print("Done!") 