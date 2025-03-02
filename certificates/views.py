from django.db import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.http import JsonResponse
from .models import Certificate
from .serializers import CertificateSerializer
from .blockchain import issue_certificate, ipfs_client
from rest_framework.views import APIView
from rest_framework import status

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
        result = issue_certificate(
            request.data.get('student_name'),
            request.data.get('course'),
            request.data.get('institution'),
            request.data.get('issue_date')
        )
        
        certificate = Certificate.objects.create(
            student_name=request.data.get('student_name'),
            course=request.data.get('course'),
            institution=request.data.get('institution'),
            issue_date=request.data.get('issue_date'),
            cert_hash=result['cert_hash'],
            ipfs_hash=result.get('ipfs_hash', '')
        )
        
        serializer = CertificateSerializer(certificate)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def verify_certificate_view(request, cert_hash):
    try:
        certificate = Certificate.objects.get(cert_hash=cert_hash)
        if ipfs_client:
            ipfs_data = ipfs_client.get_json(certificate.ipfs_hash)
            return Response({
                'certificate': ipfs_data,
                'is_valid': True
            })
        else:
            serializer = CertificateSerializer(certificate)
            return Response(serializer.data)
    except Certificate.DoesNotExist:
        return Response({'error': 'Certificate not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
def admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        return JsonResponse({'token': 'your_jwt_token'})
    else:
        return JsonResponse({'error': 'Invalid credentials'}, status=400)
