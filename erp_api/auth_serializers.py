from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Extra claims inside JWT
        token['userid'] = user.id
        token['username'] = user.username
        token['email'] = user.email
        token['groups'] = list(user.groups.values_list('name', flat=True))
        token['role'] = getattr(user, 'role', None)

        return token

    def validate(self, attrs):
        data = super().validate(attrs)  # includes refresh & access
        user = self.user

        # Add extra fields to response body
        data['userid'] = user.id
        data['username'] = user.username
        data['email'] = user.email
        groups = list(user.groups.values_list('name', flat=True))
        data['groups'] = groups
        data['role'] = getattr(user, 'role', groups[0] if groups else 'user')

        return data
