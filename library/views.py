from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
import json
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from .models import Book, Category, SavedBook

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
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            # In ra console để debug
            print(f"Nhận Webhook từ SePay: {data}")
            
            # Lấy thông tin giao dịch
            transaction_id = data.get("id")  # ID giao dịch trên SePay
            content = data.get("content", "")  # Nội dung chuyển khoản
            transfer_amount = data.get("transferAmount")  # Số tiền giao dịch
            transfer_type = data.get("transferType")  # Loại giao dịch (in/out)
            transaction_date = data.get("transactionDate")  # Thời gian giao dịch
            gateway = data.get("gateway")  # Ngân hàng
            
            # Kiểm tra nếu đây là tiền vào (chuyển khoản đến tài khoản)
            if transfer_type != "in":
                print(f"Bỏ qua giao dịch {transaction_id} vì không phải tiền vào")
                return JsonResponse({"message": "Not an incoming transfer"}, status=200)
            
            # Phân tích nội dung thanh toán để tìm book_id và user_id
            # Định dạng mới: "PTITBOOK[book_id][user_id]" - không có ký tự đặc biệt
            try:
                if "PTITBOOK" in content:
                    # Cắt bỏ phần "PTITBOOK" ở đầu
                    payment_info = content.replace("PTITBOOK", "")
                    
                    # Phân tích chuỗi còn lại để lấy book_id và user_id
                    # Giả sử book_id có tối đa 5 chữ số và user_id có phần còn lại
                    if len(payment_info) > 5:
                        book_id = int(payment_info[:5])  # Lấy tối đa 5 chữ số đầu tiên cho book_id
                        user_id = int(payment_info[5:])  # Phần còn lại là user_id
                        
                        print(f"Phát hiện mua sách: book_id={book_id}, user_id={user_id}")
                        
                        # Xử lý mua sách
                        from django.contrib.auth.models import User
                        
                        book = Book.objects.get(id=book_id)
                        user = User.objects.get(id=user_id)
                        
                        # Kiểm tra số tiền thanh toán với giá sách
                        if int(book.price) <= int(transfer_amount):
                            # Tạo SavedBook nếu chưa tồn tại
                            if not SavedBook.objects.filter(user=user, book=book).exists():
                                saved_book = SavedBook.objects.create(user=user, book=book)
                                print(f"Đã lưu sách ID: {book_id} cho người dùng ID: {user_id}")
                                
                                # Lưu thông tin giao dịch (nếu cần)
                                # Có thể tạo model Transaction để lưu chi tiết giao dịch
                                
                                return JsonResponse({"message": "Book purchased successfully"}, status=200)
                            else:
                                print(f"Sách ID: {book_id} đã được lưu cho người dùng ID: {user_id} trước đó")
                                return JsonResponse({"message": "Book already purchased"}, status=200)
                        else:
                            print(f"Số tiền không đủ: Sách giá {book.price}, thanh toán {transfer_amount}")
                            return JsonResponse({"message": "Insufficient payment amount"}, status=200)
                    else:
                        print(f"Nội dung không đủ dài: {content}")
                else:
                    print(f"Không phải giao dịch mua sách: {content}")
            except Book.DoesNotExist:
                print(f"Không tìm thấy sách với ID: {book_id}")
            except User.DoesNotExist:
                print(f"Không tìm thấy người dùng với ID: {user_id}")
            except (IndexError, ValueError) as e:
                print(f"Lỗi khi phân tích nội dung: {str(e)}")
            except Exception as e:
                print(f"Lỗi khi xử lý lưu sách: {str(e)}")
            
            # Trả về phản hồi thành công ngay cả khi không xử lý được giao dịch
            # để tránh SePay gửi lại webhook nhiều lần
            return JsonResponse({"message": "Webhook received but not processed"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            print(f"Lỗi không xác định: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
def check_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            book_id = data.get('book_id')
            amount = data.get('amount')
            
            if not book_id:
                return JsonResponse({'status': 'error', 'message': 'Thiếu ID sách'})
            
            book = Book.objects.get(id=book_id)
            
            # Kiểm tra xem người dùng đã có sách này trong thư viện chưa
            if SavedBook.objects.filter(user=request.user, book=book).exists():
                return JsonResponse({'status': 'success', 'message': 'Sách đã được mua trước đó'})
            
            # Trong môi trường thật, bạn sẽ kiểm tra giao dịch từ SePay ở đây
            # Ví dụ: gọi API của SePay để kiểm tra giao dịch gần đây
            
            # Tìm kiếm giao dịch trong database
            found_payment = False
            
            # TODO: Thêm logic kiểm tra thanh toán thực tế
            
            # Giả lập kiểm tra thanh toán cho môi trường test
            # Trong môi trường thật, hãy bỏ đoạn giả lập này và sử dụng API SePay
            import random
            import time
            
            # Thêm độ trễ để mô phỏng việc kiểm tra
            time.sleep(2)
            
            # Mô phỏng xác suất thanh toán thành công 20% để test
            if random.random() < 0.2:  # 20% xác suất thành công
                found_payment = True
            
            if found_payment:
                # Lưu sách cho người dùng khi xác nhận thanh toán thành công
                if not SavedBook.objects.filter(user=request.user, book=book).exists():
                    SavedBook.objects.create(user=request.user, book=book)
                
                return JsonResponse({'status': 'success', 'message': 'Thanh toán thành công'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Chưa tìm thấy giao dịch thanh toán'})
        except Book.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy sách'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Dữ liệu không hợp lệ'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ'})

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
