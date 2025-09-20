from user.serializers import (
    UserRegisterSerializer, UserVerifySerializer
)
from user.view_container import (
    sent_mail_verification, status,
    User, Response, AppStatus, TypeEmailEnum,
    GenericAPIView, AllowAny
)


class RegisterViewSet(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            sent_mail_verification(user, TypeEmailEnum.REGISTER)
            return Response(AppStatus.SEND_MAIL_SUCCESS.message)
        else:
            user = User.objects.filter(email=serializer.data['email']).first()
            if user and not user.is_active:
                user.set_password(serializer.data['password'])
                user.full_name = serializer.data['full_name']
                user.save()
                sent_mail_verification(user, TypeEmailEnum.REGISTER)
                return Response(AppStatus.SEND_MAIL_SUCCESS.message)
            return Response(serializer.errors)


class VerifyCodeViewSet(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserVerifySerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def put(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.update(instance=None, validated_data=serializer.validated_data)
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
