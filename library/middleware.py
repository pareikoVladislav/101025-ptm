class JWTFromCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Если заголовка Authorization нет, но есть кука access_token
        if 'HTTP_AUTHORIZATION' not in request.META and 'access_token' in request.COOKIES:
            access_token = request.COOKIES['access_token']

            # ЗАЩИТА: Если кука по какой-то причине прилетела в виде кортежа/списка, берем первый элемент
            if isinstance(access_token, (tuple, list)):
                if len(access_token) > 0:
                    access_token = access_token[0]
                else:
                    access_token = None

            if access_token:
                # Маскируемся под стандартный Bearer токен
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

        response = self.get_response(request)
        return response