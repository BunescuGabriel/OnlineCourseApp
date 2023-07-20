from click import Choice
from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Lesson, Question, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        enrollment = Enrollment.objects.create(user=user, course=course, mode='honor')

        # Assign a lesson to the enrollment (you can set this based on your logic)
        # For example, if you want to assign the first lesson in the course:
        first_lesson = course.lesson_set.first()
        if first_lesson:
            enrollment.lesson = first_lesson
            enrollment.save()

        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
         # Get user and course object, then get the associated enrollment object created when the user enrolled the course
         # Create a submission object referring to the enrollment
         # Collect the selected choices from exam form
         # Add each selected choice object to the submission object
         # Redirect to show_exam_result with the submission id

         
# def submit(request, course_id):
#     user = request.user
#     course = get_object_or_404(Course, id=course_id)
#     enrollment = get_object_or_404(Enrollment, user=user, course=course)
    
#     if request.method == 'POST':
#         submission = Submission.objects.create(enrollment=enrollment)
#         selected_choice_ids = request.POST.getlist('selected_choices')
#         correct_choices = 0
        
#         for choice_id in selected_choice_ids:
#             try:
#                 choice = Choice.objects.get(id=choice_id)
#                 submission.choices.add(choice)
#                 if choice.is_correct:
#                     correct_choices += 1
#             except Choice.DoesNotExist:
#                 pass

#         return render(request, 'exam_result.html', {'course': course, 'submission': submission, 'correct_choices': correct_choices})

#     return render(request, 'exam_form.html', {'course': course})    
 
def exam_form(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    questions = Question.objects.filter(course=course)

    return render(request, 'exam_form.html', {'course': course, 'questions': questions})
        
# # <HINT> A example method to collect the selected choices from the exam form from the request object
# def extract_answers(request):
#    submitted_anwsers = []
#    for key in request.POST:
#        if key.startswith('choice'):
#            value = request.POST[key]
#            choice_id = int(value)
#            submitted_anwsers.append(choice_id)
#    return submitted_anwsers

# # <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# # you may implement it based on the following logic:
#         # Get course and submission based on their ids
#         # Get the selected choice ids from the submission record
#         # For each selected choice, check if it is a correct answer or not
#         # Calculate the total score

# def show_exam_result(request, course_id, submission_id):
#     course = get_object_or_404(Course, id=course_id)
#     submission = get_object_or_404(Submission, id=submission_id)
    
#     selected_choice_ids = submission.choices.values_list('id', flat=True)
    
#     total_score = 0
#     for choice_id in selected_choice_ids:
#         try:
#             choice = submission.choices.get(id=choice_id)
#             if choice.is_correct:
#                 total_score += choice.question.grade
#         except submission.choices.model.DoesNotExist:
#             pass

#     passing_score = course.passing_score 
#     passed_exam = total_score >= passing_score

#     return render(request, 'exam_result.html', {
#         'course': course,
#         'submission': submission,
#         'total_score': total_score,
#         'passed_exam': passed_exam,
#     })

#####################
# def submit(request, course_id):
#     # Get the user object from the request
#     user = request.user

#     # Get the course object based on the course_id
#     course = get_object_or_404(Course, id=course_id)

#     # Get the enrollment object for the user and course
#     enrollment = get_object_or_404(Enrollment, user=user, course=course)

#     if request.method == 'POST':
#         # Create a new submission object and associate it with the enrollment
#         submission = Submission.objects.create(enrollment=enrollment)

#         # Collect the selected choices from the exam form
#         selected_choice_ids = request.POST.getlist('selected_choices')

#         # Add each selected choice to the submission object
#         for choice_id in selected_choice_ids:
#             choice = get_object_or_404(Choice, id=choice_id)
#             submission.choices.add(choice)

#         # Update the progress for the enrollment based on the new submission
#         submission.update_progress()

#         # Redirect to a view to show the exam result with the submission id
#         return redirect('show_exam_result', submission_id=submission.id)

#     # If it's not a POST request, render the exam form for the user to submit
#     # Here, you would need to create a template with the exam form containing the available choices for the questions.
#     # The form should have checkboxes or radio buttons to allow the user to select their choices.

#     return render(request, 'exam_form.html', {'course': course})

    

# def exam_form(request, course_id):
#     course = get_object_or_404(Course, id=course_id)
#     lessons = Lesson.objects.filter(course=course)
#     questions = Question.objects.filter(lesson__in=lessons)

#     return render(request, 'exam_form.html', {'course': course, 'questions': questions})


# def show_exam_result(request, submission_id):
#     submission = get_object_or_404(Submission, id=submission_id)
#     total_score = 0
#     question_results = []

#     for question in submission.enrollment.course.question_set.all():
#         selected_choice_ids = submission.choices.filter(question=question).values_list('id', flat=True)
#         score = question.calculate_score(selected_choice_ids)
#         total_score += score
#         question_results.append({
#             'question_text': question.question_text,
#             'score': score,
#             'total_score': question.grade,
#             'selected_choices': question.choice_set.filter(id__in=selected_choice_ids),
#         })

#     passing_score = submission.enrollment.course.passing_score
#     passed_exam = total_score >= passing_score

#     return render(request, 'exam_result.html', {
#         'submission': submission,
#         'total_score': total_score,
#         'question_results': question_results,
#         'passed_exam': passed_exam,
#     })
    
# def extract_answers(request):
#     submitted_answers = []
#     for key in request.POST:
#         if key.startswith('selected_choices_'):
#             value = request.POST[key]
#             choice_id = int(value)
#             submitted_answers.append(choice_id)
#     return submitted_answers
##################

# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
# Get user and course object, then get the associated enrollment object created when the user enrolled the course
# Create a submission object referring to the enrollment
# Collect the selected choices from exam form
# Add each selected choice object to the submission object
# Redirect to show_exam_result with the submission id

def submit(request, course_id):
    user = request.user
    course = get_object_or_404(Course, id=course_id)

    try:
        enrollment = Enrollment.objects.get(user=user, course=course)
    except Enrollment.DoesNotExist:
        # Handle the case where the user is not enrolled in the course
        return redirect('enroll_in_course', course_id=course_id)

    if request.method == 'POST':
        submission = Submission.objects.create(enrollment=enrollment)
        selected_choice_ids = extract_answers(request)

        for choice_id in selected_choice_ids:
            choice = get_object_or_404(Choice, id=choice_id)
            submission.choices.add(choice)

        submission.update_progress()

        return redirect('show_exam_result', submission_id=submission.id)

    questions = Question.objects.filter(lesson__course=course)
    return render(request, 'exam_form.html', {'course': course, 'questions': questions})


def extract_answers(request):
    submitted_answers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_answers.append(choice_id)
    return submitted_answers


# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
# Get course and submission based on their ids
# Get the selected choice ids from the submission record
# For each selected choice, check if it is a correct answer or not
# Calculate the total score

def show_exam_result(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    total_score = 0
    question_results = []

    for question in submission.enrollment.course.question_set.all():
        selected_choice_ids = submission.choices.filter(question=question).values_list('id', flat=True)
        score = question.calculate_score(selected_choice_ids)
        total_score += score
        question_results.append({
            'question_text': question.question_text,
            'score': score,
            'total_score': question.grade,
            'selected_choices': question.choice_set.filter(id__in=selected_choice_ids),
        })

    passing_score = submission.enrollment.course.passing_score
    passed_exam = total_score >= passing_score

    return render(request, 'exam_result.html', {
        'submission': submission,
        'total_score': total_score,
        'question_results': question_results,
        'passed_exam': passed_exam,
    })




