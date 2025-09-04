from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from .models import Quiz, Question
from .models import Option
from .models import Category
from .models import Attempt, Answer, Blog, Tag, Comment, BlogReaction
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.contrib.auth.models import User
import csv
from io import TextIOWrapper
from .forms import BlogForm, CommentForm, CategoryForm
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
import socket
from django.db.models import Q

# socket.getaddrinfo('localhost', 8000)
# Create your views here.
def home(request):
    categories = Category.objects.all()
    blogs = Blog.objects.all().order_by('-created_at')[:6]  # latest 6 blogs
    return render(request, 'core/home.html', {'categories': categories,'blogs':blogs})

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email    = request.POST['email']
        password = request.POST['password']
        confirm  = request.POST['confirm_password']

        # Validate form
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('register')

        # Save user
        User.objects.create(
            username=username,
            email=email,
            password=make_password(password)
        )

        messages.success(request, "Account created successfully. Please login.")
        return redirect('login')

    return render(request, 'core/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        
        if user is not None and not user.is_staff:
            login(request, user)
            messages.success(request, f"Welcome {username}!")
            return redirect('home')
        elif user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f"Welcome {username}!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')
    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('/')

def category_quizzes(request, category_id):
    quizzes = Quiz.objects.filter(category_id=category_id)
    return render(request, 'core/quizzes_by_category.html', {'quizzes': quizzes})

@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    request.session['score'] = 0
    request.session['question_index'] = 0
    request.session['answers'] = {}
    request.session['quiz_id'] = quiz_id

    if quiz.status != 'active':
        messages.warning(request, "This quiz is not currently active.")
        return redirect('quizzes_by_category')

    questions = Question.objects.filter(quiz=quiz).order_by('?')
    return render(request, 'core/quiz_attempt.html', {
        'quiz': quiz,
        'questions': questions,
        'total_questions': questions.count()
    })

@login_required
def attempt_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    questions = quiz.question_set.all()

    # Initialize session variables if not already set
    if 'question_index' not in request.session:
        request.session['question_index'] = 0
        request.session['score'] = 0
        request.session['answers'] = {}

    question_index = request.session['question_index']

    if question_index >= len(questions):
        return redirect('quiz_result', quiz_id=quiz_id)

    current_question = questions[question_index]
    options = current_question.options.all()

    if request.method == 'POST':
        selected_option_id = request.POST.get('option')
        if selected_option_id:
            selected_option = Option.objects.get(id=selected_option_id)

            # Safely update answers and score
            answers = request.session.get('answers', {})
            answers[str(current_question.id)] = selected_option.id
            request.session['answers'] = answers

            if selected_option.is_correct:
                request.session['score'] += 1

        request.session['question_index'] += 1
        return redirect('attempt_quiz', quiz_id=quiz_id)  # Pass quiz_id here

    return render(request, 'core/quiz_attempt.html', {
        'question': current_question,
        'options': options,
        'question_number': question_index + 1,
        'total_questions': len(questions),
    })

@login_required
def quiz_result(request,quiz_id):
    score = request.session.get('score', 0)
    # quiz_id = request.session.get('quiz_id')
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    total_questions = quiz.question_set.count()
    answers = request.session.get('answers', {})

    # Save attempt
    attempt = Attempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total=total_questions,
    )

    # Save each answer
    for qid, oid in answers.items():
        question = Question.objects.get(pk=qid)
        option = Option.objects.get(pk=oid)
        Answer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=option
        )

    # Clear session
    for key in ['score', 'quiz_id', 'question_index', 'answers']:
        request.session.pop(key, None)

    return render(request, 'core/quiz_result.html', {
        'score': score,
        'total_questions': total_questions,
        'quiz': quiz
    })

@login_required
def my_attempts(request):
    attempts = Attempt.objects.filter(user=request.user).order_by('-completed_at')
    return render(request, 'core/my_attempts.html', {'attempts': attempts})

@staff_member_required
def admin_dashboard(request):
    from .models import User, Quiz, Attempt

    context = {
        'total_users': User.objects.count(),
        'total_quizzes': Quiz.objects.count(),
        'total_attempts': Attempt.objects.count(),
        'top_quizzes': Quiz.objects.annotate(attempts=Count('attempt')).order_by('-attempts')[:5],
    }

    return render(request, 'core/admin_dashboard.html', context)

