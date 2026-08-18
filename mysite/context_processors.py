from django.conf import settings


def react_web_url(request):
    """Base URL of the new React web app, used by the transitional 'New UI' sidebar links."""
    return {'react_web_url': settings.REACT_WEB_URL}
