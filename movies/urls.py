from django.contrib import admin
from django.urls import path,reverse_lazy,re_path
from django.conf.urls import include, url
from . import views
from accounts.views import (login_view, register_view, logout_view,add_review)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

app_name = 'movies'

urlpatterns = [
                  path('', views.post_list, name='home'),
                  path('loginn', login_view, name='login'),
                  path('logout', logout_view, name='logout'),
                  path('register', register_view, name='register'),
                  path('recommendation', views.recommendation, name='recommendation'),
                  path('detail/<int:id>', views.detail, name='detail'),
                  path('addreview/<int:id>',add_review,name="add_review"),
                  path('search',views.search,name="search"),
                  path('editreview/<int:review_id>',views.edit_review,name="edit_review"),
                  path('deletereview/<int:review_id>',views.delete_review,name="delete_review"),
                  re_path(r'^password_reset/$', auth_views.PasswordResetView.as_view(
                      email_template_name='registration/password_reset_email.html',
                      success_url=reverse_lazy('movies:password_reset_done'),
                      template_name= "registration/password_reset_form.html"),
                            name='password_reset'),
                  re_path(r'^password_reset/done/$', auth_views.PasswordResetDoneView.as_view(
                      template_name= "registration/password_reset_done.html"),
                            name='password_reset_done'),
                  re_path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,23})/$',
                            auth_views.PasswordResetConfirmView.as_view(
                            template_name= "registration/password_reset_confirm.html",
                            success_url=reverse_lazy('movies:password_reset_complete')
                            ),
                            name='password_reset_confirm'),
                  re_path(r'^reset/done/$', auth_views.PasswordResetCompleteView.as_view(
                             template_name= "registration/password_reset_complete.html"
                              ),
                            name='password_reset_complete')
]

if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

