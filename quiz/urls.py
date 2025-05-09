from django.urls import path
from . import views

urlpatterns = [
    path('all_quiz/', views.all_quiz_view, name='all_quiz'),
    path('start_quiz/<int:quiz_id>/', views.quiz_view, name='start_quiz'),
    path('class/<int:class_id>/quiz-excel-upload/', views.quiz_excel_upload, name='quiz_excel_upload'),
    path('preview-quiz-excel/', views.preview_quiz_excel, name='preview_quiz_excel'),
    path('create-quiz-from-excel-submit/', views.create_quiz_from_excel_submit, name='create_quiz_from_excel_submit'),
    path('quiz_result/<int:quiz_id>/<int:quiz_result_id>', views.quiz_result_view, name='quiz_result'),
    path('addquiz', views.addQuiz, name='addquiz'),
    path('quiz/<int:quiz_id>/user-result/', views.user_quiz_result, name='user_quiz_result'),
    path('mark_quiz/<int:quiz_id>', views.mark_quiz, name='mark_quiz'),
    path('quiz_leaderboard/<int:quiz_id>', views.quiz_leaderboard_view, name='quiz_leaderboard'),
    path('class/<int:class_id>/createquizfromdb/', views.create_quiz_from_db, name='createQuizFromDB'),
    path('class/<int:class_id>/create-pdf-quiz/', views.create_pdf_quiz, name='create_pdf_quiz'),
    path('pdf_quiz/<int:quiz_id>/', views.pdf_quiz_view, name='pdf_quiz_view'),
    path('submit_pdf_quiz/<int:quiz_id>/<int:quiz_result_id>/', views.submit_pdf_quiz, name='submit_pdf_quiz'),
    path('grade_pdf_submission/<int:submission_id>/', views.grade_pdf_submission, name='grade_pdf_submission'),
]
