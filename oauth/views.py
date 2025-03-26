from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status,generics
from .serializers import *
from users. models import  User
class GoogleSocialAuthView(generics.GenericAPIView):
    serializer_class = GoogleSocialAuthSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        return Response(validated_data, status=status.HTTP_200_OK)
