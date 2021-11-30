from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from .views import WeatherDataParse

urlpatterns = [
        url(r'^weather-parse/$',
            csrf_exempt(WeatherDataParse.as_view()),
            name='weather-parse-get-post')
        ]