@staff_member_required
def admin_manage_users(request):
    users = User.objects.all()
    return render(request, 'core/admin_users.html', {'users': users})

@staff_member_required
def admin_add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "User created successfully.")
        return redirect('admin_manage_users')
    return render(request, 'core/admin_add_user.html')

@staff_member_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "User deleted.")
    return redirect('admin_manage_users')

@staff_member_required
def upload_users_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
        reader = csv.DictReader(file_data)

        for row in reader:
            username = row['username']
            email = row['email']
            password = row['password']
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(username=username, email=email, password=password)

        messages.success(request, "Users uploaded successfully.")
        return redirect('admin_manage_users')

    return render(request, 'core/admin_upload_users.html')

@staff_member_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        password = request.POST.get('password')

        if password:
            user.set_password(password)

        user.save()
        messages.success(request, "User updated successfully.")
        return redirect('admin_manage_users')

    return render(request, 'core/admin_edit_user.html', {'user': user})

@staff_member_required
def admin_manage_quizzes(request):
    quizzes = Quiz.objects.all()
    categories = Category.objects.all()[:9]

    # Handle new category form
    if request.method == "POST" and "category_submit" in request.POST:
        category_form = CategoryForm(request.POST)
        if category_form.is_valid():
            category_form.save()
            return redirect('admin_manage_quizzes')
    else:
        category_form = CategoryForm()

    return render(request, 'core/admin_quizzes.html', {
        'quizzes': quizzes,
        'categories': categories,
        'category_form': category_form,
    })

@staff_member_required
def admin_add_quiz(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        category = request.POST.get('category')

        category = get_object_or_404(Category, id=category_id)

        status = request.POST.get('status')
        Quiz.objects.create(title=title, category=category, status=status)
        messages.success(request, "Quiz added successfully.")
        return redirect('admin_manage_quizzes')
    return render(request, 'core/admin_add_quiz.html', {'categories': categories})

@staff_member_required
def admin_edit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    categories = Category.objects.all()

    if request.method == 'POST':
        quiz.title = request.POST.get('title')
        category_id = request.POST.get('category')
        quiz.category = get_object_or_404(Category, id=category_id)
        quiz.status = request.POST.get('status')
        quiz.is_paid = request.POST.get('is_paid')
        quiz.price = request.POST.get('price')
        quiz.save()
        messages.success(request, "Quiz updated successfully.")
        return redirect('admin_manage_quizzes')
    return render(request, 'core/admin_edit_quiz.html', {'quiz': quiz, 'categories': categories})

@staff_member_required
def admin_delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz.delete()
    messages.success(request, "Quiz deleted.")
    return redirect('admin_manage_quizzes')

@staff_member_required
def upload_quizzes_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
        reader = csv.DictReader(file_data)

        for row in reader:
            category_name = row['category']
            category, _ = Category.objects.get_or_create(name=category_name)

            Quiz.objects.create(
                title=row['title'],
                category=category,
                status=row.get('status', 'active')
            )

        messages.success(request, "Quizzes uploaded successfully.")
        return redirect('admin_manage_quizzes')

    return render(request, 'core/admin_upload_quizzes.html')

@staff_member_required
def admin_add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == 'POST':
        question_text = request.POST.get('question')
        options = request.POST.getlist('options[]')
        correct_option_index = int(request.POST.get('correct_option'))

        question = Question.objects.create(quiz=quiz, text=question_text)

        for idx, opt_text in enumerate(options):
            Option.objects.create(
                question=question,
                text=opt_text,
                is_correct=(idx == correct_option_index)
            )

        messages.success(request, "Question added successfully.")
        return redirect('admin_add_question', quiz_id=quiz.id)

    return render(request, 'core/admin_add_question.html', {'quiz': quiz})

@staff_member_required
def upload_mcq_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
        reader = csv.DictReader(file_data)

        for row in reader:
            quiz_title = row['quiz_title']
            quiz = Quiz.objects.filter(title=quiz_title).first()
            if not quiz:
                continue

            question = Question.objects.create(
                quiz=quiz,
                text=row['question']
            )

            for i in range(1, 5):
                is_correct = (int(row['correct_option_index']) == i - 1)
                Option.objects.create(
                    question=question,
                    text=row[f'option{i}'],
                    is_correct=is_correct
                )

        messages.success(request, "Questions uploaded successfully.")
        return redirect('admin_dashboard')

    return render(request, 'core/upload_mcq_csv.html')

def quiz_list(request):
    # quizzes = Quiz.objects.filter(status='active')  # or all quizzes if admin
    quizzes = Quiz.objects.all().order_by('-status')
    return render(request, 'core/quiz_list.html', {'quizzes': quizzes})

def blog_list(request):
    blogs = Blog.objects.all().order_by('-created_at')
    return render(request, 'core/blog_list.html', {'blogs': blogs})

def about_us(request):
    return render(request, 'core/about_us.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        full_message = f"Message from {name} ({email}):\n\n{message}"

        # Send email (requires EMAIL settings configured in settings.py)
        send_mail(
            subject,
            full_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],  # change to your email
            fail_silently=False
        )

        messages.success(request, "Thank you for contacting us! We'll reply soon.")
        return redirect('contact')

    return render(request, 'core/contact.html')

def course(request):
    return render(request, 'core/course.html')

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'core/category_list.html', {'categories': categories})

