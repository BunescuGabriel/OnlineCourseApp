import sys
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Sum

try:
    from django.db import models
except Exception:
    print("There was an error loading django modules. Do you have django installed?")
    sys.exit()

from django.conf import settings
import uuid


# Instructor model
class Instructor(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    full_time = models.BooleanField(default=True)
    total_learners = models.IntegerField()

    def __str__(self):
        return self.user.username


# Learner model
class Learner(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    STUDENT = 'student'
    DEVELOPER = 'developer'
    DATA_SCIENTIST = 'data_scientist'
    DATABASE_ADMIN = 'dba'
    OCCUPATION_CHOICES = [
        (STUDENT, 'Student'),
        (DEVELOPER, 'Developer'),
        (DATA_SCIENTIST, 'Data Scientist'),
        (DATABASE_ADMIN, 'Database Admin')
    ]
    occupation = models.CharField(
        null=False,
        max_length=20,
        choices=OCCUPATION_CHOICES,
        default=STUDENT
    )
    social_link = models.URLField(max_length=200)

    def __str__(self):
        return self.user.username + "," + \
               self.occupation


# Course model
class Course(models.Model):
    name = models.CharField(null=False, max_length=30, default='online course')
    image = models.ImageField(upload_to='course_images/')
    description = models.CharField(max_length=1000)
    pub_date = models.DateField(null=True)
    instructors = models.ManyToManyField(Instructor)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Enrollment')
    total_enrollment = models.IntegerField(default=0)
    is_enrolled = False
    passing_score = models.FloatField(default=0)

    def __str__(self):
        return "Name: " + self.name + "," + \
               "Description: " + self.description


# Lesson model
class Lesson(models.Model):
    title = models.CharField(max_length=200, default="title")
    order = models.IntegerField(default=0)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    content = models.TextField()
    passing_score = models.FloatField(default=0)
    

# Enrollment model
# <HINT> Once a user enrolled a class, an enrollment entry should be created between the user and course
# And we could use the enrollment to track information such as exam submissions
class Enrollment(models.Model):
    AUDIT = 'audit'
    HONOR = 'honor'
    BETA = 'BETA'
    COURSE_MODES = [
        (AUDIT, 'Audit'),
        (HONOR, 'Honor'),
        (BETA, 'BETA')
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateField(default=now)
    mode = models.CharField(max_length=5, choices=COURSE_MODES, default=AUDIT)
    rating = models.FloatField(default=5.0)
    started_test = models.BooleanField(default=False)
    progress = models.FloatField(default=0.0)

# <HINT> Create a Question Model with:
# Used to persist question content for a course
# Has a One-To-Many (or Many-To-Many if you want to reuse questions) relationship with course
# Has a grade point for each question
# Has question content
# Other fields and methods you would like to design
class Question(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    question_text = models.TextField()
    grade = models.FloatField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')  # Adăugați acest câmp

    def calculate_score(self, selected_choice_ids):
        correct_choices = self.choice_set.filter(is_correct=True, id__in=selected_choice_ids).count()
        total_choices = self.choice_set.filter(id__in=selected_choice_ids).count()
        if total_choices == 0:
            return 0
        return (correct_choices / total_choices) * self.grade



# <HINT> Create a Choice Model with:
# Used to persist choice content for a question
# One-To-Many (or Many-To-Many if you want to reuse choices) relationship with Question
# Choice content
# Indicate if this choice of the question is a correct one or not
# Other fields and methods you would like to design
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.TextField()
    is_correct = models.BooleanField(default=False)


# <HINT> The submission model
# One enrollment could have multiple submissions
# One submission could have multiple choices
# One choice could belong to multiple submissions
class Submission(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    choices = models.ManyToManyField(Choice)  # Many-To-Many with Choice
    timestamp = models.DateTimeField(default=timezone.now)
    feedback = models.TextField(blank=True, null=True)
    final_grade = models.FloatField(default=0)

    def calculate_final_grade(self):
        lessons = self.enrollment.course.lesson_set.all()
        total_max_grade = Question.objects.filter(lesson__in=lessons).aggregate(Sum('grade'))['grade__sum']
        if total_max_grade and total_max_grade > 0:
            total_score = self.calculate_total_score()
            final_grade = (total_score / total_max_grade) * 10.0
            # Normalize the final grade to be between 0 and 10
            final_grade = min(10, final_grade)
            return final_grade
        return 0.0

    def calculate_total_score(self):
        total_score = 0
        for question in self.enrollment.course.questions.all():
            selected_choice_ids = self.choices.filter(question=question).values_list('id', flat=True)
            score = question.calculate_score(selected_choice_ids)
            total_score += score
        return total_score

    def is_complete(self):
        lessons = self.enrollment.course.lesson_set.all()
        required_questions = Question.objects.filter(lesson__in=lessons)
        answered_questions = self.choices.values_list('question__id', flat=True).distinct()
        return set(required_questions.values_list('id', flat=True)) == set(answered_questions)

    def update_progress(self):
        lessons = self.enrollment.course.lesson_set.all()
        total_questions = Question.objects.filter(lesson__in=lessons).count()
        answered_questions = self.choices.count()
        if total_questions > 0:
            progress = (answered_questions / total_questions) * 100
            self.enrollment.progress = progress
            self.enrollment.save()


#    Other fields and methods you would like to design?