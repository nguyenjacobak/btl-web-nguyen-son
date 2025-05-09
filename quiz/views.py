from django.shortcuts import render, redirect, get_object_or_404
# render: dùng để render template với context
# redirect: dùng để chuyển hướng người dùng đến URL khác
# get_object_or_404: dùng để lấy một đối tượng hoặc trả về lỗi 404 nếu không tìm thấy
import json
from django.contrib.auth.decorators import login_required
# login_required: decorator yêu cầu người dùng phải đăng nhập mới có thể truy cập view

from allClass.models import MyClass
# MyClass: model từ ứng dụng allClass

from .models import Quiz, Category, Question, Option, QuizResult, StudentAnswer, QuizAttempt, FullStudentAnswer, Document, PDFSubmission
# Quiz, Category, Question, Option, QuizResult, StudentAnswer , QuizAttempt, FullStudentAnswer, Document, PDFSubmission: các model tùy chỉnh của ứng dụng hiện tại

from django.db.models import Q, Count
# Q: dùng để xây dựng các truy vấn phức tạp với các điều kiện logic

from django.utils import timezone
# timezone: cung cấp các tiện ích liên quan đến múi giờ

from django.views.decorators.cache import never_cache
# never_cache: decorator để ngăn chặn việc lưu cache cho một view cụ thể

from django.contrib.auth.decorators import user_passes_test
# user_passes_test: decorator yêu cầu người dùng phải vượt qua một kiểm tra tùy chỉnh mới có thể truy cập view

from django.http import JsonResponse
# JsonResponse: dùng để trả về dữ liệu JSON

from django.db.models import Max
# Max: dùng để tính giá trị lớn nhất của một trường trong các bản ghi

from django.db.models import OuterRef, Subquery
# OuterRef, Subquery: dùng để tạo các truy vấn con (subquery) trong Django ORM

# from quiz.models import QuizSubmission
# QuizSubmission: model từ ứng dụng quiz (đã bị comment)

from django.contrib import messages
# messages: dùng để hiển thị thông báo cho người dùng

from django.core.files.storage import FileSystemStorage
# FileSystemStorage: dùng để quản lý lưu trữ file trong hệ thống file
import matplotlib.pyplot as plt
import matplotlib 
from django.views.decorators.http import require_http_methods
matplotlib.use('Agg')
import pandas as pd
import numpy as np
from io import BytesIO
import seaborn as sns
import base64

def is_admin(user):
    return user.is_superuser
def is_giaovien(user):
    return user.is_staff or user.is_superuser
