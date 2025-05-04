from django.http import JsonResponse


CREATE_STATUS_CODE = 201
SUCCESS_STATUS_CODE = 200
ERROR_STATUS_CODE = 400
ERROR_STATUS_CODE_FORBIDDEN = 403
ERROR_STATUS_CODE_CONFLICT = 409
ERROR_STATUS_CODE_NOT_FOUND = 404
INTERNAL_SERVER_ERROR_STATUS_CODE = 500
OTP_EXPIRED= 400
class Response(object):

    @staticmethod
    def create(created_response="created"):
        return JsonResponse({"description": created_response}, status=CREATE_STATUS_CODE)

    @staticmethod
    def create_data(created_data_response, status=SUCCESS_STATUS_CODE):
        return JsonResponse({"data": created_data_response}, status=status)

    @staticmethod
    def success(success_response="success"):
        return JsonResponse({"description": success_response}, status=SUCCESS_STATUS_CODE)

    @staticmethod
    def success_data(success_data_response):
        return JsonResponse({"data": success_data_response}, status=SUCCESS_STATUS_CODE)



    @staticmethod
    def error_login(error_response="error", wrong_attempts="", status=ERROR_STATUS_CODE):
        return JsonResponse({"description": error_response, "wrong_attempts": wrong_attempts,
                             "error": 1}, status=status)

   
    @staticmethod
    def error(error_response, status=400):
        """
        Returns an error response with the provided description and status code.
        """
        return JsonResponse(
            {"description": error_response, "status": status},
            status=status
        )

    @staticmethod
    def internal_server_error(error_response="An error occurred"):
        """
        Returns a 500 internal server error response.
        """
        return JsonResponse(
            {"description": error_response, "status": 500},
            status=500
        )


