from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Certificate

class CertificateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.issue_url = reverse('issue_certificate')
        self.verify_url = reverse('verify_certificate', args=['dummy_hash'])

    def test_issue_certificate(self):
        data = {
            'student_name': 'Alice',
            'course': 'Computer Science',
            'institution': 'University of Blockchain',
            'issue_date': '2025-01-01T00:00:00Z'
        }
        response = self.client.post(self.issue_url, data, format='json')
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            print(f"Error: {response.data['error']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cert_hash', response.data)

    def test_verify_certificate(self):
        # First, issue a certificate
        data = {
            'student_name': 'Alice',
            'course': 'Computer Science',
            'institution': 'University of Blockchain',
            'issue_date': '2025-01-01T00:00:00Z'
        }
        response = self.client.post(self.issue_url, data, format='json')
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            print(f"Error: {response.data['error']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cert_hash = response.data['cert_hash']

        # Now, verify the issued certificate
        verify_url = reverse('verify_certificate', args=[cert_hash])
        response = self.client.get(verify_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['certificate']['student_name'], 'Alice')
        self.assertEqual(response.data['certificate']['course'], 'Computer Science')
        self.assertEqual(response.data['certificate']['institution'], 'University of Blockchain')
        self.assertTrue(response.data['is_valid'])
