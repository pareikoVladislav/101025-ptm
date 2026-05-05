from django.http import HttpRequest, HttpResponse


def greetings(request: HttpRequest) -> HttpResponse:
    return HttpResponse("HELLO FROM OUR FIRST VIEW!!!!!")
