document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing...");
    
    // Add floating shapes to enhance the glassmorphism effect
    addFloatingShapes();
    
    // Xử lý filter
    const filterButton = document.querySelector('.card-body .glass-btn');
    if (filterButton) {
        filterButton.addEventListener('click', function() {
            // Lấy các giá trị filter
            const categories = Array.from(document.querySelectorAll('input[type="checkbox"][id^="category"]:checked')).map(cb => cb.value);
            const bookType = document.querySelector('input[name="bookType"]:checked').value;
            const formats = Array.from(document.querySelectorAll('input[type="checkbox"][id^="format"]:checked')).map(cb => cb.value);
            
            // Thêm hiệu ứng khi nhấn nút
            this.classList.add('filter-button-active');
            setTimeout(() => {
                this.classList.remove('filter-button-active');
            }, 300);
            
            // Log ra để debug
            console.log('Filter applied:', { categories, bookType, formats });
            
            // TODO: Gửi request AJAX để lấy sách phù hợp với bộ lọc
        });
    }
    
    // Xử lý nút thêm vào danh sách yêu thích
    const favoriteButtons = document.querySelectorAll('.glass-btn-danger-sm');
    favoriteButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Toggle trạng thái active của nút
            this.classList.toggle('active');
            const isActive = this.classList.contains('active');
            
            // Hiệu ứng khi nhấn
            this.style.transform = 'scale(0.9)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
            
            // Thay đổi style dựa trên trạng thái
            if (isActive) {
                this.style.background = 'rgba(239, 68, 68, 0.9)';
            } else {
                this.style.background = 'rgba(239, 68, 68, 0.7)';
            }
            
            // TODO: Gửi request AJAX để lưu/xóa sách khỏi danh sách yêu thích
        });
    });
    
    // Xử lý form thêm sách mới (cho admin)
    const addBookForm = document.getElementById('addBookForm');
    if (addBookForm) {
        const submitButton = document.querySelector('button[form="addBookForm"]');
        submitButton.addEventListener('click', function() {
            // Kiểm tra validation của form
            if (addBookForm.checkValidity()) {
                // Thêm hiệu ứng loading
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý';
                this.disabled = true;
                
                // Giả lập xử lý backend
                setTimeout(() => {
                    // Đóng modal sau khi thêm sách thành công
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addBookModal'));
                    modal.hide();
                    
                    // Hiển thị thông báo thành công
                    showToast('Thêm sách thành công!');
                    
                    // Khôi phục nút
                    this.innerHTML = 'Thêm sách';
                    this.disabled = false;
                }, 1500);
                
                // TODO: Gửi form data qua AJAX để thêm sách mới
            } else {
                // Kích hoạt validation của trình duyệt
                addBookForm.reportValidity();
            }
        });
    }
    
    // Xử lý thông báo
    initializeToasts();
    
    // Xử lý nút lưu sách
    initializeSaveBookButtons();
    
    // Xử lý nút mua sách
    initializeBuyBookButtons();
    
    // Animated scroll effect for book cards
    animateOnScroll();
    window.addEventListener('scroll', animateOnScroll);
});