def blog_detail(request, blog_id):
    blog = get_object_or_404(Blog, pk=blog_id)
    comments = blog.comments.order_by('-created_at')
    related_blogs = Blog.objects.exclude(id=blog_id)[:3]

    like_count = blog.reactions.filter(is_like=True).count()
    dislike_count = blog.reactions.filter(is_like=False).count()

    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.user = request.user
            comment.save()
            return redirect('blog_detail', blog_id=blog.id)
    else:
        form = CommentForm()

    return render(request, 'core/blog_detail.html', {
        'blog': blog,
        'comments': comments,
        'form': form,
        'related_blogs': related_blogs,
        'like_count': like_count,
        'dislike_count': dislike_count,
    })

def blogs_by_tag(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    blogs = tag.blogs.all().order_by('-created_at')
    return render(request, 'core/blogs_by_tag.html', {'tag': tag, 'blogs': blogs})

@login_required
def submit_blog(request):
    if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user
            blog.save()
            form.save_m2m()  # Save tags
            return redirect('blog_detail', blog.id)
    else:
        form = BlogForm()
    return render(request, 'core/blog_submit.html', {'form': form})

@login_required
def toggle_blog_reaction(request, blog_id, reaction_type):
    blog = get_object_or_404(Blog, id=blog_id)
    is_like = True if reaction_type == 'like' else False

    reaction, created = BlogReaction.objects.get_or_create(user=request.user, blog=blog)
    if not created and reaction.is_like == is_like:
        # Remove reaction if already liked/disliked
        reaction.delete()
        status = 'removed'
    else:
        # Update or set new reaction
        reaction.is_like = is_like
        reaction.save()
        status = 'added'

    like_count = blog.reactions.filter(is_like=True).count()
    dislike_count = blog.reactions.filter(is_like=False).count()

    return JsonResponse({
        'status': status,
        'likes': like_count,
        'dislikes': dislike_count
    })

def redirect_after_login(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('dashboard')


def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_blogs(request):
    blogs = Blog.objects.all().order_by('-created_at')
    return render(request, 'core/admin_blogs.html', {'blogs': blogs})

@login_required
@user_passes_test(is_admin)
def add_blog(request):
    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_blogs')
    else:
        form = BlogForm()
    return render(request, 'core/add_blog.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def edit_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            return redirect('admin_blogs')
    else:
        form = BlogForm(instance=blog)
    return render(request, 'core/edit_blog.html', {'form': form, 'blog': blog})

@login_required
@user_passes_test(is_admin)
def delete_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    blog.delete()
    return redirect('admin_blogs')

def search(request):
    query = request.GET.get('q')
    quizzes = []
    blogs = []

    if query:
        quizzes = Quiz.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
        blogs = Blog.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query) | Q(tags__name__icontains=query)
        ).distinct()

    return render(request, 'core/search_results.html', {
        'query': query,
        'quizzes': quizzes,
        'blogs': blogs
    })


