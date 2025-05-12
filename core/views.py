from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
import os
import sys # Keep sys for captcha_log
import sqlite3
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Import Azure AI Inference libraries
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# Database schema description for SQL queries
SCHEMA_DESCRIPTION = '''
allClass_myclass(id, name, code, instructor_id);
allClass_myclass_students(id, myclass_id, user_id);
forums_forum(id, title, slug, desc, created_at, user_id);
quiz_category(id, name);
quiz_document(id, title, description, file, upload_date, myclass_id, uploader_id);
quiz_quizattempt(id, completed, timestamp, quiz_id, user_id);
quiz_quiz(id, title, description, quiz_file, created_at, updated_at, duration, total_questions, active, category_id, class_id_id, instructor_id, quiz_type);
quiz_quizresult(id, correct_answers, incorrect_answers, start_time, end_time, quiz_id_id, user_id_id, score);
library_category(id, name);
library_book(id, title, author, description, cover_image, file, price, download_count, created_at, updated_at, category_id);
library_savedbook(id, saved_at, book_id, user_id);
auth_user(id, username, email,first_name, last_name);
'''

PROMPT_TEMPLATE = """
Bạn là trợ lý thông minh cho hệ thống học tập trực tuyến. Bạn có khả năng trả lời các câu hỏi về hệ thống và viết truy vấn SQL để lấy dữ liệu từ cơ sở dữ liệu.

Dưới đây là thông tin về cơ sở dữ liệu SQLite của hệ thống:
{schema}

Thông tin về người dùng hiện tại:
- User ID: {user_id}

HƯỚNG DẪN PHẢN HỒI:

1. Đối với các câu hỏi liên quan đến DỮ LIỆU HỆ THỐNG sau đây:
   - Bài kiểm tra lấy ở bảng quiz_quiz
   - Điểm số lấy ở bảng quiz_quizresult
   - Sách và tài liệu trong thư viện lấy ở bảng library_book
   - Sách đã lưu trong thư viện lấy ở bảng library_savedbook
   - Bài viết diễn đàn lấy ở bảng forums_forum
   - Lớp học lấy ở bảng allClass_myclass_students
   - Thông tin về người dùng lấy ở bảng auth_user
   - Thông tin người dùng đã làm bài kiểm tra hay chưa lấy ở bảng quiz_quizattempt kết hợp bảng quiz_quiz 
   
   => Hãy viết câu truy vấn SQL phù hợp và đặt nó trong cặp dấu ngoặc vuông []. Ví dụ: [SELECT * FROM quiz_quiz WHERE instructor_id = {user_id}]
   => Các câu truy vấn SQL phải được viết trên một dòng duy nhất.

2. Đối với các câu hỏi KHÔNG liên quan đến hệ thống (như chào hỏi, tư vấn học tập, kiến thức tổng quát):
   => Hãy báo với người dùng là bạn chỉ có thể trả lời các câu hỏi liên quan đến hệ thống này và các thông tin liên quan đến lớp học, bài kiểm tra, điểm số của người dùng mà KHÔNG viết SQL.

3. Nếu người dùng yêu cầu dữ liệu của người khác:
   => Trả lời "Bạn không có quyền truy cập thông tin này."
   => Tuy nhiên các bài viết của người khác trong diễn đàn lại công khai, nếu người dùng hỏi bạn hoàn toàn có thể trả lời.

4. LƯU Ý QUAN TRỌNG:
   - Luôn sử dụng user_id={user_id} khi viết các truy vấn liên quan đến dữ liệu người dùng hiện tại
   - Khi người dùng hỏi về sách/tài liệu trong thư viện hoặc bài viết trong diễn đàn hoặc bài kiểm tra hoặc điểm số, hãy viết SQL để lấy toàn bộ dữ liệu ( ví dụ SELECT * FROM library_book), không cần lọc theo từ khóa tìm kiếm

Câu hỏi của người dùng:
{question}
"""

