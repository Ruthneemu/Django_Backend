from web3 import Web3
import json

# Certificate data from successful issuance
cert_data = {
    'student_name': 'Kiragu',
    'course': 'ICTM',
    'institution': 'maseno',
    'issue_date': 1740258000
}

# Method used in issue_certificate function
def generate_cert_hash_for_issuance(data):
    return '0x' + Web3.keccak(text=json.dumps(data)).hex()

# How the hash is passed to the smart contract in issueCertificate
def generate_on_chain_hash(student_name, course, institution, issue_date):
    # This simulates the Solidity function: keccak256(abi.encodePacked(student_name, course, institution, issue_date))
    # In Web3.py, we need to manually construct the packed encoding
    packed_data = Web3.solidity_keccak(
        ['string', 'string', 'string', 'uint256'],
        [student_name, course, institution, issue_date]
    )
    return '0x' + packed_data.hex()

# Compare the hashes
issuance_hash = generate_cert_hash_for_issuance(cert_data)
onchain_hash = generate_on_chain_hash(
    cert_data['student_name'],
    cert_data['course'],
    cert_data['institution'],
    cert_data['issue_date']
)

print("Hash generated during issuance:", issuance_hash)
print("Hash generated on blockchain:", onchain_hash)
print("Are they the same?", issuance_hash == onchain_hash)

# The certificate hash from your successful issuance
actual_cert_hash = "0xc62afda06135cf9d32d87579d873a26a10bc5922ea283d6bfa45837d32e215fb"
print("\nActual certificate hash:", actual_cert_hash)
print("Matches issuance hash?", actual_cert_hash == issuance_hash)
print("Matches onchain hash?", actual_cert_hash == onchain_hash)

if __name__ == "__main__":
    print("\nWhen looking up this certificate on the blockchain, we should be using:", onchain_hash) 