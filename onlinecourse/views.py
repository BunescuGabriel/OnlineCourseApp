from ipaddress import summarize_address_range
from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Choice, Lesson, Question, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
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

# def enroll(request, course_id):
#     course = get_object_or_404(Course, pk=course_id)
#     user = request.user

#     is_enrolled = check_if_enrolled(user, course)
#     if not is_enrolled and user.is_authenticated:
#         # Create an enrollment
#         Enrollment.objects.create(user=user, course=course, mode='honor')
#         course.total_enrollment += 1
#         course.save()

#     return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))

def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        enrollment = Enrollment.objects.create(user=user, course=course, mode='honor')

        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))



# @login_required
# def enroll(request, course_id, lesson_id):
#     course = get_object_or_404(Course, pk=course_id)
#     user = request.user

#     is_enrolled = check_if_enrolled(user, course)
#     if not is_enrolled and user.is_authenticated:
#         # Create an enrollment
#         enrollment = Enrollment.objects.create(user=user, course=course, mode='honor')

#         # Get the lesson associated with the lesson_id
#         lesson = get_object_or_404(Lesson, pk=lesson_id)
#         enrollment.lesson = lesson  # Associate the lesson with the enrollment
#         enrollment.save()

#         course.total_enrollment += 1
#         course.save()

#     return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
# Get user and course object, then get the associated enrollment object created when the user enrolled the course
# Create a submission object referring to the enrollment
# Collect the selected choices from exam form
# Add each selected choice object to the submission object
# Redirect to show_exam_result with the submission id

@login_required
def submit_exam(request, course_id):
    user = request.user
    course = get_object_or_404(Course, id=course_id)

    # Get the associated enrollment object for the user and course
    enrollment = get_object_or_404(Enrollment, user=user, course=course)

    if request.method == 'POST':
        # Create a new submission object for the enrollment
        submission = Submission.objects.create(enrollment=enrollment)

        # Collect the selected choices from the exam form using the extract_answers function
        submitted_answers = extract_answers(request)

        # Add each selected choice to the submission object
        for question_id, selected_choice_ids in submitted_answers.items():
            question = get_object_or_404(Question, id=question_id)
            selected_choices = Choice.objects.filter(id__in=selected_choice_ids)
            submission.choices.add(*selected_choices)

        # Update the progress of the enrollment
        submission.update_progress()

        # Redirect to the exam result view with the submission id as a parameter
        return redirect('onlinecourse:show_exam_result', submission_id=submission.id)

    # If the request method is not POST, render the exam submission page
    return render(request, 'onlinecourse/exam_submission.html', {'course': course})

# <HINT> A example method to collect the selected choices from the exam form from the request object


def extract_answers(request):
    submitted_answers = {}
    for key in request.POST:
        if key.startswith('choice'):
            question_id, choice_id = key.split('_')[1:]  # Get the question_id and choice_id from the key
            question_id = int(question_id)
            choice_id = int(choice_id)
            if question_id in submitted_answers:
                submitted_answers[question_id].append(choice_id)
            else:
                submitted_answers[question_id] = [choice_id]
    return submitted_answers

# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
# Get course and submission based on their ids
# Get the selected choice ids from the submission record
# For each selected choice, check if it is a correct answer or not
# Calculate the total score
@login_required
def show_exam_result(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    enrollment = submission.enrollment
    
    
    course = enrollment.course
    user = request.user
    

    # Calculate the total score and check if the learner passed the exam
    total_score = submission.calculate_total_score()
    passing_score = course.passing_score
    is_passed = total_score >= passing_score

    # Calculate the final grade with normalization to 10
    final_grade = submission.calculate_final_grade()

    # Prepare the dictionary with question results
    question_results_dict = []
    for question in course.questions.all():
        selected_choices = submission.choices.filter(question=question)
        selected_choices_ids = [choice.id for choice in selected_choices]
        choices_info = []
        for choice in question.choice_set.all():
            is_correct = choice.is_correct
            selected = choice.id in selected_choices_ids
            choices_info.append((choice, is_correct, selected))
        question_result = {
            'question': question,
            'choices': choices_info,
            'score': question.calculate_score(selected_choices_ids),
        }
        question_results_dict.append(question_result)

    # Render the exam result page with question results and overall result
    return render(request, 'onlinecourse/exam_result.html', {
        'course': course,
        'submission': submission,
        'user': user,
        'total_score': total_score,
        'passing_score': passing_score,
        'is_passed': is_passed,
        'question_results_dict': question_results_dict,
        'final_grade': final_grade,
    })



