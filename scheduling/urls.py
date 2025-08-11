from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'skills', views.SkillViewSet, basename='skill')
router.register(r'timeslots', views.TimeSlotViewSet, basename='timeslot')
router.register(r'meetings', views.MeetingViewSet, basename='meeting')
router.register(r'proposals/my', views.MyProposalsViewSet, basename='my-proposal')
router.register(r'proposals/respond', views.RespondToProposalViewSet, basename='reschedule-proposal')
router.register(r'whats-on-now', views.WhatsOnNowViewSet, basename='whats-on-now')
router.register(r'public-profiles', views.PublicProfileViewSet, basename='public-profile')
router.register(r'admin/users', views.UserAdminViewSet, basename='user-admin')
router.register(r'leaderboard', views.LeaderboardViewSet, basename='leaderboard')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('profile/', views.ProfileView.as_view(), name='user-profile'),
    path('profile/clear-interests/', views.ClearInterestsView.as_view(), name='user-profile-clear-interests'),
    path('profile/snooze/', views.SnoozeNotificationsView.as_view(), name='user-profile-snooze'),
    path('profile/unsnooze/', views.UnSnoozeNotificationsView.as_view(), name='user-profile-unsnooze'),
    path('stats/my/', views.MyStatsView.as_view(), name='my-stats'),
    path('matches/recommended/', views.RecommendedMatchesView.as_view(), name='recommended-matches'),
    path('feed/my/', views.MyEventFeedView.as_view(), name='my-feed'),
    path('summary/my/', views.MyEventSummaryView.as_view(), name='my-summary'),
    path('meetings/<int:pk>/feedback/', views.MeetingFeedbackViewSet.as_view({'get': 'list', 'post': 'create'}), name='meeting-feedback'),
]