@login_required(login_url='login')
def quiz_result_visualize(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_results = QuizResult.objects.filter(quiz_id=quiz_id)
    student_answers = FullStudentAnswer.objects.filter(quiz_id=quiz_id)
    scores = [quiz_result.score for quiz_result in quiz_results]

    correct_answers_by_difficulty = student_answers.filter(is_correct=True).values('question_id__difficulty').annotate(count=Count('question_id__difficulty'))
    incorrect_answers_by_difficulty = student_answers.filter(is_correct=False).values('question_id__difficulty').annotate(count=Count('question_id__difficulty'))
    difficulties = [1, 2, 3]  # Assuming difficulties are 1, 2, and 3
    correct_counts = [next((item['count'] for item in correct_answers_by_difficulty if item['question_id__difficulty'] == d), 0) for d in difficulties]
    incorrect_counts = [next((item['count'] for item in incorrect_answers_by_difficulty if item['question_id__difficulty'] == d), 0) for d in difficulties]
    total_times = [(quiz_result.end_time - quiz_result.start_time).total_seconds() for quiz_result in quiz_results]
    # Ensure no invalid values in counts
    correct_counts = [0 if np.isnan(count) or np.isinf(count) else int(count) for count in correct_counts]
    incorrect_counts = [0 if np.isnan(count) or np.isinf(count) else int(count) for count in incorrect_counts]

    pie_charts = {}
    for i, difficulty in enumerate(difficulties):
        if correct_counts[i] + incorrect_counts[i] == 0:
            continue  # Skip if no data
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.pie(
            [correct_counts[i], incorrect_counts[i]],
            colors=['#28a745', '#dc3545'],  # Green for correct, Red for incorrect
            autopct='%1.1f%%',
            startangle=140
        )
        ax.set_title(f'Question Level {difficulty}', fontsize=14, color='#333')
        ax.legend(['Correct', 'Incorrect'], loc='upper right')
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        pie_chart_image = buffer.getvalue()
        buffer.close()
        pie_charts[difficulty] = base64.b64encode(pie_chart_image).decode('utf-8')

    buffer = BytesIO()
    plt.figure(figsize=(10, 5))
    sns.histplot(scores, bins=10, kde=True, color='#007bff', edgecolor='black')
    plt.xlim(0, 10)
    plt.xlabel('Scores', fontsize=12, color='#333')
    plt.ylabel('Number of Students', fontsize=12, color='#333')
    plt.title('Distribution of Scores', fontsize=14, color='#333')
    plt.legend(['Density Curve'], loc='upper right')
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    histogram_graphic = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    buffer = BytesIO()
    plt.figure(figsize=(10, 5))
    sns.scatterplot(x=total_times, y=scores, color='#ffc107')
    plt.xlabel('Total Time', fontsize=12, color='#333')
    plt.ylabel('Scores', fontsize=12, color='#333')
    plt.title('Relation between time and score', fontsize=14, color='#333')
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    scatter_graphic = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    return render(request, 'quiz_result_visualization.html', {
        'quiz': quiz,
        'histogram_graphic': histogram_graphic,
        'pie_charts': pie_charts,
        'student_answers': student_answers,
        'scatter_graphic': scatter_graphic
    })

    
@login_required(login_url='login')
# hàm này dùng để render ra trang tất cả các bài quiz
def all_quiz_view(request):

    quizzes = Quiz.objects.order_by('-created_at')
    categories = Category.objects.all()

    context = {"quizzes": quizzes, "categories": categories}
    return render(request, 'all-quiz.html', context)


@login_required(login_url='login')
# hàm này dùng để render ra trang chi tiết của một bài quiz
def quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Si es un examen de tipo PDF, redirigir a la vista específica
    if quiz.quiz_type == 'PDF':
        return redirect('pdf_quiz_view', quiz_id=quiz_id)
    
    # Para exámenes normales, continuar con el flujo habitual
    if not quiz.active:
        return render(request, '404.html', {'quiz': quiz})
    questions = Question.objects.filter(quiz_id=quiz_id)
    options = []
    #  check if the user has already taken the quiz
    quiz_attempt, created = QuizAttempt.objects.get_or_create(user=request.user, quiz=quiz)
    if quiz_attempt.completed:
        return render(request, 'already_taken.html', {'quiz': quiz})
    # Chuyển đổi các đối tượng Question thành dictionary
    question_dicts = [
        {
            'id': question.id,
            'question_text': question.question_text,
            'question_type': question.question_type,
            'category': question.category.id if question.category else None,
            'topic': question.topic,
            'subtopic': question.subtopic,
            'CLO': question.CLO,
            'quiz_id': question.quiz_id.id,
            'difficulty': question.difficulty
        } 
        for question in questions
    ]
    if 'quiz_id' in request.session and request.session['quiz_id'] != quiz_id:
        request.session['quiz_id'] = quiz_id
        del request.session['options']
    else:
        request.session['quiz_id'] = quiz_id
    if 'options' in request.session and options != []:
        options = request.session['options']
    else:
        for question in questions:
            correct_option = Option.objects.filter(question_id=question, is_correct=True).order_by('?').first()
            incorrect_options = Option.objects.filter(question_id=question, is_correct=False).order_by('?')[:3]

            if correct_option is None or len(incorrect_options) < 3:
                continue
            # Chuyển đổi các đối tượng Option thành dictionary
            option_dicts = [
                {
                    'id': opt.id,
                    'option_text': opt.option_text,
                    'question_id': opt.question_id.id,
                    'is_correct': opt.is_correct
                } 
                for opt in [correct_option] + list(incorrect_options)
            ]
            options.append(option_dicts)
        
        # Lưu các câu trả lời vào session
        request.session['options'] = options
    if not questions.exists():
        return render(request, 'quiz.html', {'quiz': quiz, 'questions': question_dicts, 'options': options, 'quiz_result': None, 'error': 'No questions available for this quiz.'})
    
    try: 
        quiz_result = QuizResult.objects.filter(user_id=request.user, quiz_id=quiz).order_by('-id').first()
        if quiz_result:
            elapsed_time = (timezone.now() - quiz_result.start_time).total_seconds()
            if elapsed_time > quiz.duration * 60:
                raise QuizResult.DoesNotExist
        else:
            raise QuizResult.DoesNotExist
    except QuizResult.DoesNotExist:
        quiz_result = QuizResult.objects.create(
            user_id=request.user,
            score=0,
            correct_answers=0,
            incorrect_answers=0,
            quiz_id=quiz,
            start_time=timezone.now()
        )
    elapsed_time = (timezone.now() - quiz_result.start_time).total_seconds()
    remaining_time = max(quiz.duration * 60 - elapsed_time, 0)
    return render(request, 'quiz.html', 
                  {'quiz': quiz, 
                   'questions': question_dicts, 
                   'options': options, 
                   'quiz_result': quiz_result,
                   'remaining_time': remaining_time,
                   })
# hàm này dùng để xử lý việc người dùng gửi đã gửi câu trả lời của bài quiz(người dùng đã làm bài này hay chưa)
def already_taken(request):
    return render(request, 'already_taken.html')

@login_required(login_url='login')
@never_cache
# hàm này dùng để xử lý việc người dùng gửi câu trả lời của bài quiz(xem kết quă)
def quiz_result_view(request, quiz_id, quiz_result_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz_id=quiz_id)
    quiz_result = get_object_or_404(QuizResult, id=quiz_result_id)
    user = request.user
    quiz_attempt, created = QuizAttempt.objects.get_or_create(user=user, quiz=quiz)
    if quiz_attempt.completed:
        return render(request, 'already_taken.html', {'quiz': quiz})
    if request.method == 'POST':
        quiz_result.end_time = timezone.now()
        score = 0
        correct_answers = 0
        incorrect_answers = 0
        heso = 10 / len(questions)
        for question in questions:
            if question.question_type == 'MCQ':
                selected_option_id = request.POST.get(str(question.id))
                if selected_option_id:
                    selected_option = Option.objects.get(id=int(selected_option_id))
                    options = request.session['options']
                    options_of_question = [opt for opt in options if opt[0]['question_id'] == question.id]
                    if len(options_of_question) == 0:
                        continue
                    option_1 = Option.objects.filter(id=options_of_question[0][0]['id']).first()
                    option_2 = Option.objects.filter(id=options_of_question[0][1]['id']).first()
                    option_3 = Option.objects.filter(id=options_of_question[0][2]['id']).first()
                    option_4 = Option.objects.filter(id=options_of_question[0][3]['id']).first()
                    FullStudentAnswer.objects.create(
                        question_id=question,
                        quiz_result_id=quiz_result,
                        selected_option=selected_option,
                        option_1=option_1,
                        option_2=option_2,
                        option_3=option_3,
                        option_4=option_4,
                        quiz_id=quiz,
                        is_correct = selected_option.is_correct
                    )
                    if selected_option.is_correct:
                        score += heso
                        correct_answers += 1
                    else:
                        incorrect_answers += 1
            elif question.question_type == 'FIB':
                answer_text = request.POST.get(str(question.id))
                if answer_text:
                    FullStudentAnswer.objects.create(
                        question_id=question,
                        quiz_result_id=quiz_result,
                        answer_text=answer_text,
                        quiz_id=quiz
                    )
                    StudentAnswer.objects.create(
                        question_id=question,
                        quiz_result_id=quiz_result,
                        answer_text=answer_text,
                        studen_id=request.user.profile.studen_id,
                        quiz_id=quiz
                    )
        quiz_result.score = score
        quiz_result.correct_answers = correct_answers
        quiz_result.incorrect_answers = incorrect_answers
        quiz_result.save()
        quiz_attempt.completed = True
        quiz_attempt.save()
    return render(request, 'quiz_result.html', {
        'score': score, 
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'username': request.user.username,
        'total_questions': len(questions),
        'quiz': quiz,
        'quiz_result': quiz_result
    })

@login_required(login_url='login')
@user_passes_test(is_giaovien)
# hàm này dùng để render ra trang thêm bài quiz
def addQuiz(request, class_id):
    myclass = get_object_or_404(MyClass, id=class_id)
    categories = Category.objects.all()
    return render(request, 'addQuiz.html',{'categories': categories,
                                           'class_id': class_id,
                                           'myclass': myclass})

@login_required(login_url='login')
# hàm này dùng để xử lý kết qủa bài thi và in ra bảng xếp hạng
def quiz_leaderboard_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    class_instance = quiz.class_id
    if request.user != quiz.instructor and request.user not in class_instance.students.all():
        return render(request, '404.html', status=404)  # Trả về trang 403 nếu không có quyền truy cập
    subquery = QuizResult.objects.filter(
    user_id=OuterRef('user_id'),  
    quiz_id=OuterRef('quiz_id')   
    ).order_by('-score').values('score')[:1]
    results = QuizResult.objects.filter(score = Subquery(subquery), quiz_id = quiz_id).order_by('-score')   
    return render(request, 
                  'quiz_leaderboard.html', 
                  { 'quiz': quiz,
                    'results': results})

@login_required(login_url='login')
@user_passes_test(is_giaovien)
#  hàm này có chức năng tạo ra đề kiểm tra từ cơ sở dữ liệu câu hỏi hiện có
def create_quiz_from_db(request, class_id):
    myclass = get_object_or_404(MyClass, id=class_id)
    categories = Category.objects.all()
    questions = Question.objects.filter(quiz_id=None)
    valid_questions = []
    for question in questions:
        if question.question_type == 'MCQ':
            options = Option.objects.filter(question_id=question.id)
            num_correct_options = options.filter(is_correct=True).count()
            num_incorrect_options = options.filter(is_correct=False).count()
            if num_correct_options >= 1 and num_incorrect_options >= 3:
                valid_questions.append(question)
        else:
            valid_questions.append(question)
    questions = Question.objects.filter(id__in=[question.id for question in valid_questions])
    if request.method == 'POST':
        quiz_title = request.POST.get('quiz_title')
        quiz_description = request.POST.get('quiz_description')
        quiz_category = request.POST.get('quiz_category')
        quiz_duration = request.POST.get('quiz_duration')  # Get duration from form
        selected_questions = request.POST.getlist('questions')
        quiz = Quiz.objects.create(
            title=quiz_title,
            description=quiz_description,
            category_id=quiz_category,
            duration=quiz_duration,
            total_questions=len(selected_questions),
            instructor=request.user,
            class_id=myclass
        )
        for question_id in selected_questions:
            question = Question.objects.get(id=question_id)
            question = Question.objects.create(
                quiz_id=quiz,
                question_text=question.question_text,
                CLO=question.CLO,
                difficulty=question.difficulty,
                question_type=question.question_type,
                topic=question.topic,
                subtopic=question.subtopic
            )
            if question.question_type == 'MCQ':
                options = Option.objects.filter(question_id=question_id)
                for option in options:
                    Option.objects.create(
                        question_id=question,
                        option_text=option.option_text,
                        is_correct=option.is_correct
                    )
        messages.success(request, 'Quiz created successfully!')
        return redirect('class_detail', class_id=myclass.id)
    if 'category' in request.GET:
        category_filter = request.GET['category'].split(',')
        questions = questions.filter(category_id__in=category_filter)
    if 'clo' in request.GET:
        clo_filter = request.GET['clo'].split(',')
        questions = questions.filter(CLO__in=clo_filter)
    if 'difficulty' in request.GET:
        difficulty_filter = request.GET['difficulty'].split(',')
        questions = questions.filter(difficulty__in=difficulty_filter)
    if 'type' in request.GET:
        type_filter = request.GET['type'].split(',')
        questions = questions.filter(question_type__in=type_filter)
    if 'topic' in request.GET:
        topic_filter = request.GET['topic'].split(',')
        questions = questions.filter(topic__in=topic_filter)
    if 'subtopic' in request.GET:
        subtopic_filter = request.GET['subtopic'].split(',')
        questions = questions.filter(subtopic__in=subtopic_filter)
    # Lấy các giá trị duy nhất cho các bộ lọc
    clos = questions.values_list('CLO', flat=True).distinct()
    topics = questions.values_list('topic', flat=True).distinct()
    subtopics = questions.values_list('subtopic', flat=True).distinct()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        questions_data = list(questions.values('id', 'question_text', 'CLO', 'difficulty', 'question_type'))
        return JsonResponse({'questions': questions_data})
    context = {
        'categories': categories,
        'clos': clos,
        'topics': topics,
        'subtopics': subtopics,
        'questions': questions,
        'class_id': class_id
    }
    return render(request, 'createQuizFromDB.html', context)
@login_required(login_url='login')
@user_passes_test(is_giaovien)
# hàm này có chức năng cho phép giáo viên chấm các câu hỏi tự luận của sinh viên, có thể lấy câu trả lời làm đáp án lưu trong cơ sở dữ liệu
def mark_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # For PDF quizzes
    if quiz.quiz_type == 'PDF':
        pdf_submissions = PDFSubmission.objects.filter(quiz=quiz)
        return render(request, 'mark_pdf_quiz.html', {
            'quiz': quiz,
            'pdf_submissions': pdf_submissions
        })
    
    # For normal quizzes
    questions = Question.objects.filter(quiz_id=quiz_id)
    
    # If no questions, show empty state
    if not questions.exists():
        return render(request, 'mark_quiz.html', {
            'quiz': quiz,
            'text_answers': [],
            'text_questions': [],
            'heso': 0,
            'no_questions': True
        })
    
    text_questions = Question.objects.filter(quiz_id=quiz_id, question_type='FIB')
    text_answers = StudentAnswer.objects.filter(question_id__in=text_questions, is_mark=False)
    
    # Calculate heso safely (avoid division by zero)
    heso = 10/len(questions) if questions.exists() else 0
    
    if request.method == 'POST':
        for answer in text_answers:
            is_correct = request.POST.get(f'correct_{answer.id}')
            filled_score = request.POST.get(f'score_{answer.id}')
            if is_correct == 'true':
                answer.score += heso
            if filled_score:
                answer.score = float(filled_score)
            if is_correct != None or filled_score != None:
                answer.is_mark = True
            student_answer = FullStudentAnswer.objects.filter(question_id=answer.question_id, quiz_result_id=answer.quiz_result_id).first()
            if student_answer:
                student_answer.is_correct = is_correct == 'true'
                student_answer.save()
            answer.save()
            add_option = request.POST.get(f'option_{answer.id}')
            if add_option:
                question = Question.objects.get(id=answer.question_id_id)
                if not Question.objects.filter(question_text=question.question_text, question_type = 'MCQ').exists():
                    new_question = Question.objects.create(
                            question_text=question.question_text,
                            CLO=question.CLO,
                            difficulty=question.difficulty,
                            question_type='MCQ',
                            category=question.quiz_id.category,
                            topic=question.topic,
                            subtopic=question.subtopic
                        )
                    new_question.save()
                    Option.objects.create(
                        question_id=new_question,
                        option_text=answer.answer_text,
                        is_correct=is_correct == 'true'
                    )
                else:
                    old_question = Question.objects.get(question_text=question.question_text, question_type = 'MCQ')
                    Option.objects.create(
                        question_id=old_question,
                        option_text=answer.answer_text,
                        is_correct=is_correct == 'true'
                    )
        for quiz_result in QuizResult.objects.filter(quiz_id=quiz_id):
            text_score = sum([answer.score for answer in text_answers if answer.quiz_result_id == quiz_result])
            quiz_result.score += text_score
            quiz_result.save()
        if quiz.class_id:
            return redirect('class_detail', class_id=quiz.class_id.id)
        else:
            return redirect('all_quiz')
            
    return render(request, 'mark_quiz.html', {
        'quiz': quiz, 
        'text_answers': text_answers, 
        'text_questions': text_questions,
        'heso': heso
    })

@login_required(login_url='login')
@user_passes_test(is_giaovien)
# thông báo đã tải đề thi lên thành công
def upload_success(request):
    return render(request, 'upload_success.html')

@login_required(login_url='login')
def upload_error(request):
    return render(request, 'upload_error.html')
    

@login_required(login_url='login')
@user_passes_test(is_giaovien) 
def create_quiz_from_excel(request):
    categories = Category.objects.all()
    if request.method == 'POST' and request.FILES['quiz_file']:
        quiz_file = request.FILES['quiz_file']
        category_id = request.POST.get('category')
        category = Category.objects.get(id=category_id)
        
        # Đọc file Excel và sử dụng hàng đầu tiên làm tiêu đề cột
        try:
            df = pd.read_excel(quiz_file)
        except Exception as e:
            return render(request, 'upload_error.html', {'error': 'Cannot read from file.'})

        # Xóa tất cả các cột toàn NaN
        df = df.dropna(axis=1, how='all')

        required_columns = ['question_type', 'question_text', 'topic', 'subtopic', 'CLO', 'difficulty', 'op1', 'op2', 'op3', 'op4', 'correct']
        # Kiểm tra từng cột có tồn tại không
        for column in required_columns:
            if column not in df.columns:
                return render(request, 'upload_error.html', {'error': f'Missing required column: {column}'})

        # Xóa tất cả các hàng có giá trị NaN trong các cột cần thiết
        df = df.dropna(subset=['topic', 'subtopic', 'CLO', 'difficulty'])

        # Lấy các giá trị từ các cột cần thiết
        question_types = df['question_type']
        question_texts = df['question_text']

        try:
            Topic = df['topic']
        except KeyError:
            return render(request, 'upload_error.html', {'error': 'Không tìm thấy cột "topic".'})

        try:
            SubTopic = df['subtopic']
        except KeyError:
            return render(request, 'upload_error.html', {'error': 'Không tìm thấy cột "subtopic".'})

        try:
            CLO = df['CLO'].astype(str).str.extract(r'(\d+)')[0]
        except KeyError:
            return render(request, 'upload_error.html', {'error': 'Không tìm thấy cột "CLO".'})

        try:
            difficulty = df['difficulty']
        except KeyError:
            return render(request, 'upload_error.html', {'error': 'Không tìm thấy cột "difficulty".'})

        # Lưu các câu hỏi vào model Question
        for i in range(len(df)):
            question_type = question_types.iloc[i]
            question_text = question_texts.iloc[i]
            topic = Topic.iloc[i]
            subtopic = SubTopic.iloc[i]
            CLO_value = CLO.iloc[i]
            difficulty_value = difficulty.iloc[i]

            # Tạo đối tượng Question
            question = Question.objects.create(
                question_type=question_type,
                question_text=question_text,
                topic=topic,
                subtopic=subtopic,
                CLO=CLO_value,
                difficulty=difficulty_value,
                category=category
            )

            # Nếu question_type là MCQ, tạo các đối tượng Option
            if question_type.upper() == 'MCQ':
                try:
                    options = df.iloc[i, 6:10]  # Lấy các cột op1, op2, op3, op4
                    correct_option = int(df.iloc[i, 10])  # Lấy cột correct
                    for j, option_text in enumerate(options, start=1):
                        Option.objects.create(
                            question_id=question,
                            option_text=option_text,
                            is_correct=(j == correct_option)
                        )
                except IndexError:
                    return render(request, 'upload_error.html', {'error': 'Không tìm thấy các cột "op1", "op2", "op3", "op4" hoặc "correct".'})

        return redirect('upload_success')
    return redirect('upload_success')
@login_required(login_url='login')
# xem chi tiết lại bài thi và đáp án mà sinh viên đã làm sau khi đã nộp bài thi
def all_quiz_result_view(request, quiz_id, quiz_result_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz_id=quiz_id)
    quiz_result = get_object_or_404(QuizResult, id=quiz_result_id)
    full_student_answers = FullStudentAnswer.objects.filter(quiz_result_id=quiz_result_id)
    return render(request, 'all_student_answers.html', {
        'quiz': quiz,
        'questions': questions,
        'quiz_result': quiz_result,
        'full_student_answers': full_student_answers
    })

@login_required(login_url='login')
#  dùng để cho phép giáo viên kích hoạt bài kiểm tra, cho phép sinh viên có thể vào làm bài
def activate_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.user == quiz.instructor:
        if request.method == 'POST':
            quiz.active = 'active' in request.POST
            quiz.save()
    # Get the MyClass instance associated with this quiz
    my_class = quiz.class_id  # Use the correct field name
    if my_class:
        return redirect('class_detail', class_id=my_class.id)
    else:
        messages.error(request, 'This quiz is not associated with any class.')
        return redirect('my_classes')

@login_required(login_url='login')
def add_document(request, class_id):
    myclass = get_object_or_404(MyClass, id=class_id)
    if request.user != myclass.instructor:
        return redirect('inyourclass', class_id=class_id)
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST.get('description', '')
        file = request.FILES['file']
        Document.objects.create(
            myclass=myclass,
            title=title,
            description=description,
            file=file,
            uploader=request.user
        )
        messages.success(request, 'Tải lên tài liệu thành công.')
        return redirect('class_detail', class_id=class_id)
    return redirect('class_detail', class_id=class_id)


@login_required(login_url='login')
@require_http_methods(["DELETE"])
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.user == quiz.instructor:
        quiz.delete()
        return JsonResponse({'message': 'Quiz deleted successfully.'}, status=200)
    else:
        return JsonResponse({'message': 'You do not have permission to delete this quiz.'}, status=403)

@login_required(login_url='login')
@require_http_methods(["DELETE"])
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    if request.user == document.myclass.instructor:
        document.delete()
        return JsonResponse({'message': 'Document deleted successfully.'}, status=200)
    else:
        return JsonResponse({'message': 'You do not have permission to delete this document.'}, status=403)
@login_required(login_url='login')
@user_passes_test(is_giaovien)
def quiz_excel_upload(request, class_id):
    """Display page for uploading and previewing Excel files for quiz creation"""
    myclass = get_object_or_404(MyClass, id=class_id)
    categories = Category.objects.all()
    
    context = {
        'class_id': class_id,
        'categories': categories,
        'myclass': myclass
    }
    
    return render(request, 'create_quiz_excel.html', context)

@login_required(login_url='login')
@user_passes_test(is_giaovien)
def preview_quiz_excel(request):
    """Process Excel file and return questions as JSON for preview"""
    if request.method == 'POST' and request.FILES.get('quiz_file'):
        quiz_file = request.FILES['quiz_file']
        category_id = request.POST.get('category')
        
        # Process the file
        try:
            df = pd.read_excel(quiz_file)
            
            # Basic validation
            df = df.dropna(axis=1, how='all')
            required_columns = ['question_type', 'question_text', 'topic', 'subtopic', 'CLO', 'difficulty', 'op1', 'op2', 'op3', 'op4', 'correct']
            
            for column in required_columns:
                if column not in df.columns:
                    return JsonResponse({'success': False, 'error': f'Missing required column: {column}'})
            
            # Clean data
            df = df.dropna(subset=['topic', 'subtopic', 'CLO', 'difficulty'])
            
            # Process questions
            questions = []
            for i in range(len(df)):
                question_type = str(df['question_type'].iloc[i]).strip()
                question_text = str(df['question_text'].iloc[i]).strip()
                topic = str(df['topic'].iloc[i]).strip()
                subtopic = str(df['subtopic'].iloc[i]).strip()
                
                try:
                    clo_value = df['CLO'].iloc[i]
                    # Extract numeric part if present
                    if isinstance(clo_value, str):
                        import re
                        match = re.search(r'(\d+)', clo_value)
                        clo = match.group(1) if match else clo_value
                    else:
                        clo = str(int(clo_value)) if pd.notna(clo_value) else ""
                except:
                    clo = ""
                    
                difficulty = str(df['difficulty'].iloc[i]).strip()
                
                question_data = {
                    'question_type': question_type,
                    'question_text': question_text,
                    'topic': topic,
                    'subtopic': subtopic,
                    'CLO': clo,
                    'difficulty': difficulty
                }
                
                # Process options for MCQ
                if question_type.upper() == 'MCQ':
                    options = []
                    correct_index = 0  # Default to first option
                    
                    # First, try to get the correct answer index
                    if 'correct' in df.columns and pd.notna(df['correct'].iloc[i]):
                        try:
                            # Try to parse as integer (1-4)
                            correct_index = int(df['correct'].iloc[i]) - 1  # Convert to 0-based index
                        except ValueError:
                            # If not an integer, might be the text of the correct answer
                            correct_text = str(df['correct'].iloc[i]).strip()
                            for j in range(4):
                                col_name = f'op{j+1}'
                                if col_name in df.columns and pd.notna(df[col_name].iloc[i]):
                                    if str(df[col_name].iloc[i]).strip() == correct_text:
                                        correct_index = j
                                        break
                    
                    # Add all options
                    for j in range(4):
                        col_name = f'op{j+1}'
                        if col_name in df.columns and pd.notna(df[col_name].iloc[i]):
                            option_text = str(df[col_name].iloc[i]).strip()
                            is_correct = (j == correct_index)
                            
                            options.append({
                                'option_text': option_text,
                                'is_correct': is_correct
                            })
                    
                    question_data['options'] = options
                
                questions.append(question_data)
            print("Success 01")
            return JsonResponse({
                'success': True, 
                'questions': questions,
                'count': len(questions)
            })
            
        except Exception as e:
            print("Error")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'No file provided'})
