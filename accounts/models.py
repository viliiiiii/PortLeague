from django.contrib.auth.models import User
from django.db import models
from core.models import Team

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favorite_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

class UserStatistics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_quizzes = models.IntegerField(default=0)
    avg_accuracy = models.FloatField(default=0)
    avg_response_time = models.FloatField(default=0)
    hard_mode_completed = models.IntegerField(default=0)
    normal_mode_completed = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "User Statistics"
    
    def __str__(self):
        return f"{self.user.username}'s Statistics"