PROMPT_TEMPLATE_2 = """
Tôi sẽ gửi cho bạn câu hỏi của người dùng và câu truy vấn sql và kết quả của câu truy vấn đó (truy vấn đó là để tìm câu trả lời cho câu hỏi của người dùng), bây giờ bạn dựa vào thông tin của kết quả truy vấn để trả lời câu hỏi của người dùng nhé.

Dưới đây là câu hỏi của người dùng:
{question}

Dưới đây là câu truy vấn sql:
{sql}

Dưới đây là kết quả của câu truy vấn sql:
{output}

hãy trả lời và format câu trả lời sao cho nó đẹp nhất, bạn cũng có thể dựa vào kết quả đó đưa ra nhận xét, lời khuyên gì gì đó cho người dùng, nhưng nhớ là câu trả lời của bạn đừng có nhắc lại gì về câu hỏi người dùng, câu truy vấn nhé.

Trường hợp khác nếu câu hỏi của người dùng có gì đó liên quan đến hướng dẫn thực hiện điều gì gì liên quan đến hệ thống (ví dụ hướng dẫn sử dụng web, hướng dẫn vào lớp học, hướng dẫn làm bài kiểm tra, hướng dẫn mua sách) thì hãy bỏ qua toàn bộ những thông tin về sql bên trên mà hãy dựa vào các thông tin hướng dẫn sau để trả lời
Hướng dẫn về cách sử dụng hệ thống: Web site này là một nền tảng cho phép giáo viên và học sinh có thể tương tác với nhau thông qua các lớp học trực tuyến, bài kiểm tra, diễn đàn và thư viện tài liệu. Bạn có thể tham gia vào các lớp học, làm bài kiểm tra, tham gia thảo luận trên diễn đàn và tìm kiếm tài liệu trong thư viện. Để sử dụng hệ thống, bạn cần đăng nhập vào tài khoản của mình. Nếu bạn chưa có tài khoản, hãy đăng ký một tài khoản mới.
Hướng dẫn vào lớp học: để vào lớp hãy tìm đến mục my class, ở đây bạn sẽ tìm các lớp được giảng viên tạo theo mã, hãy xin mã đó và đợi giảng viên duyệt nhé.
Hướng dẫn làm bài kiểm tra : để làm bài kiểm tra bạn cần vào lớp học, đợi đề kiểm tra từ giảng viên, sau đó bài kiểm tra sẽ có trạng thái được kích hoạt hoặc chưa kích hoạt, bạn chỉ có thể làm khi bài kiểm tra đã được kích hoạt, sau khi đã nộp bài hoặc hết thời gian, bạn sẽ không thể làm được nữa.
Hướng dẫn mua sách : hệ thống được tích hợp thư viện online để bạn có thể tìm sách, lưu sách về và đọc trực tuyến trên hệ thống, sách có thể miễn phí hoặc trả phí, nếu trả phí, bạn bám vào nút mua, sau khi quét mã và nhập đúng nội dung chuyển khoản, sách sẽ tự động được lưu.
Hướng dẫn tham gia thảo luận: hệ thống có tich hợp forum, nếu bạn cần hỏi gì hãy cứ lên đó trao đổi nhé.
bạn dựa vào các thông tin đó để viết hướng dẫn nhé.

Trong trường hợp người dùng hỏi câu hỏi dạng " có bài viết nào trong thư viện liên quan đến" bạn hãy xem xét và trả lời dựa trên dữ liệu và có thể tạo một chỗ nút gửi link bài viết đó cho người dùng, với các bài viết trong diễn đàn link chung sẽ là http://127.0.0.1:8000/forum/slug, slug lấy từ cơ sở dữ liệu ở bảng Forum ấy, hoặc sách trong thư viện sẽ là http://127.0.0.1:8000/library/book/book_id/.
Khi người dùng có ý định tìm kiếm bài kiểm tra nào mà họ chưa làm thì hãy tra trong bảng quiz_quizattempt và bảng quiz_quiz và có thể đưa link bài kiểm tra bằng cú pháp sau http://127.0.0.1:8000/myclass/start_quiz/ với id là quiz_id được chèn vào cuối url trên bạn hãy để nút này là bạn có thể bấm vào đây để bắt đầu làm.
"""

# Configuration for Azure AI Inference
ENDPOINT = "https://models.github.ai/inference"
MODEL = os.environ.get("MODEL_ID", "")

# GITHUB_TOKEN = ""
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
# Logger setup
logger = logging.getLogger("chatbot")

# Initialize Azure AI client
client = ChatCompletionsClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(GITHUB_TOKEN),
)

# Function to extract SQL query from AI response
def extract_sql_from_brackets(response):
    # Look for SQL patterns inside square brackets
    pattern = r'\[(.*?)\]'
    matches = re.findall(pattern, response, re.DOTALL)
    
    # Return the first SQL pattern found, or empty string
    if matches:
        sql = matches[0].strip()
        # Remove any quotes that might be in the SQL
        sql = sql.replace('"', '').replace("'", "")
        return sql
    return ""

