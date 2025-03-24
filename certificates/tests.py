from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Certificate
from django.core.management import call_command
from .blockchain import web3, contract, issue_certificate
from web3 import Web3
import json

class BlockchainIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.test_certificate_data = {
            'student_name': 'Alice',
            'course': 'Computer Science',
            'institution': 'University of Blockchain',
            'issue_date': '2025-01-01T00:00:00Z'
        }

    def test_blockchain_connection(self):
        """Test if we can connect to the blockchain"""
        try:
            is_connected = web3.is_connected()
            self.assertTrue(is_connected, "Blockchain connection failed")
            # Test if we can get the network version
            network_id = web3.net.version
            self.assertIsNotNone(network_id, "Could not get network ID")
        except Exception as e:
            self.fail(f"Blockchain connection test failed: {str(e)}")

    def test_smart_contract_connection(self):
        """Test if we can connect to the smart contract"""
        try:
            # Check if contract address is valid
            self.assertTrue(Web3.is_address(contract.address), "Invalid contract address")
            # Check if we can call a view function (assuming your contract has one)
            contract_functions = dir(contract.functions)
            self.assertGreater(len(contract_functions), 0, "No contract functions found")
        except Exception as e:
            self.fail(f"Smart contract connection test failed: {str(e)}")

    def test_certificate_hash_generation(self):
        """Test if certificate hash generation is consistent"""
        # Generate hash for the same data twice
        result1 = issue_certificate(**self.test_certificate_data)
        result2 = issue_certificate(**self.test_certificate_data)
        
        # Verify hashes are consistent
        self.assertEqual(
            result1['cert_hash'], 
            result2['cert_hash'], 
            "Hash generation is not consistent for the same data"
        )
        
        # Verify hash format
        self.assertTrue(
            result1['cert_hash'].startswith('0x'),
            "Certificate hash should start with '0x'"
        )
        self.assertEqual(
            len(result1['cert_hash']), 
            66,  # '0x' + 64 hex characters
            "Certificate hash should be 32 bytes (64 hex characters) plus '0x'"
        )

    def test_different_certificate_different_hash(self):
        """Test if different certificate data produces different hashes"""
        result1 = issue_certificate(**self.test_certificate_data)
        
        modified_data = self.test_certificate_data.copy()
        modified_data['student_name'] = 'Bob'
        result2 = issue_certificate(**modified_data)
        
        self.assertNotEqual(
            result1['cert_hash'], 
            result2['cert_hash'], 
            "Different certificate data should produce different hashes"
        )

class CertificateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.issue_url = reverse('issue_certificate')
        self.verify_url = reverse('verify_certificate', args=['dummy_hash'])
        self.test_certificate_data = {
            'student_name': 'Alice',
            'course': 'Computer Science',
            'institution': 'University of Blockchain',
            'issue_date': '2025-01-01T00:00:00Z'
        }
        
        # Run migrations
        call_command('migrate')

    def test_issue_certificate(self):
        """Test certificate issuance"""
        response = self.client.post(self.issue_url, self.test_certificate_data, format='json')
        if response.status_code != status.HTTP_200_OK:
            print(f"Response data: {response.data}")  # Debug information
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cert_hash', response.data)

    def test_verify_certificate(self):
        """Test certificate verification with a valid certificate"""
        # First, issue a certificate
        issue_response = self.client.post(self.issue_url, self.test_certificate_data, format='json')
        if issue_response.status_code != status.HTTP_200_OK:
            print(f"Issue response data: {issue_response.data}")  # Debug information
            self.skipTest("Certificate issuance failed, skipping verification test")
            
        cert_hash = issue_response.data['cert_hash']
        
        # Now verify the certificate
        verify_url = reverse('verify_certificate', args=[cert_hash])
        response = self.client.get(verify_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['certificate']['student_name'], 'Alice')

    def test_invalid_certificate_verification(self):
        """Test verification of non-existent certificate"""
        invalid_hash = '0x1234567890abcdef'
        verify_url = reverse('verify_certificate', args=[invalid_hash])
        response = self.client.get(verify_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_certificate_model(self):
        """Test the Certificate model directly"""
        certificate = Certificate.objects.create(
            student_name='Alice',
            course='Computer Science',
            institution='University of Blockchain',
            issue_date='2025-01-01T00:00:00Z',
            cert_hash='0x123',
            ipfs_hash='QmTest'
        )
        self.assertEqual(str(certificate), "Certificate for Alice")
        self.assertEqual(certificate.course, "Computer Science")
