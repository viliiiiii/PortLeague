from django.contrib import admin
from .models import (
    QuizQuestion, QuizScore,
    MatchPoll, PollVote
)
# Register your models here.

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'difficulty', 'points')
    list_filter = ('difficulty',)
    search_fields = ('question', 'option_a', 'option_b', 'option_c', 'option_d')

@admin.register(QuizScore)
class QuizScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'mode', 'score', 'date_achieved')
    list_filter = ('mode',)
    search_fields = ('user__username',)

@admin.register(MatchPoll)
class MatchPollAdmin(admin.ModelAdmin):
    list_display = ('home_team', 'away_team', 'match_date', 'is_closed')
    list_filter = ('is_closed',)
    search_fields = ('home_team', 'away_team')

@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'poll', 'prediction', 'is_correct')
    list_filter = ('prediction', 'is_correct')
    search_fields = ('user__username', 'poll__home_team', 'poll__away_team') 