@login_required(login_url='login')
@user_passes_test(is_giaovien)
def create_quiz_from_excel_submit(request):
    """Create quiz from the previewed Excel data"""
    if request.method == 'POST':
        try:
            # Get form data
            class_id = request.POST.get('class_id')
            quiz_title = request.POST.get('quiz_title')
            quiz_description = request.POST.get('quiz_description', '')
            quiz_duration = int(request.POST.get('quiz_duration', 45))
            category_id = request.POST.get('category_id')
            excel_data = request.POST.get('excel_data')
            
            # Get user-modified correct answers
            modified_correct_answers = {}
            for key, value in request.POST.items():
                if key.startswith('correct_answer_'):
                    question_index = key.replace('correct_answer_', '')
                    modified_correct_answers[question_index] = int(value)
            
            # Validate data
            if not all([class_id, quiz_title, category_id, excel_data]):
                messages.error(request, 'Missing required fields')
                return redirect('quiz_excel_upload', class_id=class_id)
            
            # Parse JSON data
            questions_data = json.loads(excel_data)
            
            # Apply user-modified correct answers
            for question_idx, question_data in enumerate(questions_data):
                if question_data['question_type'].upper() == 'MCQ' and str(question_idx) in modified_correct_answers:
                    correct_option_idx = modified_correct_answers[str(question_idx)]
                    for i, option in enumerate(question_data.get('options', [])):
                        option['is_correct'] = (i == correct_option_idx)
            
            # Get related objects
            myclass = get_object_or_404(MyClass, id=class_id)
            category = get_object_or_404(Category, id=category_id)
            
            # Create quiz
            quiz = Quiz.objects.create(
                title=quiz_title,
                description=quiz_description,
                category=category,
                duration=quiz_duration,
                total_questions=len(questions_data),
                instructor=request.user,
                class_id=myclass
            )
            
            # Create questions and options
            for question_data in questions_data:
                question = Question.objects.create(
                    quiz_id=quiz,
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    topic=question_data['topic'],
                    subtopic=question_data['subtopic'],
                    CLO=question_data['CLO'],
                    difficulty=question_data['difficulty'],
                    category=category
                )
                
                # Create options for MCQ questions
                if question_data['question_type'].upper() == 'MCQ' and 'options' in question_data:
                    for option_data in question_data['options']:
                        Option.objects.create(
                            question_id=question,
                            option_text=option_data['option_text'],
                            is_correct=option_data['is_correct']
                        )
            print("Success")
            messages.success(request, f'Đề kiểm tra "{quiz_title}" đã được tạo thành công!')
            return redirect('class_detail', class_id=class_id)
            
        except Exception as e:
            print("Error in E")
            messages.error(request, f'Đã xảy ra lỗi: {str(e)}')
            return redirect('quiz_excel_upload', class_id=request.POST.get('class_id'))
    
    # If not POST, redirect to the upload page
    return redirect('quiz_excel_upload', class_id=request.GET.get('class_id'))

