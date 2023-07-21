from django.contrib import admin
from .models import Course, Lesson, Instructor, Learner, Question, Choice, Submission

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
    list_display = ('name', 'pub_date', 'instructor_names')  # Update the method name here
    list_filter = ['pub_date']
    search_fields = ['name', 'description']

    def instructor_names(self, obj):  # Update the method name here
        instructor_names = ', '.join([instructor.user.get_full_name() for instructor in obj.instructors.all()])
        return instructor_names

    instructor_names.short_description = 'Instructors' 



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


class SubmissionAdmin(admin.ModelAdmin):
    def learner_username(self, obj):
        return obj.enrollment.user.username

    learner_username.short_description = 'Enrolled User'

    def learner_full_name(self, obj):
        learner = obj.enrollment.user.learner
        return f"{learner.user.first_name} {learner.user.last_name}"

    learner_full_name.short_description = 'Enrolled Full Name'

    def course_and_lesson(self, obj):
        course_name = obj.enrollment.course.name
        lesson_order = obj.enrollment.lesson.order + 1
        return f"{course_name} - Lesson {lesson_order}"

    def user_full_name(self, obj):
        return f"{obj.enrollment.user.first_name} {obj.enrollment.user.last_name}"

    user_full_name.short_description = 'User Full Name'

    def save_model(self, request, obj, form, change):
        # Before saving the submission, update the learner's progress
        obj.update_progress()

        # Set the final grade based on the calculated final_grade attribute of the object
        obj.final_grade = obj.final_grade

        # Save the object
        super().save_model(request, obj, form, change)

    def is_complete(self, obj):
        return obj.is_complete()

    is_complete.boolean = True

    def user_has_started_test(self, obj):
        return obj.enrollment.started_test

    user_has_started_test.boolean = True
    user_has_started_test.short_description = 'Test Started'

    def delete_selected_submissions(self, request, queryset):
        # Delete the selected submissions
        queryset.delete()

    delete_selected_submissions.short_description = 'Delete selected submissions'

    list_display = ['course_and_lesson', 'user_full_name', 'timestamp', 'is_complete', 'final_grade', 'feedback', 'user_has_started_test']
    list_filter = ['timestamp', 'enrollment__course']

    # Add the action method to the actions attribute
    actions = [delete_selected_submissions]


# Register all models
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Submission, SubmissionAdmin)
