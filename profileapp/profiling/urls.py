# yourapp/urls.py
from django.urls import path
from . import views
from profiling.admin_views import skills_chart, export_skills_to_pdf, export_specializations_to_pdf, specialization_chart, profile_chart_view, gender_chart_view, region_chart_view, province_chart_view, barangay_chart_view, city_chart_view
from . import api_views
from . import admin_views
from .views import handler404 as custom_404, handler500 as custom_500
from .views import handler403 as custom_403, handler400 as custom_400




urlpatterns = [
    path("", views.index, name="index"),

        
    path('password_reset/', views.password_reset_request, name='password_reset'),

    path('password_reset_done/', views.password_reset_done, name='password_reset_done'),

    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),

    path('about-us/', views.about_us, name='about_us'),

    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    
    path('freelancer/about-us/', views.about_us_logined, name='about_us_logined'),

    path('freelancer/privacy-policy/', views.privacy_policy_logined, name='privacy_policy_logined'),

    path('announcement/guest', views.guest_announcement, name='guest_announcement'),

    path('otp-verification/', views.otp_verification, name='otp_verification'),

    path('resend-otp/', views.resend_otp, name='resend_otp'),

    path('announcement/guest/<int:ann_id>/', views.guest_announcement_view, name='guest_announcement_view'),

    path('events/guest/', views.guest_event, name='guest_event_all'),

    path('events/guest/<int:event_id>/', views.guest_event_attendance, name='guest_event'),

    path('signup', views.create_account, name="create_account"),

    path('create-profile/', views.create_profile, name='create_profile'),

    path('activate/<int:account_id>/', views.activate_account, name='activate_account'),

    path('account/<int:account_id>/', views.account_status, name='account_status'),

    path('login/', views.user_login, name='user_login'),
    
    path('get_provinces/', views.get_provinces, name='get_provinces'),

    path('get_cities/', views.get_cities, name='get_cities'),

    path('get_barangays/', views.get_barangays, name='get_barangays'),

    path('get_all_countries/', views.get_all_countries, name='get_all_countries'),

    path('get_languages/', views.get_languages,  name='get_languages'),

    path('get_skills/', views.get_skills,  name='get_skills'),

    path('create_profile_step/', views.create_profile_step, name='create_profile_step'),
    
    path('finish-registration/', views.finish_registration, name='finish_registration'),

    path('profile/', views.profile_detail, name='profile_detail'),

    path('logout', views.logout_view, name='logout'),

    path('profile/page/', views.profile_page,  name='profile_page'),
    
    path('profile/announcement/', views.announcement_view, name='announcement'),
    
    path('project/pdf_preview/<int:project_id>/', api_views.pdf_preview, name='pdf_preview'),
    
    path('languages/update/<int:language_id>/', views.update_language_view, name='update_language_view'),

    path('add-experience/', views.add_experience_view, name='add_experience'),  # URL for adding new experience
    # path('profile/portofolio/<int:account_id>', views.portfolio_view, name='portfolio_view'),
    path('certificates/', views.certificates_view, name='certificates_view'),

    path('add-project/', views.add_project, name='add_project'),

    path('project/update/<int:project_id>/', views.update_project, name='update_project'),
    
    path('update_projects/', views.update_projects_view, name='update_projects'),
    
    path('skills/', views.skills_view, name='skills_view'),

    path('languages/', views.languages_view, name='languages_view'),    

    path('experiences/', views.experiences_view, name='experiences_view'),
    
    path('edit-certificate/<int:certificate_id>/', views.edit_certificate_view, name='edit_certificate'),

    path('update_resume/<int:resume_id>/<int:account_id>/', views.update_resume_view, name='update_resume'),    

    path('edit_profile/<int:account_id>/', views.edit_profile, name='edit_profile'),

    path('update_account/', views.update_account, name='update_account'),

    path('profile/events/', views.event_view, name='event'),

    path('add-certificate/', views.add_certificate_view, name='add_certificate'),

    path('profile/events/<int:event_id>/', views.event_detail_view, name='event_detail_view'),

    path('announcement/<int:account_id>/tag/<int:tag_id>/', views.tag_filter_view, name='tag_filter_view'),

    path('announcement/<int:announcement_id>/', views.announcement_detail, name='announcement_detail'),

    path('notification/read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),

    path('notifications/', views.notification_page, name='notification_page'),
    
    path('events/tag/<int:tag_id>/account/<int:account_id>/', views.tag_filter_event_view, name='tag_filter_event_view'),   

    path('admin/skills-chart/', skills_chart, name='skills-chart'),

    path('admin/skills_chart/export/pdf/', export_skills_to_pdf, name='export_skills_to_pdf'),

    path('admin/specialization-chart/', specialization_chart, name='specialization_chart'),

    path('admin/export-specializations-to-pdf/', export_specializations_to_pdf, name='export_specializations_to_pdf'),

    path('api/freelancer_count/', api_views.get_freelancer_count, name='get_freelancer_count'),

    path('admin/profile-charts/', profile_chart_view, name='profile_charts'),

    path('admin/profile-charts/gender/', gender_chart_view, name='gender_chart'),

    path('admin/profile-charts/region/', region_chart_view, name='region_chart'),

    path('admin/profile-charts/province/', province_chart_view, name='province_chart'),
    
    path('admin/profile-charts/city/', city_chart_view, name='city_chart'),

    path('admin/export-gender-chart-to-pdf/', admin_views.export_gender_chart_to_pdf, name='export_gender_chart_to_pdf'),

    path('admin/profile-charts/barangay/', barangay_chart_view, name='barangay_chart'),

    path('admin/export-region-chart-to-pdf/', admin_views.export_region_chart_to_pdf, name='export_region_chart_to_pdf'),

    path('admin/export-province-chart-to-pdf/', admin_views.export_province_chart_to_pdf, name='export_province_chart_to_pdf'),

    path('admin/export-city-chart-to-pdf/', admin_views.export_city_chart_to_pdf, name='export_city_chart_to_pdf'),

    path('admin/export-barangay-chart-to-pdf/', admin_views.export_barangay_chart_to_pdf, name='export_barangay_chart_to_pdf'),

    path('admin/export-profile-chart-to-pdf/', admin_views.export_profile_chart_to_pdf, name='export_profile_chart_to_pdf'),    

    path('admin/language-chart/', admin_views.language_chart, name='language_chart'),

    path('admin/export-languages-to-pdf/', admin_views.export_languages_to_pdf, name='export_languages_to_pdf'),

    path('admin/past-experience-chart/', admin_views.past_experience_chart, name='past_experience_chart'),

    path('admin/export-past-experiences-to-pdf/', admin_views.export_past_experiences_to_pdf, name='export_past_experiences_to_pdf'),

    path('api/bgy-freelancer-count/', api_views.get_freelancer_count_per_barangay, name='get_freelancer_count_per_barangay'),

    path('api/bgy-dominant-details/', api_views.get_dominant_details_per_barangay, name='get_dominant_details_per_barangay'),

    path('get_languages_and_skills/', api_views.get_languages_and_skills, name='get_languages_and_skills'),

    path('api/events/', api_views.events_api, name='events_api'),

    path('barangay/<str:barangay_name>/', api_views.barangay_breakdown, name='barangay_breakdown'),

    path('admin/profile/<int:profile_id>/', admin_views.admin_profile_detail, name='admin_profile_detail'),

    path('filter_skills_by_tags/', api_views.filter_skills_by_tags, name='filter_skills_by_tags'),

    path('admin/event-chart/', admin_views.event_chart_view, name='event_chart'),

    path('events/attended/', views.event_attended_view, name='event_attended_view'),

    path('export_event_age_report_pdf/', admin_views.export_event_age_report_pdf, name='export_event_age_report_pdf'),

    path('help/', views.create_ticket, name='help'),
    
    path('help/ticket/<int:ticket_id>/', views.view_ticket, name='view_ticket'),

    path('api/latest-messages/', api_views.latest_tickets_with_message, name='latest_tickets_with_message'),

    path('api/barangay-breakdown/', api_views.index_barangay_breakdown, name='barangay_breakdown'),

    path('event-statistics/', api_views.latest_event_statistics, name='latest_event_statistics'),

    path('admin/event_statistics/<int:event_id>/', admin_views.render_event_statistics, name='render_event_statistics'),

    path('admin/event_statistics/data/<int:event_id>/', api_views.event_statistics, name='event_statistics'),  # For API data

    path('api/overall_event_statistics/', api_views.overall_event_statistics, name='overall_event_statistics'),

    path('api/unread-messages/', api_views.unread_messages_count, name='unread_messages_count'),

    path('api/mark-messages-read/<int:ticket_id>/', api_views.mark_messages_as_read, name='mark_messages_as_read'),

    path('api/add-message/<int:ticket_id>/', api_views.add_message_to_conversation, name='add_message_to_conversation'),

    path('notifications/mark_all_as_read/', api_views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),

    path('export-skills-excel/', admin_views.export_skills_to_excel, name='export_skills_to_excel'),

    path('export-specializations-excel/', admin_views.export_specializations_to_excel, name='export_specializations_to_excel'),
    
    path('export-profile-chart-excel/', admin_views.export_profile_chart_to_excel, name='export_profile_chart_to_excel'),

    path('export-gender-chart-excel/', admin_views.export_gender_chart_to_excel, name='export_gender_chart_to_excel'),

    path('export-region-chart-excel/', admin_views.export_region_chart_to_excel, name='export_region_chart_to_excel'),

    path('export-province-chart-excel/', admin_views.export_province_chart_to_excel, name='export_province_chart_to_excel'),

    path('export-city-chart-excel/', admin_views.export_city_chart_to_excel, name='export_city_chart_to_excel'),

    path('export-barangay-chart-excel/', admin_views.export_barangay_chart_to_excel, name='export_barangay_chart_to_excel'),

    path('export-language-chart-excel/', admin_views.export_language_chart_to_excel, name='export_language_chart_to_excel'),

    path('export-event-chart-excel/', admin_views.export_event_chart_to_excel, name='export_event_chart_to_excel'),

    path('export-event-statistics-excel/<int:event_id>/', admin_views.export_event_statistics_excel, name='export_event_statistics_excel'),

    path('offline/', views.offline, name='offline'),

    path('profile/edit/<int:df_id>/', views.edit_resume_and_projects, name='edit_resume_projects'),

    path('api/events/count/', api_views.event_count_api, name='event_count_api'),

    path('api/unverified-users/', api_views.unverified_users_count, name='unverified-users-api'),

    path('api/admin-notifications/', api_views.admin_latest_notifications, name='admin_latest_notifications'),

    path('api/admin-notifications/read/<int:notif_id>/',  api_views.MarkSingleNotificationReadView.as_view(), name='mark_notification_read'),

    path('api/admin-notifications/read/', api_views.MarkAllReadView.as_view(), name='admin_notifications_read'),

]


handler404 = custom_404
handler500 = custom_500
handler403 = custom_403
handler400 = custom_400