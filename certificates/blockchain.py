# certificates/blockchain.py

import json
import os
import sys
import time
from web3 import Web3
from django.core.files.base import ContentFile
from django.conf import settings

# Web3 setup
GANACHE_URL = 'http://127.0.0.1:8545'

class BlockchainConnectionError(Exception):
    """Raised when blockchain connection fails"""
    pass

class SmartContractError(Exception):
    """Raised when smart contract interaction fails"""
    pass

def get_web3():
    """Get Web3 instance with error handling"""
    try:
        print(f"Attempting to connect to Ganache at {GANACHE_URL}")
        web3_instance = Web3(Web3.HTTPProvider(GANACHE_URL))
        
        # Test the connection
        if not web3_instance.is_connected():
            raise BlockchainConnectionError("Could not connect to blockchain")
            
        # Get the current block number to verify chain sync
        block_number = web3_instance.eth.block_number
        print(f"Connected to blockchain. Current block number: {block_number}")
        
        return web3_instance
    except Exception as e:
        print(f"Web3 connection error: {str(e)}")
        raise BlockchainConnectionError(f"Web3 initialization failed: {str(e)}")

def get_contract(web3_instance):
    """Get contract instance with error handling"""
    try:
        # Contract setup
        ABI_PATH = '../certificate-verification-system/build/contracts/CertificateVerification.json'
        
        if not os.path.exists(ABI_PATH):
            raise SmartContractError(f"Contract ABI file not found at {ABI_PATH}")
            
        print(f"Loading contract ABI from {ABI_PATH}")
        with open(ABI_PATH, 'r') as abi_file:
            artifact = json.load(abi_file)
            
        contract_abi = artifact["abi"]
        CONTRACT_ADDRESS = '0xEc2262Ed50CB05C3844E1080d88550d403e4556F'  # Updated contract address
        
        if not Web3.is_address(CONTRACT_ADDRESS):
            raise SmartContractError(f"Invalid contract address: {CONTRACT_ADDRESS}")
            
        print(f"Initializing contract at address: {CONTRACT_ADDRESS}")
        contract = web3_instance.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
        
        # Test contract connection by checking if we can access the contract
        try:
            # Create a test hash and try to access the certificates mapping
            test_hash = Web3.keccak(text="test")
            contract.functions.certificates(test_hash).call()
            print("Contract connection test successful")
        except Exception as e:
            print(f"Contract connection test failed: {str(e)}")
            raise SmartContractError("Contract is not properly deployed or initialized")
            
        return contract
    except Exception as e:
        if isinstance(e, SmartContractError):
            raise e
        raise SmartContractError(f"Contract initialization failed: {str(e)}")

# Initialize Web3 and contract
try:
    print("Initializing blockchain connection...")
    web3 = get_web3()
    contract = get_contract(web3)
    print("Blockchain connection initialized successfully")
except (BlockchainConnectionError, SmartContractError) as e:
    print(f"Warning: {str(e)}")
    web3 = None
    contract = None

def is_test_mode():
    """Check if we're running in test mode"""
    return 'test' in sys.argv