@login_required(login_url='login')
def user_quiz_result(request, quiz_id):
    """Redirect to the latest quiz result for the current user for a specific quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_result = QuizResult.objects.filter(
        user_id=request.user, 
        quiz_id=quiz
    ).order_by('-end_time').first()
    
    if quiz_result:
        # Change 'all_quiz_result_view' to 'all_student_answers'
        return redirect('all_student_answers', quiz_id=quiz_id, quiz_result_id=quiz_result.id)
    else:
        messages.info(request, 'Bạn chưa làm bài kiểm tra này.')
        return redirect('class_detail', class_id=quiz.class_id.id)

@login_required(login_url='login')
@user_passes_test(is_giaovien)
def create_pdf_quiz(request, class_id):
    """Display page for creating PDF quiz"""
    myclass = get_object_or_404(MyClass, id=class_id)
    categories = Category.objects.all()
    
    if request.method == 'POST':
        title = request.POST.get('quiz_title')
        description = request.POST.get('quiz_description')
        duration = int(request.POST.get('quiz_duration', 45))
        quiz_file = request.FILES.get('quiz_file')
        
        # Validate data
        if not all([title, description, quiz_file]):
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin.')
            return redirect('create_pdf_quiz', class_id=class_id)
        
        # Create quiz
        quiz = Quiz.objects.create(
            title=title,
            description=description,
            quiz_file=quiz_file,
            quiz_type='PDF',
            duration=duration,
            total_questions=1,  # Default value for PDF quizzes
            instructor=request.user,
            class_id=myclass
        )
        
        messages.success(request, f'Đề kiểm tra PDF "{title}" đã được tạo thành công!')
        return redirect('class_detail', class_id=class_id)
    
    context = {
        'class_id': class_id,
        'categories': categories,
        'myclass': myclass
    }
    
    return render(request, 'create_pdf_quiz.html', context)


@login_required(login_url='login')
def pdf_quiz_view(request, quiz_id):
    """Display PDF quiz for students"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if quiz is active
    if not quiz.active:
        return render(request, '404.html', {'quiz': quiz})
    
    # Check if the user has already taken the quiz
    quiz_attempt, created = QuizAttempt.objects.get_or_create(user=request.user, quiz=quiz)
    if quiz_attempt.completed:
        return render(request, 'already_taken.html', {'quiz': quiz})
    
    # Create QuizResult if it doesn't exist
    try:
        quiz_result = QuizResult.objects.filter(user_id=request.user, quiz_id=quiz).order_by('-id').first()
        if quiz_result:
            elapsed_time = (timezone.now() - quiz_result.start_time).total_seconds()
            if elapsed_time > quiz.duration * 60:
                raise QuizResult.DoesNotExist
        else:
            raise QuizResult.DoesNotExist
    except QuizResult.DoesNotExist:
        quiz_result = QuizResult.objects.create(
            user_id=request.user,
            score=0,
            correct_answers=0,
            incorrect_answers=0,
            quiz_id=quiz,
            start_time=timezone.now()
        )
    
    elapsed_time = (timezone.now() - quiz_result.start_time).total_seconds()
    remaining_time = max(quiz.duration * 60 - elapsed_time, 0)
    
    context = {
        'quiz': quiz,
        'quiz_result': quiz_result,
        'remaining_time': remaining_time
    }
    
    return render(request, 'pdf_quiz.html', context)


