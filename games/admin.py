from django.contrib import admin
from .models import QuizQuestion
# Register your models here.

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "correct_answer")  # Customize the admin view