def issue_certificate(student_name, course, institution, issue_date):
    """Issue a certificate and store its hash on the blockchain"""
    if not all([student_name, course, institution, issue_date]):
        raise ValueError("All certificate fields are required")

    # Convert issue_date to integer if it's a string
    if isinstance(issue_date, str):
        try:
            issue_date = int(issue_date)
        except ValueError:
            raise ValueError("issue_date must be a valid integer timestamp")

    # Validate the timestamp is reasonable (not in the future, not too far in the past)
    current_time = int(time.time())
    if issue_date > current_time:
        raise ValueError("Issue date cannot be in the future")
    if issue_date < 946684800:  # Jan 1, 2000
        raise ValueError("Issue date seems too old (before year 2000)")

    # Generate the hash in the same way as the blockchain smart contract
    # This matches keccak256(abi.encodePacked(student_name, course, institution, issue_date)) in Solidity
    cert_hash = '0x' + Web3.solidity_keccak(
        ['string', 'string', 'string', 'uint256'],
        [student_name, course, institution, issue_date]
    ).hex()
    
    print(f"Generated certificate hash: {cert_hash}")
    
    # If we're not in test mode and blockchain is available, store on chain
    if not is_test_mode() and web3 and contract:
        try:
            print(f"Attempting to issue certificate for {student_name}, course: {course}")
            
            # Get the first account to use as sender
            account = web3.eth.accounts[0]
            if not account:
                raise SmartContractError("No blockchain account available")
            
            print(f"Using account {account} to issue certificate")
            
            # Store certificate on blockchain with correct parameter order
            tx_hash = contract.functions.issueCertificate(
                student_name,  # string _studentName
                course,        # string _course
                institution,   # string _institution
                issue_date    # uint256 _issueDate
            ).transact({'from': account})
            
            print(f"Transaction sent with hash: {tx_hash.hex()}")
            
            # Wait for transaction to be mined
            print("Waiting for transaction to be mined...")
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status != 1:
                raise SmartContractError(f"Transaction failed. Receipt status: {tx_receipt.status}")
            
            # Log successful transaction
            print(f"Certificate issued successfully. Transaction hash: {tx_hash.hex()}")
            print(f"Block number: {tx_receipt.blockNumber}")
            print(f"Gas used: {tx_receipt.gasUsed}")
                
        except Exception as e:
            error_msg = str(e)
            print(f"Warning: Blockchain storage failed: {error_msg}")
            
            if "already exists" in error_msg.lower():
                raise SmartContractError("Certificate with this data already exists on the blockchain")
            elif "revert" in error_msg.lower():
                raise SmartContractError("Smart contract reverted the transaction. Possible duplicate certificate or invalid data.")
            else:
                raise SmartContractError(f"Failed to store certificate on blockchain: {error_msg}")
    
    return {
        'cert_hash': cert_hash,
        'ipfs_hash': None,  # IPFS storage is currently disabled
        'transaction_hash': tx_hash.hex() if 'tx_hash' in locals() else None
    }

def verify_certificate_on_chain(cert_hash):
    """Verify a certificate on the blockchain"""
    if not web3:
        print("Error: Web3 connection not available")
        raise BlockchainConnectionError("Web3 connection not available")
    if not contract:
        print("Error: Smart contract not initialized")
        raise BlockchainConnectionError("Smart contract not initialized")
        
    try:
        print(f"Attempting to verify certificate hash: {cert_hash}")
        
        # Convert the hash to bytes32 format
        if cert_hash.startswith('0x'):
            cert_hash = cert_hash[2:]  # Remove '0x' prefix if present
        
        print(f"Formatted hash for verification: {cert_hash}")
            
        # Convert hex string to bytes32
        try:
            cert_hash_bytes = Web3.to_bytes(hexstr=cert_hash)
            print(f"Converted hash to bytes: {cert_hash_bytes.hex()}")
        except Exception as e:
            print(f"Error converting hash to bytes: {str(e)}")
            raise SmartContractError(f"Invalid certificate hash format: {str(e)}")
        
        # Call the contract with the properly formatted hash
        try:
            print(f"Calling contract.verifyCertificate with hash: {cert_hash_bytes.hex()}")
            result = contract.functions.verifyCertificate(cert_hash_bytes).call()
            print(f"Blockchain verification result: {result}")
            return result
        except Exception as contract_error:
            error_msg = str(contract_error)
            print(f"Contract call error: {error_msg}")
            
            if "revert Certificate not found" in error_msg:
                raise SmartContractError("Certificate not found on blockchain")
            elif "revert" in error_msg:
                raise SmartContractError(f"Contract reverted: {error_msg}")
            else:
                raise SmartContractError(f"Contract call failed: {error_msg}")
    except Exception as e:
        if isinstance(e, (BlockchainConnectionError, SmartContractError)):
            raise e
            
        error_msg = str(e)
        print(f"Error during blockchain verification: {error_msg}")
        if "connection" in error_msg.lower():
            raise BlockchainConnectionError("Failed to connect to blockchain")
        
        raise SmartContractError(f"Blockchain verification failed: {error_msg}")

def revoke_certificate(cert_hash):
    """Revoke a certificate on the blockchain"""
    if not web3 or not contract:
        raise BlockchainConnectionError("Blockchain connection not available")
        
    try:
        # Get the first account to use as sender (assuming it's an admin account)
        account = web3.eth.accounts[0]
        
        # Call the smart contract's revokeCertificate function
        tx_hash = contract.functions.revokeCertificate(cert_hash).transact({'from': account})
        
        # Wait for transaction to be mined
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        
        if tx_receipt.status != 1:
            raise SmartContractError("Revocation transaction failed")
            
        return True
    except Exception as e:
        raise SmartContractError(f"Certificate revocation failed: {str(e)}")