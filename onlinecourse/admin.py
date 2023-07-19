from django.contrib import admin
from .models import Course, Lesson, Instructor, Learner, Question, Choice

# Register the LessonInline for Course
class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5


# Register the QuestionInline for Lesson
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


# Register the ChoiceInline for Question
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


# Register CourseAdmin
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('name', 'pub_date')
    list_filter = ['pub_date']
    search_fields = ['name', 'description']


# Register LessonAdmin
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title']
    inlines = [QuestionInline]


# Register QuestionAdmin
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text']


# Register ChoiceAdmin
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text', 'is_correct']


# Register all models
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
