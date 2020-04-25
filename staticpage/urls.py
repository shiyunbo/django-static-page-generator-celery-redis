from django.urls import path, re_path
from . import views


urlpatterns = [

    # Create a page
    path('', views.page_create, name='page_create'),

    # Page detail
    re_path(r'^page/(?P<pk>\d+)/$', views.page_detail, name='page_detail'),

    ]