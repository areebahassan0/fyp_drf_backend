import jwt
from rest_framework_simplejwt.tokens import RefreshToken
from fyp.settings import SECRET_KEY
from user.models import User  # Adjust the import path based on your project structure

class PewBillJWT:

    def __init__(self):
        self.name = "PewBillJWT"

    def create_jwt(self, user):
        """
        Creates a JWT and Refresh token for a user.
        """
        encoded_token = RefreshToken.for_user(user)
        access_token = str(encoded_token.access_token)
        encoded_token['consumer_no'] = user.consumer_no  # Replace with the primary key field
        encoded_token['name'] = user.name
        return access_token, str(encoded_token)

    def parse_token(self, token):
        """
        Decodes and verifies a JWT token.
        """
        try:
            token = token.split(" ")[1]  # Remove 'Bearer' if present
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS512"])
            user_id = decoded_token['id']
            return user_id, decoded_token
        except (jwt.ExpiredSignatureError, jwt.DecodeError, jwt.InvalidTokenError):
            return None, {}

    def check_token(self, user_id, token):
        """
        Checks if a token exists for a given user.
        """
        try:
            user = User.objects.get(pk=user_id)
            return user.jwt_token == token
        except User.DoesNotExist:
            return False
