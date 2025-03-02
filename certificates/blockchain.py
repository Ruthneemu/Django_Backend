# certificates/blockchain.py

import json
import ipfshttpclient
from web3 import Web3
from django.core.files.base import ContentFile

# Connect to IPFS daemon
try:
    ipfs_client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
except Exception as e:
    print(f"Warning: Could not connect to IPFS daemon: {str(e)}")
    ipfs_client = None

# Web3 setup
GANACHE_URL = 'http://127.0.0.1:8545'
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# Contract setup
ABI_PATH = '../certificate-verification-system/build/contracts/CertificateVerification.json'

with open(ABI_PATH, 'r') as abi_file:
    artifact = json.load(abi_file)

contract_abi = artifact["abi"]
CONTRACT_ADDRESS = '0xA172B37A2fB70aBE269559726B47c73956E62769'
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

def store_on_ipfs(data):
    """Store data on IPFS and return the hash"""
    if not ipfs_client:
        raise Exception("IPFS client not connected")
    
    # Convert data to JSON string
    json_data = json.dumps(data)
    # Add to IPFS
    res = ipfs_client.add_json(json_data)
    return res

def issue_certificate(student_name, course, institution, issue_date):
    # Prepare certificate data
    certificate_data = {
        'student_name': student_name,
        'course': course,
        'institution': institution,
        'issue_date': issue_date
    }
    
    try:
        # Store on IPFS
        ipfs_hash = store_on_ipfs(certificate_data)
        
        # Store hash on blockchain
        cert_hash = web3.keccak(text=ipfs_hash)
        tx_hash = contract.functions.issueCertificate(
            student_name,
            course,
            institution,
            issue_date
        ).transact()
        receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        
        return {
            'cert_hash': cert_hash.hex(),
            'ipfs_hash': ipfs_hash
        }
    except Exception as e:
        raise Exception(f"Failed to issue certificate: {str(e)}")