# Function to run SQL query
def run_query(db_file, query):
    # Chuẩn hóa câu truy vấn về 1 dòng
    query = ' '.join(query.split())

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute(query)

        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            col_names = [description[0] for description in cursor.description]

            if not rows:
                return "Không có kết quả."

            # Ghép tên cột và giá trị tương ứng
            result_lines = []
            for row in rows:
                row_text = '\n'.join(f"{col}: {val}" for col, val in zip(col_names, row))
                result_lines.append(row_text)

            return '\n\n'.join(result_lines)
        else:
            conn.commit()
            return "Truy vấn thực thi thành công."
    except sqlite3.Error as e:
        return f"Lỗi SQL: {str(e)}"
    except Exception as e:
        return f"Lỗi không xác định: {str(e)}"
    finally:
        if conn:
            conn.close()

@csrf_exempt
@require_POST
def chat_api(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({'content': 'Yêu cầu không hợp lệ: Dữ liệu JSON sai định dạng.', 'question': ''}, status=400)

    # Extract user question from either format
    user_question = data.get('message', '')
    if not user_question and 'messages' in data:
        for msg in data.get('messages', []):
            if msg.get('role') == 'user':
                user_question = msg.get('content', '')
                break

    if not user_question:
        return JsonResponse({'content': 'Yêu cầu không hợp lệ: Tin nhắn không được để trống.', 'question': ''}, status=400)

    # Get the current user's ID
    user_id = request.user.id if request.user.is_authenticated else None
    
    # If user is not authenticated, provide a default message
    if not user_id:
        return JsonResponse({
            'content': 'Vui lòng đăng nhập để sử dụng tính năng này.',
            'question': user_question
        })

    # Format system prompt with schema info and user ID
    system_prompt = PROMPT_TEMPLATE.format(
        schema=SCHEMA_DESCRIPTION, 
        question=user_question,
        user_id=user_id
    )

    # Extract other parameters
    temperature = data.get('temperature', 0.8)
    top_p = data.get('top_p', 0.1)
    max_tokens = data.get('max_tokens', 2048)
    model = data.get('model', MODEL)

    try:
        # STEP 1: Get initial AI response
        completion = client.complete(
            messages=[
                SystemMessage(system_prompt),
                UserMessage(user_question),
            ],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            model=model
        )
        
        # Extract response and check for SQL
        if completion and hasattr(completion, 'choices') and completion.choices:
            first_response = completion.choices[0].message.content.strip()
            sql_query = extract_sql_from_brackets(first_response)
            
            # If SQL found, execute it and generate detailed response
            if sql_query and (sql_query.upper().startswith('SELECT') or 
                            sql_query.upper().startswith('INSERT') or 
                            sql_query.upper().startswith('UPDATE') or
                            sql_query.upper().startswith('DELETE')):
                
                # Execute SQL and get second response
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
                query_result = run_query(db_path, sql_query)
                
                second_prompt = PROMPT_TEMPLATE_2.format(
                    question=user_question,
                    sql=sql_query,
                    output=query_result
                )
                
                second_completion = client.complete(
                    messages=[
                        SystemMessage(second_prompt),
                        UserMessage(user_question)
                    ],
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    model=model
                )
                
                if second_completion and hasattr(second_completion, 'choices') and second_completion.choices:
                    final_content = second_completion.choices[0].message.content.strip()
                else:
                    # Fallback to first response if second call fails
                    final_content = first_response.replace(f"[{sql_query}]", "")
            else:
                # For non-system questions, use first response directly
                final_content = first_response
                
                # Remove any empty square brackets that might be in the response
                final_content = re.sub(r'\[\s*\]', '', final_content)
        else:
            logger.error("Azure AI Inference API Error: Unexpected response structure")
            final_content = "Xin lỗi, tôi không thể tạo phản hồi vào lúc này do có sự cố từ dịch vụ AI."
            
    except Exception as e:
        logger.error(f"Azure AI Inference Error: {e}")
        return JsonResponse({'content': f"Lỗi từ dịch vụ AI: {str(e)}", 'question': user_question}, status=500)

    return JsonResponse({'content': final_content, 'question': user_question})
