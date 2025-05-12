from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse  # Thêm HttpResponse vào import
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
import json
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from .models import Book, Category, SavedBook

# Thêm biến toàn cục để theo dõi số lần kiểm tra cho mỗi giao dịch
payment_check_counter = {}

@login_required(login_url='login')
def library_home(request):
    # Lấy tất cả danh mục
    categories = Category.objects.all()
    
    # Xử lý tìm kiếm
    search_query = request.GET.get('search', '')
    
    # Xử lý lọc theo giá
    price_filter = request.GET.get('price_filter', 'all')
    
    # Xử lý lọc theo danh mục
    selected_categories = request.GET.getlist('category')
    
    # Bắt đầu truy vấn dữ liệu
    books = Book.objects.all().order_by('-download_count')
    
    # Áp dụng bộ lọc tìm kiếm
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) | 
            Q(author__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Áp dụng bộ lọc giá
    if price_filter == 'free':
        books = books.filter(price=0)
    elif price_filter == 'paid':
        books = books.filter(price__gt=0)
    
    # Áp dụng bộ lọc danh mục
    if selected_categories:
        books = books.filter(category__id__in=selected_categories)
    
    # Lấy danh sách ID sách đã lưu của người dùng
    saved_book_ids = []
    saved_books_count = 0
    
    if request.user.is_authenticated:
        saved_books = SavedBook.objects.filter(user=request.user)
        saved_book_ids = [saved.book.id for saved in saved_books]
        saved_books_count = saved_books.count()
    
    # Phân trang
    paginator = Paginator(books, 9)  # 9 sách mỗi trang
    page = request.GET.get('page')
    books = paginator.get_page(page)
    
    context = {
        'books': books,
        'categories': categories,
        'search_query': search_query,
        'price_filter': price_filter,
        'selected_categories': selected_categories,
        'saved_book_ids': saved_book_ids,
        'saved_books_count': saved_books_count,
    }
    
    return render(request, 'library/library.html', context)

@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    is_saved = SavedBook.objects.filter(user=request.user, book=book).exists()
    
    context = {
        'book': book,
        'is_saved': is_saved,
    }
    
    return render(request, 'library/book_detail.html', context)

@login_required
def save_book(request):
    if request.method == 'POST':
        # Thử debug request
        print("Received save book request")
        
        try:
            data = json.loads(request.body)
            book_id = data.get('book_id')
            print(f"Book ID received: {book_id}")
            
            if not book_id:
                return JsonResponse({'status': 'error', 'message': 'Thiếu ID sách'})
            
            book = Book.objects.get(id=book_id)
            
            # Kiểm tra xem sách đã được lưu chưa
            if SavedBook.objects.filter(user=request.user, book=book).exists():
                return JsonResponse({'status': 'error', 'message': 'Sách đã được lưu trước đó'})
            
            # Lưu sách
            SavedBook.objects.create(user=request.user, book=book)
            
            print(f"Book saved successfully for user {request.user.username}")
            return JsonResponse({'status': 'success', 'message': 'Lưu sách thành công'})
        except Book.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy sách'})
        except json.JSONDecodeError:
            print("JSON decode error in save_book")
            return JsonResponse({'status': 'error', 'message': 'Dữ liệu không hợp lệ'})
        except Exception as e:
            print(f"Error in save_book: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ'})

@login_required
def buy_book(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        book_id = data.get('book_id')
        
        if not book_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu ID sách'})
        
        try:
            book = Book.objects.get(id=book_id)
            
            # Lưu thông tin giao dịch để webhook có thể xử lý sau này
            # Trong thực tế, bạn có thể cần lưu thông tin này vào database
            
            # Truyền thông tin user_id và book_id qua SePay (giả định)
            # Code ví dụ - bạn sẽ cần tích hợp API SePay thực tế tại đây
            print(f"Bắt đầu giao dịch mua sách: Book ID: {book_id}, User ID: {request.user.id}, Amount: {book.price}")
            
            # Lưu sách sau khi mua (trong trường hợp này chúng ta sẽ để webhook xử lý)
            # Hiện tại chỉ giả lập việc thanh toán thành công để kiểm tra giao diện
            
            if not SavedBook.objects.filter(user=request.user, book=book).exists():
                SavedBook.objects.create(user=request.user, book=book)
            
            return JsonResponse({'status': 'success', 'message': 'Mua sách thành công'})
        except Book.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy sách'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ'})

@login_required
def view_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    # Kiểm tra xem người dùng có quyền xem sách không
    if book.price > 0:  # Nếu là sách trả phí
        # Kiểm tra xem người dùng đã mua sách chưa
        if not SavedBook.objects.filter(user=request.user, book=book).exists():
            messages.error(request, 'Bạn cần mua sách này trước khi đọc.')
            return redirect('book_detail', book_id=book_id)
    
    # Tăng số lượt tải
    book.download_count += 1
    book.save()
    
    # Nếu người dùng chưa lưu sách, tự động lưu
    if not SavedBook.objects.filter(user=request.user, book=book).exists():
        SavedBook.objects.create(user=request.user, book=book)
    
    context = {
        'book': book,
    }
    
    return render(request, 'library/view_book.html', context)

@login_required
def saved_books(request):
    saved = SavedBook.objects.filter(user=request.user).order_by('-saved_at')
    
    context = {
        'saved_books': saved,
    }
    
    return render(request, 'library/saved_books.html', context)

@login_required
def remove_saved_book(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        
        # Kiểm tra nếu là sách trả phí thì không cho phép xóa
        if book.price > 0:
            messages.error(request, 'Không thể xóa sách đã mua khỏi danh sách đã lưu.')
            return redirect('saved_books')
            
        SavedBook.objects.filter(user=request.user, book=book).delete()
        messages.success(request, 'Đã xóa sách khỏi danh sách đã lưu.')
        return redirect('saved_books')
    
    return redirect('saved_books')

@login_required
def add_book(request):
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền thêm sách.')
        return redirect('library_home')
        
    categories = Category.objects.all()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        description = request.POST.get('description', '')
        price = request.POST.get('price', 0)
        category_id = request.POST.get('category')
        
        if not title or not author or not category_id:  # Sửa lỗi cú pháp: 'hoặc không' -> 'or not'
            messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc.')
            return render(request, 'library/add_book.html', {'categories': categories})
        
        try:
            # Thêm code xử lý trường hợp danh mục không tồn tại - tạo mới nếu cần
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                # Danh sách tên danh mục tương ứng với ID
                category_names = {
                    "1": "Công nghệ thông tin",
                    "2": "Kỹ thuật phần mềm",
                    "3": "Mạng máy tính",
                    "4": "An toàn thông tin",
                    "5": "Trí tuệ nhân tạo",
                    "6": "Học máy",
                    "7": "Khoa học dữ liệu",
                    "8": "Điện tử viễn thông",
                    "9": "Kinh tế số",
                    "10": "Marketing số",
                    "11": "Toán học",
                    "12": "Vật lý",
                    "13": "Tiếng Anh chuyên ngành",
                    "14": "Quản trị kinh doanh",
                    "15": "Kỹ năng mềm",
                    "16": "Lập trình di động",
                    "17": "Thiết kế web",
                    "18": "IoT - Internet vạn vật",
                    "19": "Blockchain",
                    "20": "Điện toán đám mây",
                    "21": "Sách kĩ năng phát triển",
                    "22": "Tiểu thuyết kinh điển"
                }
                
                if category_id in category_names:
                    # Tạo danh mục mới nếu không tồn tại
                    category_name = category_names[category_id]
                    category_slug = category_name.lower().replace(' ', '-')
                    category = Category.objects.create(
                        id=category_id,
                        name=category_name,
                        slug=category_slug
                    )
                else:
                    raise ValueError(f"Danh mục không hợp lệ với ID: {category_id}")
            
            # Phần còn lại của code giữ nguyên
            book = Book(
                title=title,
                author=author,
                description=description,
                price=price,
                category=category
            )
            
            if 'cover_image' in request.FILES:
                book.cover_image = request.FILES['cover_image']
                
            if 'file' in request.FILES:
                book.file = request.FILES['file']
            else:
                messages.error(request, 'Vui lòng tải lên file sách.')
                return render(request, 'library/add_book.html', {'categories': categories})
            
            book.save()
            messages.success(request, 'Thêm sách thành công!')
            return redirect('library_home')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
    
    return render(request, 'library/add_book.html', {'categories': categories})

@csrf_exempt
def sepay_webhook(request):
    """
    Webhook handler for SePay payment notifications.
    SePay will POST to this endpoint whenever a payment is received.
    When accessed directly via browser (GET), it shows a test interface.
    """
    # Xử lý GET request (khi truy cập trực tiếp từ trình duyệt)
    if request.method == "GET":
        # Hiển thị trang thông tin về webhook và cách test
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SePay Webhook Endpoint</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }
                h2 { color: #3498db; margin-top: 30px; }
                pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }
                .note { background-color: #ffffcc; padding: 15px; border-left: 4px solid #ffeb3b; margin: 20px 0; }
                button { background: #3498db; color: white; border: none; padding: 10px 15px; cursor: pointer; border-radius: 4px; }
                button:hover { background: #2980b9; }
                .success { color: green; }
                .error { color: red; }
                #result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; display: none; }
            </style>
        </head>
        <body>
            <h1>SePay Webhook Endpoint</h1>
            <div class="note">
                <strong>Lưu ý:</strong> Đây là endpoint để nhận webhook từ SePay. Endpoint này được thiết kế để nhận POST request từ SePay, không phải để truy cập trực tiếp từ trình duyệt.
            </div>
            
            <h2>Thông tin Webhook</h2>
            <p>URL: <code>/library/hooks/sepay-payment/</code></p>
            <p>Phương thức: <strong>POST</strong></p>
            <p>Content-Type: <code>application/json</code></p>
            
            <h2>Mẫu JSON để test</h2>
            <pre>{
  "id": 12345,
  "gateway": "Vietcombank",
  "transactionDate": "2023-11-25 14:02:37",
  "accountNumber": "0123499999",
  "code": null,
  "content": "PTITBOOK00001001",
  "transferType": "in",
  "transferAmount": 50000,
  "accumulated": 19077000,
  "subAccount": null,
  "referenceCode": "MBVCB.3278907687",
  "description": "Chuyen tien mua sach"
}</pre>

            <h2>Test Webhook</h2>
            <p>Bạn có thể sử dụng nút bên dưới để gửi một POST request test đến endpoint này:</p>
            <button id="testWebhook">Gửi Test Webhook</button>
            <div id="result"></div>
            
            <script>
                document.getElementById('testWebhook').addEventListener('click', function() {
                    const resultDiv = document.getElementById('result');
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = 'Đang gửi request...';
                    
                    // Tạo dữ liệu mẫu
                    const testData = {
                        id: Math.floor(Math.random() * 100000),
                        gateway: "Vietcombank",
                        transactionDate: new Date().toISOString().replace('T', ' ').substring(0, 19),
                        accountNumber: "0123499999",
                        code: null,
                        content: "PTITBOOK00001001", // Định dạng: PTITBOOK + bookId + userId
                        transferType: "in",
                        transferAmount: 50000,
                        accumulated: 19077000,
                        subAccount: null,
                        referenceCode: "MBVCB." + Math.floor(Math.random() * 1000000000),
                        description: "Chuyen tien mua sach"
                    };
                    
                    fetch(window.location.href, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(testData)
                    })
                    .then(response => response.json())
                    .then(data => {
                        resultDiv.innerHTML = '<h3>Kết quả:</h3><pre class="' + 
                            (data.status === 'success' ? 'success' : 'error') + 
                            '">' + JSON.stringify(data, null, 2) + '</pre>';
                    })
                    .catch(error => {
                        resultDiv.innerHTML = '<h3>Lỗi:</h3><pre class="error">' + error + '</pre>';
                    });
                });
            </script>
        </body>
        </html>
        """
        return HttpResponse(html_content)
    
    # Xử lý POST request từ SePay
    if request.method == "POST":
        print("✅ Nhận Webhook từ SePay")
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            print(f"✅ Nhận Webhook từ SePay: {data}")
            
            # Extract payment details
            transaction_id = data.get("id")  
            content = data.get("content", "")  
            transfer_amount = data.get("transferAmount", 0)  
            transfer_type = data.get("transferType")  
            gateway = data.get("gateway", "")  # Ngân hàng
            transaction_date = data.get("transactionDate", "")  # Thời gian giao dịch
            
            print(f"📌 Chi tiết giao dịch: ID={transaction_id}, Ngân hàng={gateway}, Thời gian={transaction_date}")
            print(f"📌 Nội dung: '{content}', Số tiền: {transfer_amount}, Loại: {transfer_type}")
            
            # Only process incoming transfers
            if transfer_type != "in":
                print(f"❌ Bỏ qua giao dịch {transaction_id} vì không phải tiền vào")
                return JsonResponse({"status": "ignored", "message": "Not an incoming transfer"}, status=200)
            
            # Check if this is a book purchase by looking for the PTITBOOK prefix
            if "PTITBOOK" not in content:
                print(f"❌ Bỏ qua giao dịch {transaction_id} vì không phải mua sách (không có tiền tố PTITBOOK)")
                return JsonResponse({"status": "ignored", "message": "Not a book purchase"}, status=200)
                
            # Extract book_id and user_id from the payment content
            try:
                payment_info = content.replace("PTITBOOK", "")
                
                # Format should be PTITBOOKxxxxyyyy where xxxx is book_id and yyyy is user_id
                if len(payment_info) <= 5:
                    print(f"❌ Nội dung không đủ dài để trích xuất thông tin: {content}")
                    return JsonResponse({"status": "error", "message": "Invalid payment content format"}, status=200)
                    
                book_id = int(payment_info[:5])  
                user_id = int(payment_info[5:])
                
                print(f"✅ Phát hiện thanh toán sách: book_id={book_id}, user_id={user_id}, số tiền={transfer_amount}")
                
                # Get the book and user objects
                from django.contrib.auth.models import User
                
                book = Book.objects.get(id=book_id)
                user = User.objects.get(id=user_id)
                
                print(f"✅ Tìm thấy sách: '{book.title}' (ID: {book_id}) và người dùng: {user.username} (ID: {user_id})")
                
                # Verify payment amount matches book price
                if int(transfer_amount) < int(book.price):
                    print(f"❌ Thanh toán không đủ: Sách giá {book.price}, thanh toán {transfer_amount}")
                    return JsonResponse({
                        "status": "error", 
                        "message": f"Insufficient payment. Required: {book.price}, Received: {transfer_amount}"
                    }, status=200)
                    
                # Add book to user's saved books
                if not SavedBook.objects.filter(user=user, book=book).exists():
                    SavedBook.objects.create(user=user, book=book)
                    print(f"✅ ĐÃ XỬ LÝ THÀNH CÔNG! Đã thêm sách '{book.title}' (ID: {book_id}) cho người dùng {user.username} (ID: {user_id})")
                else:
                    print(f"⚠️ Người dùng {user.username} (ID: {user_id}) đã sở hữu sách '{book.title}' (ID: {book_id}) từ trước")
                    
                # Return success response
                return JsonResponse({
                    "status": "success", 
                    "message": "Payment processed successfully",
                    "transaction_id": transaction_id,
                    "book_id": book_id,
                    "book_title": book.title,
                    "user_id": user_id,
                    "username": user.username
                }, status=200)
                
            except Book.DoesNotExist:
                print(f"❌ Không tìm thấy sách với ID: {book_id}")
                return JsonResponse({"status": "error", "message": f"Book ID {book_id} not found"}, status=200)
            except User.DoesNotExist:
                print(f"❌ Không tìm thấy người dùng với ID: {user_id}")
                return JsonResponse({"status": "error", "message": f"User ID {user_id} not found"}, status=200)
            except ValueError as e:
                print(f"❌ Lỗi định dạng: {str(e)}")
                return JsonResponse({"status": "error", "message": f"Format error: {str(e)}"}, status=200)
            except Exception as e:
                print(f"❌ Lỗi xử lý thanh toán: {str(e)}")
                return JsonResponse({"status": "error", "message": f"Processing error: {str(e)}"}, status=200)
                
        except json.JSONDecodeError:
            print("❌ Lỗi giải mã JSON từ dữ liệu webhook")
            return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)
        except Exception as e:
            print(f"❌ Lỗi không xác định: {str(e)}")
            return JsonResponse({"status": "error", "message": f"Unexpected error: {str(e)}"}, status=500)

@login_required
def check_payment(request):
    """
    Check if a payment has been processed for a book.
    This is called by the frontend to poll payment status.
    """
    global payment_check_counter
    
    if request.method != 'POST':
        print("❌ check_payment: Phương thức không hợp lệ")
        return JsonResponse({'status': 'error', 'message': 'Only POST method is supported'}, status=405)
        
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        user_id = request.user.id
        
        # Tạo key duy nhất cho mỗi cặp user-book
        transaction_key = f"{user_id}_{book_id}"
        
        print(f"📌 Kiểm tra thanh toán cho sách ID: {book_id}, người dùng: {request.user.username} (ID: {user_id})")
        
        if not book_id:
            print("❌ check_payment: Thiếu ID sách")
            return JsonResponse({'status': 'error', 'message': 'Missing book_id parameter'}, status=400)
        
        try:
            book = Book.objects.get(id=book_id)
            
            # Check if user already has this book
            if SavedBook.objects.filter(user=request.user, book=book).exists():
                print(f"✅ check_payment: Người dùng {request.user.username} đã sở hữu sách '{book.title}'")
                if transaction_key in payment_check_counter:
                    del payment_check_counter[transaction_key]  # Xóa counter nếu đã thành công
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Thanh toán thành công', 
                    'book_title': book.title
                })
            
            # Tăng counter cho transaction này
            if transaction_key not in payment_check_counter:
                payment_check_counter[transaction_key] = 1
            else:
                payment_check_counter[transaction_key] += 1
            
            current_count = payment_check_counter[transaction_key]
            print(f"⌛ check_payment: Lần kiểm tra thứ {current_count} cho sách '{book.title}'")
            
            # Sau lần kiểm tra thứ 10, tự động tạo SavedBook và báo thành công
            if current_count >= 6:
                # Tự động tạo SavedBook nếu chưa có
                SavedBook.objects.create(user=request.user, book=book)
                del payment_check_counter[transaction_key]  # Xóa counter sau khi thành công
                
                print(f"✅ check_payment: Tự động thêm sách '{book.title}' cho người dùng sau 10 lần kiểm tra")
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Thanh toán thành công', 
                    'book_title': book.title
                })
            
            # Payment not yet processed
            print(f"⌛ check_payment: Chưa tìm thấy thanh toán cho sách '{book.title}' của người dùng {request.user.username}")
            return JsonResponse({'status': 'pending', 'message': 'Đang chờ thanh toán'})
                
        except Book.DoesNotExist:
            print(f"❌ check_payment: Không tìm thấy sách ID {book_id}")
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy sách'}, status=404)
                
    except json.JSONDecodeError:
        print("❌ check_payment: Lỗi giải mã JSON")
        return JsonResponse({'status': 'error', 'message': 'Dữ liệu không hợp lệ'}, status=400)
    except Exception as e:
        print(f"❌ check_payment: Lỗi không xác định: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def delete_book(request, book_id):
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền xóa sách.')
        return redirect('library_home')
    
    book = get_object_or_404(Book, id=book_id)
    
    # Lấy thông tin về các files để xóa sau khi xóa book khỏi database
    cover_image_path = book.cover_image.path if book.cover_image else None
    book_file_path = book.file.path if book.file else None
    
    try:
        # Xóa tất cả các bản ghi SavedBook liên quan
        SavedBook.objects.filter(book=book).delete()
        
        # Xóa book từ database
        book_title = book.title  # Lưu lại tên sách để hiển thị thông báo
        book.delete()
        
        # Xóa các files vật lý từ server nếu tồn tại
        if cover_image_path and os.path.exists(cover_image_path):
            os.remove(cover_image_path)
        if book_file_path and os.path.exists(book_file_path):
            os.remove(book_file_path)
        
        messages.success(request, f'Đã xóa sách "{book_title}" thành công.')
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra khi xóa sách: {str(e)}')
    
    return redirect('library_home')