@login_required(login_url='login')
def submit_pdf_quiz(request, quiz_id, quiz_result_id):
    """Handle PDF quiz submission"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_result = get_object_or_404(QuizResult, id=quiz_result_id)
    quiz_attempt, created = QuizAttempt.objects.get_or_create(user=request.user, quiz=quiz)
    
    if quiz_attempt.completed:
        return render(request, 'already_taken.html', {'quiz': quiz})
    
    if request.method == 'POST':
        submission_file = request.FILES.get('submission_file')
        
        if not submission_file:
            messages.error(request, 'Vui lòng tải lên file bài làm của bạn.')
            return redirect('pdf_quiz_view', quiz_id=quiz_id)
        
        # Update quiz result
        quiz_result.end_time = timezone.now()
        quiz_result.save()
        
        # Create PDF submission
        PDFSubmission.objects.create(
            user=request.user,
            quiz=quiz,
            quiz_result=quiz_result,
            submission_file=submission_file
        )
        
        # Mark quiz as completed
        quiz_attempt.completed = True
        quiz_attempt.save()
        
        messages.success(request, 'Bạn đã nộp bài thành công!')
        return redirect('user_quiz_result', quiz_id=quiz_id)
    
    return redirect('pdf_quiz_view', quiz_id=quiz_id)


@login_required(login_url='login')
@user_passes_test(is_giaovien)
def grade_pdf_submission(request, submission_id):
    """Grade a PDF submission"""
    submission = get_object_or_404(PDFSubmission, id=submission_id)
    
    if request.method == 'POST':
        score = request.POST.get('score')
        
        if not score:
            messages.error(request, 'Vui lòng nhập điểm.')
            return redirect('grade_pdf_submission', submission_id=submission_id)
        
        try:
            score = float(score)
            if score < 0 or score > 10:
                raise ValueError
        except ValueError:
            messages.error(request, 'Điểm phải là số từ 0 đến 10.')
            return redirect('grade_pdf_submission', submission_id=submission_id)
        
        # Update submission
        submission.score = score
        submission.is_graded = True
        submission.save()
        
        # Update quiz result
        quiz_result = submission.quiz_result
        quiz_result.score = score
        quiz_result.save()
        
        messages.success(request, 'Đã chấm điểm thành công!')
        return redirect('mark_quiz', quiz_id=submission.quiz.id)
    
    context = {
        'submission': submission
    }
    
    return render(request, 'grade_pdf_submission.html', context)