"""archivemanager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from filemanagement.views import upload_file, unpack_zip, download_file, download_video, download_archive, delete_info, \
    download_protected_archive
from loginwindow.views import login_page, redirect_to_filemanager
from simpleuserpage.views import show_archive_data, edit_info, admin_panel, edit_user_info, delete_user, \
    add_user, search, sort_table, video_player, video_streaming, update_unpacking_progress, link_access_archive, \
    download_pdf, show_mir_archives

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_filemanager, name='main_page_redirect'),
    path('accounts/login', login_page, name='login_page'),
    path('simpleuser/', show_archive_data, name='simpleuser_page'),
    path('simpleuser/mir-conferences/', show_mir_archives, name='mir_page'),
    path('simpleuser/search/', search, name='search_result'),
    path('simpleuser/administration/', admin_panel, name='admin_panel'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('simpleuser/<int:id>/edit', edit_info, name='edit_info'),
    path('simpleuser/administration/<int:id>/edit_user', edit_user_info, name='edit_user_info'),
    path('simpleuser/administration/add_user', add_user, name='add_user'),
    path('simpleuser/<int:id>/delete_user', delete_user, name='delete_user'),
    path('simpleuser/<int:id>/delete', delete_info, name='delete_info'),
    path('simpleuser/download/<int:id>/', download_archive, name='download_archive'),
    path('simpleuser/download-video/<int:id>/', download_video, name='download_video'),
    path('simpleuser/download-protected-archive/<int:id>/', download_protected_archive,
         name='download_protected_archive'),
    path('simpleuser/download-file/<int:id>/<str:handout>/', download_file, name='download_file'),
    path('simpleuser/<int:id>/', unpack_zip, name='unpack_archive'),
    path('simpleuser/sort/<str:field>/', sort_table, name='sort_table'),
    path('simpleuser/upload/<int:id>/', upload_file, name='upload_file'),
    path('video/<int:id>/', video_player, name='video_player'),
    path('stream/<int:id>/', video_streaming, name='stream'),
    path('update_info/', update_unpacking_progress, name='update_unpacking_progress'),
    path('free-access/link-access/<int:id>', link_access_archive, name='link_access_archive'),
    path('simpleuser/instruction/<str:instruction>', download_pdf, name='download_pdf'),
]
