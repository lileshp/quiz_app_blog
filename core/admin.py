from django.contrib import admin
from .models import Category, Quiz, Question, Option, Attempt, Answer, Blog, Tag
from django.contrib.auth.models import User

class OptionInline(admin.TabularInline):
    model = Option
    extra = 2  # minimum 2 options
    max_num = 4

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz')
    inlines = [OptionInline]

class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_paid', 'price']
    list_filter = ['is_paid', 'category']
    search_fields = ['title']

class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'total', 'completed_at')
    list_filter = ('quiz', 'user')
    search_fields = ('user__username', 'quiz__title')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option')

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    filter_horizontal = ('tags',)  # For a better UI in admin
    search_fields = ('title', 'author__username')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)



admin.site.register(Category)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Answer, AnswerAdmin)