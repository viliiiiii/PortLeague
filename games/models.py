from django.db import models
from django.contrib.auth.models import User
from core.models import Team

# Create your models here.

class QuizQuestion(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ]
    
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )
    points = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.get_difficulty_display()}: {self.question[:50]}..."

class MatchPoll(models.Model):
    match_id = models.IntegerField(unique=True)
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    home_team_crest = models.URLField(max_length=500, null=True, blank=True)
    away_team_crest = models.URLField(max_length=500, null=True, blank=True)
    match_date = models.DateTimeField()
    is_closed = models.BooleanField(default=False)
    correct_outcome = models.CharField(
        max_length=10,
        choices=[
            ('HOME', 'Home Win'),
            ('DRAW', 'Draw'),
            ('AWAY', 'Away Win')
        ],
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['match_date']

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.match_date.strftime('%Y-%m-%d')})"

    def get_vote_counts(self):
        """Returns a dictionary with the count of votes for each outcome"""
        votes = self.votes.all()
        return {
            'HOME': votes.filter(prediction='HOME').count(),
            'DRAW': votes.filter(prediction='DRAW').count(),
            'AWAY': votes.filter(prediction='AWAY').count()
        }

    def total_votes(self):
        """Returns the total number of votes for this poll"""
        return self.votes.count()

    def user_has_voted(self, user):
        """Check if a user has already voted on this poll"""
        return self.votes.filter(user=user).exists() if user.is_authenticated else False

class PollVote(models.Model):
    poll = models.ForeignKey(MatchPoll, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    prediction = models.CharField(
        max_length=10,
        choices=[
            ('HOME', 'Home Win'),
            ('DRAW', 'Draw'),
            ('AWAY', 'Away Win')
        ]
    )
    is_correct = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['poll', 'user']  # Ensure one vote per user per poll
        ordering = ['-created_at']

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str}'s prediction for {self.poll}"

class QuizScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_scores')
    mode = models.CharField(max_length=10, choices=[('regular', 'Regular'), ('hard', 'Hard')])
    score = models.FloatField()
    date_achieved = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'mode')
        ordering = ['-score']

    def __str__(self):
        return f"{self.user.username}'s {self.mode} quiz score: {self.score}%"