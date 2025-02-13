from django import forms
from .models import QuizQuestion

class QuizForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["answer"] = forms.ChoiceField(
            choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
            widget=forms.RadioSelect,
            label="Your Answer"
        )