// Add floating shapes to enhance the glassmorphism effect
function addFloatingShapes() {
    const floatingShapes = document.querySelector('.floating-shapes');
    
    // Create multiple shapes
    for (let i = 0; i < 15; i++) {
        const shape = document.createElement('div');
        const size = Math.random() * 80 + 40; // 40-120px
        
        shape.style.position = 'absolute';
        shape.style.width = `${size}px`;
        shape.style.height = `${size}px`;
        shape.style.borderRadius = '50%';
        shape.style.background = `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 0.05)`;
        shape.style.top = `${Math.random() * 100}%`;
        shape.style.left = `${Math.random() * 100}%`;
        shape.style.animation = `floatBubble ${Math.random() * 10 + 15}s infinite ease-in-out`;
        shape.style.animationDelay = `${Math.random() * 5}s`;
        shape.style.backdropFilter = 'blur(8px)';
        shape.style.border = '1px solid rgba(255, 255, 255, 0.1)';
        
        floatingShapes.appendChild(shape);
    }
    
    // Add CSS animation to document if not exists
    if (!document.getElementById('float-animation')) {
        const style = document.createElement('style');
        style.id = 'float-animation';
        style.textContent = `
            @keyframes floatBubble {
                0%, 100% {
                    transform: translateY(0) translateX(0) rotate(0deg);
                }
                25% {
                    transform: translateY(-30px) translateX(15px) rotate(5deg);
                }
                50% {
                    transform: translateY(10px) translateX(30px) rotate(10deg);
                }
                75% {
                    transform: translateY(20px) translateX(15px) rotate(5deg);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Show toast notification
function showToast(message) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toastEl = document.createElement('div');
    toastEl.className = 'toast glass-toast';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
        <div class="toast-header glass-toast-header">
            <i class="fas fa-check-circle me-2 text-success"></i>
            <strong class="me-auto">Thông báo</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toastEl);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 3000
    });
    toast.show();
    
    // Remove toast element after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

// Animate elements when they come into view
function animateOnScroll() {
    const cards = document.querySelectorAll('.glass-book-card');
    
    cards.forEach(card => {
        const cardTop = card.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;
        
        if (cardTop < windowHeight * 0.9) {
            card.classList.add('animate__animated', 'animate__fadeInUp');
            card.style.opacity = 1;
        }
    });
}

// Add CSS class for animation library if not already included
function addAnimationStyles() {
    const head = document.head;
    const animateCSS = document.querySelector('link[href*="animate.css"]');
    
    if (!animateCSS) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css';
        head.appendChild(link);
        
        // Also add custom animation styles
        const style = document.createElement('style');
        style.textContent = `
            .glass-book-card {
                opacity: 0;
                transition: opacity 0.3s;
            }
            .animate__fadeInUp {
                animation-duration: 0.6s;
            }
        `;
        head.appendChild(style);
    }
}

// Call to add animation styles
addAnimationStyles();

// Khởi tạo các nút lưu sách
function initializeSaveBookButtons() {
    console.log("Initializing save buttons...");
    const saveButtons = document.querySelectorAll('.save-book-btn');
    console.log("Found save buttons:", saveButtons.length);
    
    saveButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            console.log("Save button clicked");
            e.preventDefault();
            const bookId = this.getAttribute('data-book-id');
            console.log("Book ID:", bookId);
            saveBook(bookId, this);
        });
    });
}

// Khởi tạo các nút mua sách
function initializeBuyBookButtons() {
    const buyButtons = document.querySelectorAll('.buy-book-btn');
    buyButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const bookId = this.getAttribute('data-book-id');
            const price = this.getAttribute('data-price');
            
            if (confirm(`Bạn có muốn mua sách này với giá ${price} VNĐ không?`)) {
                buyBook(bookId, this);
            }
        });
    });
}

// Lưu sách - kết nối với backend
function saveBook(bookId, button) {
    console.log("saveBook function called with ID:", bookId);
    
    // Thêm hiệu ứng đang xử lý
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    // Lấy CSRF token từ element
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    console.log("CSRF Token:", csrftoken);
    
    // Gửi request AJAX đến backend
    fetch('/library/save-book/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            'book_id': bookId
        })
    })
    .then(response => {
        console.log("Response status:", response.status);
        return response.json();
    })
    .then(data => {
        console.log("Response data:", data);
        
        if (data.status === 'success') {
            // Hiển thị thông báo thành công
            alert('Đã lưu sách thành công!');
            
            // Tải lại trang sau khi lưu thành công
            window.location.reload();
        } else {
            // Hiển thị thông báo lỗi
            alert(data.message || 'Có lỗi xảy ra!');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-bookmark"></i> Lưu';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Có lỗi xảy ra khi lưu sách!');
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-bookmark"></i> Lưu';
    });
}

// Mua sách - kết nối với backend
function buyBook(bookId, button) {
    // Thêm hiệu ứng đang xử lý
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    // Gửi request AJAX đến backend
    fetch('/library/buy-book/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'book_id': bookId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Thay đổi nút thành "Đã mua"
            button.classList.remove('glass-btn-primary-sm');
            button.classList.add('book-saved');
            button.innerHTML = '<i class="fas fa-check"></i> Đã mua';
            
            // Thêm link đọc sách
            const btnGroup = button.closest('.btn-group');
            if (btnGroup) {
                if (!btnGroup.querySelector('.glass-btn-primary-sm')) {
                    const readBtn = document.createElement('a');
                    readBtn.className = 'glass-btn-primary-sm';
                    readBtn.href = `/library/view-book/${bookId}/`;
                    readBtn.innerHTML = '<i class="fas fa-book-open"></i> Đọc';
                    btnGroup.insertBefore(readBtn, button);
                }
            }
            
            // Hiển thị thông báo thành công
            showToast('Mua sách thành công!', 'success');
        } else {
            // Hiển thị thông báo lỗi
            showToast(data.message || 'Có lỗi xảy ra!', 'danger');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-shopping-cart"></i> Mua';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Có lỗi xảy ra khi mua sách!', 'danger');
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-shopping-cart"></i> Mua';
    });
}

// Khởi tạo toast messages
function initializeToasts() {
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        alerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toastEl = document.createElement('div');
    toastEl.className = 'toast';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    // Set toast class based on type
    let iconClass = 'text-info';
    let icon = 'info-circle';
    
    if (type === 'success') {
        iconClass = 'text-success';
        icon = 'check-circle';
    } else if (type === 'danger') {
        iconClass = 'text-danger';
        icon = 'exclamation-circle';
    }
    
    toastEl.innerHTML = `
        <div class="toast-header">
            <i class="fas fa-${icon} me-2 ${iconClass}"></i>
            <strong class="me-auto">Thông báo</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toastEl);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 5000
    });
    toast.show();
    
    // Remove toast element after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

// Helper function để lấy cookie (cho CSRF token)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Animate elements when they come into view
function animateOnScroll() {
    const cards = document.querySelectorAll('.glass-book-card');
    
    cards.forEach(card => {
        const cardTop = card.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;
        
        if (cardTop < windowHeight * 0.9) {
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }
    });
}

// Đảm bảo các function được khởi tạo khi trang đã tải xong
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing save buttons');
    
    // Khởi tạo các nút lưu sách
    const saveButtons = document.querySelectorAll('.save-book-btn');
    console.log('Found save buttons:', saveButtons.length);
    
    saveButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const bookId = this.getAttribute('data-book-id');
            console.log('Save button clicked for book ID:', bookId);
            saveBook(bookId, this);
        });
    });
});
