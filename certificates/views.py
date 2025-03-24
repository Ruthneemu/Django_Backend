from django.db import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.http import JsonResponse
from .models import Certificate
from .serializers import CertificateSerializer
from .blockchain import issue_certificate, revoke_certificate, verify_certificate_on_chain
from rest_framework.views import APIView
from rest_framework import status
from datetime import datetime

class IssueCertificateView(APIView):
    def post(self, request):
        student_name = request.data.get('studentName')
        course = request.data.get('course')
        institution = request.data.get('institution')
        issue_date = request.data.get('issueDate')

        cert_hash = issue_certificate(student_name, course, institution, issue_date)
        return Response({'certHash': cert_hash}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def issue_certificate_view(request):
    try:
        # Validate required fields
        required_fields = ['student_name', 'course', 'institution', 'issue_date']
        for field in required_fields:
            if not request.data.get(field):
                return Response(
                    {'error': f'Missing required field: {field}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Get the timestamp and convert it to datetime for the model
        timestamp = request.data.get('issue_date')
        try:
            timestamp = int(timestamp)
            issue_date = datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            return Response(
                {'error': 'issue_date must be a valid integer timestamp'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # First, attempt to issue on blockchain
        result = issue_certificate(
            request.data.get('student_name'),
            request.data.get('course'),
            request.data.get('institution'),
            timestamp
        )
        
        # Verify the blockchain transaction was successful
        if not result.get('transaction_hash'):
            return Response(
                {'error': 'Failed to issue certificate on blockchain'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        # No need to verify immediately - blockchain transaction success is enough
        # This was causing an error because the block might not be mined yet
        
        # Only create database record if blockchain transaction was successful
        certificate = Certificate.objects.create(
            student_name=request.data.get('student_name'),
            course=request.data.get('course'),
            institution=request.data.get('institution'),
            issue_date=issue_date,
            cert_hash=result['cert_hash'],
            ipfs_hash=result.get('ipfs_hash', '')
        )
        
        return Response({
            'cert_hash': result['cert_hash'],
            'certificate': CertificateSerializer(certificate).data,
            'transaction_hash': result['transaction_hash']
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def verify_certificate_view(request, cert_hash):
    """
    Verify a certificate by its hash.
    """
    try:
        print(f"Attempting to verify certificate: {cert_hash}")
        
        # Normalize hash format - ensure it has 0x prefix
        if not cert_hash.startswith('0x'):
            cert_hash = '0x' + cert_hash
            print(f"Normalized hash to: {cert_hash}")
            
        # First try to get the certificate from database
        try:
            certificate = Certificate.objects.get(cert_hash=cert_hash)
            print(f"Certificate found in database: {certificate.student_name}")
            found_in_db = True
        except Certificate.DoesNotExist:
            print(f"Certificate not found in database with direct hash match: {cert_hash}")
            
            # Try a fuzzy search by student name, course, and institution
            # This helps find certificates that were re-hashed during the migration
            certificates = Certificate.objects.all()
            found_in_db = False
            certificate = None
            
            for cert in certificates:
                # Check if the first part of the hash matches (simple fuzzy match)
                if cert_hash[:20] in cert.cert_hash or cert.cert_hash[:20] in cert_hash:
                    print(f"Possible match found: {cert.cert_hash}")
                    certificate = cert
                    found_in_db = True
                    break
            
            if not found_in_db:
                return Response(
                    {'error': 'Certificate not found in database'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Then try to verify on blockchain
        blockchain_valid = False
        blockchain_result = None
        blockchain_error = None
        
        try:
            print(f"Attempting blockchain verification for: {cert_hash}")
            blockchain_result = verify_certificate_on_chain(cert_hash)
            
            if blockchain_result is None:
                print("Blockchain verification returned None")
                blockchain_error = "Certificate does not exist on blockchain"
            else:
                print(f"Blockchain verification result: {blockchain_result}")
                blockchain_valid = blockchain_result[0]
                
        except Exception as e:
            blockchain_error = str(e)
            print(f"Blockchain verification error: {blockchain_error}")
        
        # Certificate is valid if it exists in the database and is not revoked
        # If blockchain verification failed but database record exists, we still show the certificate
        database_valid = not certificate.is_revoked
        overall_valid = database_valid and (blockchain_valid if blockchain_result else False)
        
        response_data = {
            'certificate': CertificateSerializer(certificate).data,
            'is_valid': overall_valid,
            'blockchain_valid': blockchain_valid if blockchain_result else False,
            'database_valid': database_valid,
        }
        
        if blockchain_result:
            response_data['blockchain_details'] = {
                'student_name': blockchain_result[1],
                'course': blockchain_result[2],
                'institution': blockchain_result[3],
                'issue_date': blockchain_result[4]
            }
        
        if blockchain_error:
            response_data['failure_reason'] = blockchain_error
            response_data['note'] = "Certificate may have been issued with a different hash format. It exists in the database but couldn't be verified on the blockchain."
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Unexpected error during verification: {str(e)}")
        return Response(
            {'error': f'Unexpected error during verification: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        return JsonResponse({'token': 'your_jwt_token'})
    else:
        return JsonResponse(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def revoke_certificate_view(request, cert_hash):
    try:
        # Check if certificate exists
        certificate = Certificate.objects.get(cert_hash=cert_hash)
        
        # Attempt to revoke on blockchain
        revoke_certificate(cert_hash)
        
        # Update certificate status in database
        certificate.is_revoked = True
        certificate.save()
        
        return Response({
            'message': 'Certificate revoked successfully',
            'certificate': CertificateSerializer(certificate).data
        }, status=status.HTTP_200_OK)
    except Certificate.DoesNotExist:
        return Response(
            {'error': 'Certificate not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
