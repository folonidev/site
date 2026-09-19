from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('encurtador/', views.shortener, name='shortener'),
    path('e/<str:short_code>/', views.follow_short_url, name='follow_short_url'),
    path('blog/', views.blog, name='blog'),
    path('portfolio/', views.portfolio, name='portfolio'),
]
