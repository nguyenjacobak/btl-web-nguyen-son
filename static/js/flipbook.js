// Xử lý PDF và hiệu ứng lật trang

// Biến global để lưu trữ trạng thái
let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;
let totalPages = 0;
let scale = 1.2; // Giảm scale để đảm bảo hiển thị đầy đủ nội dung

// Thêm biến toàn cục để quản lý cache và trạng thái loading
let pagesCache = {}; // Cache các trang đã render
let pagesBeingRendered = {}; // Theo dõi các trang đang được render
let preRenderCount = 4; // Số trang pre-render trước và sau trang hiện tại

// Khởi tạo PDF.js
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

// Hàm khởi tạo bắt đầu tải PDF
document.addEventListener('DOMContentLoaded', function() {
    console.log("Document loaded, starting flipbook initialization");
    console.log("PDF URL:", pdfUrl);
    console.log("Cover image URL:", coverImageUrl);
    
    // Kiểm tra URL hình ảnh
    if (coverImageUrl) {
        // Preload hình ảnh trước khi sử dụng
        const img = new Image();
        img.onload = function() {
            console.log("Cover image loaded successfully");
        };
        img.onerror = function() {
            console.error("Failed to load cover image, will use fallback");
        };
        img.src = coverImageUrl;
    }
    
    loadPDF(pdfUrl);
});

// Hàm tải PDF
async function loadPDF(url) {
    try {
        console.log("Loading PDF from URL:", url);
        
        // Hiển thị loading
        const loadingElement = document.querySelector('.flipbook-loading');
        loadingElement.style.display = 'flex';
        
        // Tải PDF
        const loadingTask = pdfjsLib.getDocument(url);
        pdfDoc = await loadingTask.promise;
        totalPages = pdfDoc.numPages;
        
        console.log("PDF loaded successfully. Total pages:", totalPages);
        
        // Cập nhật UI hiển thị số trang
        document.getElementById('totalPages').textContent = totalPages;
        
        // Khởi tạo sách
        await initializeBook();
        
        return pdfDoc;
    } catch (error) {
        console.error('Error loading PDF:', error);
        document.querySelector('.flipbook-loading').innerHTML = `
            <div>
                <i class="fas fa-exclamation-triangle" style="color: red"></i>
                <p>Không thể tải PDF. Lỗi: ${error.message}</p>
                <p>URL: ${url}</p>
            </div>
        `;
    }
}

// Hàm render một trang PDF thành canvas - được cải tiến với cache
async function renderPage(pageNumber) {
    // Kiểm tra cache trước
    if (pagesCache[pageNumber]) {
        console.log(`Page ${pageNumber} retrieved from cache`);
        return pagesCache[pageNumber];
    }

    // Nếu đang render trang này, đợi kết quả
    if (pagesBeingRendered[pageNumber]) {
        console.log(`Page ${pageNumber} is already being rendered, waiting...`);
        return pagesBeingRendered[pageNumber];
    }

    console.log(`Rendering page ${pageNumber}`);
    
    // Đánh dấu là đang render
    pagesBeingRendered[pageNumber] = new Promise(async (resolve, reject) => {
        try {
            // Lấy trang từ PDF
            const page = await pdfDoc.getPage(pageNumber);
            
            // Tạo canvas mới
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            
            // Tính toán kích thước để vừa với container
            const containerWidth = $('.flipbook-container').width() / 2.25; // Điều chỉnh để có khoảng trống cho gáy sách
            const containerHeight = $('.flipbook-container').height();
            
            // Lấy kích thước gốc của trang PDF
            const viewport = page.getViewport({ scale: 1.0 });
            
            // Tính toán tỷ lệ để vừa với container
            const scaleWidth = containerWidth / viewport.width;
            const scaleHeight = containerHeight / viewport.height;
            
            // Sử dụng tỷ lệ nhỏ hơn để đảm bảo hiển thị toàn bộ nội dung
            const finalScale = Math.min(scaleWidth, scaleHeight) * 0.95; // Giảm 5% để có margin
            
            // Tạo viewport mới với tỷ lệ đã tính
            const scaledViewport = page.getViewport({ scale: finalScale });
            
            // Đặt kích thước canvas
            canvas.height = scaledViewport.height;
            canvas.width = scaledViewport.width;
            
            // Đảm bảo canvas vừa với container
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            canvas.style.objectFit = 'contain';
            
            // Render PDF vào canvas
            const renderContext = {
                canvasContext: context,
                viewport: scaledViewport
            };
            
            await page.render(renderContext).promise;
            console.log(`Page ${pageNumber} rendered successfully`);
            
            // Lưu vào cache và giải phóng biến đang render
            pagesCache[pageNumber] = canvas;
            delete pagesBeingRendered[pageNumber];
            
            resolve(canvas);
        } catch (error) {
            console.error(`Error rendering page ${pageNumber}:`, error);
            delete pagesBeingRendered[pageNumber];
            
            // Tạo canvas hiển thị lỗi
            const errorCanvas = document.createElement('canvas');
            const ctx = errorCanvas.getContext('2d');
            errorCanvas.width = 500;
            errorCanvas.height = 700;
            ctx.fillStyle = '#f8f9fa';
            ctx.fillRect(0, 0, 500, 700);
            ctx.font = '16px Arial';
            ctx.fillStyle = 'red';
            ctx.textAlign = 'center';
            ctx.fillText(`Lỗi hiển thị trang ${pageNumber}`, 250, 350);
            
            resolve(errorCanvas);
        }
    });
    
    return pagesBeingRendered[pageNumber];
}

// Thêm hàm pre-render nhiều trang cùng lúc
async function preRenderPages(centerPage) {
    // Tính toán các trang cần pre-render
    const pagesToRender = [];
    
    // Thêm các trang trước trang hiện tại
    for (let i = Math.max(1, centerPage - preRenderCount); i < centerPage; i++) {
        if (!pagesCache[i] && !pagesBeingRendered[i] && i <= totalPages) {
            pagesToRender.push(i);
        }
    }
    
    // Thêm các trang sau trang hiện tại
    for (let i = centerPage + 1; i <= Math.min(totalPages, centerPage + preRenderCount); i++) {
        if (!pagesCache[i] && !pagesBeingRendered[i]) {
            pagesToRender.push(i);
        }
    }
    
    console.log("Pre-rendering pages:", pagesToRender);
    
    // Render các trang (sử dụng Promise.all để render song song)
    try {
        const renderPromises = pagesToRender.map(pageNum => renderPage(pageNum));
        await Promise.all(renderPromises);
        console.log("Pre-rendering complete");
    } catch (error) {
        console.error("Error during pre-rendering:", error);
    }
}

// Khởi tạo flip book
async function initializeBook() {
    console.log("Initializing flipbook");
    const flipbook = document.getElementById('flipbook');
    const pageWidth = $('.flipbook-container').width() / 2;
    const pageHeight = $('.flipbook-container').height();
    
    console.log("Page dimensions:", pageWidth, pageHeight);
    
    // Làm trống flipbook trước khi thêm phần tử mới
    flipbook.innerHTML = '';
    
    // Hiển thị trang bìa chỉ với hình ảnh (loại bỏ tên sách và tác giả)
    const coverFront = document.createElement('div');
    coverFront.className = 'hard cover-front';
    coverFront.innerHTML = `
        <div class="cover-image-container full-cover">
            <img src="${coverImageUrl}" class="book-image" alt="${bookTitle}" onerror="this.onerror=null; this.src='/static/images/library/default-book.jpg';">
        </div>
    `;
    flipbook.appendChild(coverFront);
    
    // Trang bìa trong
    const hardSecond = document.createElement('div');
    hardSecond.className = 'hard';
    flipbook.appendChild(hardSecond);
    
    // Tạo các trang nội dung
    for (let i = 1; i <= totalPages; i++) {
        const pageDiv = document.createElement('div');
        pageDiv.className = 'page';
        pageDiv.innerHTML = `
            <div class="page-content">
                <div class="page-loading">
                    <i class="fas fa-spinner fa-spin"></i>
                </div>
            </div>
            <div class="page-number">${i}</div>
        `;
        flipbook.appendChild(pageDiv);
    }
    
    // Thêm trang bìa sau
    const hardThird = document.createElement('div');
    hardThird.className = 'hard';
    flipbook.appendChild(hardThird);
    
    const coverBack = document.createElement('div');
    coverBack.className = 'hard cover-back';
    coverBack.innerHTML = '<h2>Kết thúc</h2>';
    flipbook.appendChild(coverBack);
    
    console.log("Flipbook HTML structure created with pages:", totalPages);
    
    try {
        // Khởi tạo turn.js
        console.log("Initializing turn.js");
        $(flipbook).turn({
            width: pageWidth * 2,
            height: pageHeight,
            autoCenter: true,
            display: 'double',
            acceleration: true,
            elevation: 50,
            gradients: true,
            duration: 1000,
            when: {
                turning: function(event, page, view) {
                    console.log("Turning to page:", page, "View:", view);
                    
                    // Cập nhật số trang hiện tại
                    document.getElementById('currentPage').textContent = page;
                    
                    // Cần render trang tiếp theo nếu chưa được render
                    if (page > 2) {
                        // Tính toán số trang cần render dựa trên view (2 trang)
                        const pagesToRender = view.map(v => v - 2); // Trừ 2 vì có 2 trang bìa
                        console.log("Pages to render immediately:", pagesToRender);
                        
                        // Render ngay các trang đang hiển thị
                        pagesToRender.forEach(async (p) => {
                            if (p > 0 && p <= totalPages) {
                                const pageElements = $(flipbook).find('.page');
                                const targetPage = pageElements[p - 1];
                                
                                if (targetPage && !targetPage.hasAttribute('data-rendered')) {
                                    try {
                                        console.log(`Rendering page ${p} for view`);
                                        const canvas = await renderPage(p);
                                        
                                        // Thay thế nội dung loading bằng canvas
                                        const pageContent = targetPage.querySelector('.page-content');
                                        pageContent.innerHTML = '';
                                        pageContent.appendChild(canvas);
                                        
                                        // Đánh dấu trang đã được render
                                        targetPage.setAttribute('data-rendered', 'true');
                                    } catch (error) {
                                        console.error(`Error rendering page ${p}:`, error);
                                    }
                                }
                            }
                        });
                        
                        // Trigger việc pre-render các trang tiếp theo
                        // Sử dụng page là trang trung tâm cho việc pre-render
                        setTimeout(() => preRenderPages(page), 100);
                    }
                },
                turned: function(event, page, view) {
                    console.log('Current page:', page, 'View:', view);
                    
                    // Thêm class để phân biệt trang lẻ/chẵn cho hiệu ứng gáy sách
                    const pages = $(flipbook).find('.page');
                    pages.each(function(index) {
                        const pageWrapper = $(this).parent();
                        if ((index + 3) % 2 === 0) { // +3 vì có 2 trang bìa và index bắt đầu từ 0
                            pageWrapper.addClass('odd');
                        } else {
                            pageWrapper.addClass('even');
                        }
                    });
                    
                    // Quản lý cache để tránh memory leak
                    manageCache(page);
                    
                    // Tiếp tục pre-render các trang xung quanh trang hiện tại sau khi đã lật trang
                    setTimeout(() => preRenderPages(page), 500);
                }
            }
        });
        console.log("Turn.js initialized successfully");
        
        // Pre-render nhiều trang hơn khi bắt đầu
        if (totalPages > 0) {
            console.log("Pre-rendering initial pages");
            
            // Render 2 trang đầu tiên ngay lập tức
            for (let i = 1; i <= Math.min(2, totalPages); i++) {
                const pages = $(flipbook).find('.page');
                if (pages.length >= i) {
                    const page = pages[i-1];
                    console.log(`Rendering initial page ${i}`);
                    
                    try {
                        const canvas = await renderPage(i);
                        const pageContent = page.querySelector('.page-content');
                        pageContent.innerHTML = '';
                        pageContent.appendChild(canvas);
                        page.setAttribute('data-rendered', 'true');
                        console.log(`Initial page ${i} rendered`);
                    } catch (error) {
                        console.error(`Error rendering initial page ${i}:`, error);
                    }
                }
            }
            
            // Pre-render thêm các trang phía sau
            setTimeout(() => preRenderPages(3), 1000);
        }
        
        // Thêm listeners cho nút điều hướng
        document.getElementById('prevBtn').addEventListener('click', function() {
            $(flipbook).turn('previous');
        });
        
        document.getElementById('nextBtn').addEventListener('click', function() {
            $(flipbook).turn('next');
        });
        
        // Xử lý phím mũi tên
        $(document).keydown(function(e) {
            if (e.keyCode == 37) { // Left arrow
                $(flipbook).turn('previous');
            } else if (e.keyCode == 39) { // Right arrow
                $(flipbook).turn('next');
            }
        });
    } catch (error) {
        console.error("Error initializing Turn.js:", error);
        document.querySelector('.flipbook-loading').innerHTML = `
            <div>
                <i class="fas fa-exclamation-triangle" style="color: red"></i>
                <p>Không thể khởi tạo sách điện tử. Lỗi: ${error.message}</p>
            </div>
        `;
        return;
    }
    
    // Ẩn màn hình loading
    document.querySelector('.flipbook-loading').style.display = 'none';
    
    // Cập nhật số trang hiện tại
    document.getElementById('currentPage').textContent = $(flipbook).turn('page');
    console.log("Flipbook initialization complete");
}

// Thêm hàm quản lý cache để tránh memory leak
function manageCache(currentPage) {
    const pagesToKeep = new Set();
    
    // Giữ lại các trang xung quanh currentPage
    for (let i = Math.max(1, currentPage - preRenderCount * 2); i <= Math.min(totalPages, currentPage + preRenderCount * 2); i++) {
        pagesToKeep.add(i);
    }
    
    // Xóa các trang không cần thiết khỏi cache
    Object.keys(pagesCache).forEach(pageNum => {
        pageNum = parseInt(pageNum);
        if (!pagesToKeep.has(pageNum)) {
            console.log(`Removing page ${pageNum} from cache`);
            delete pagesCache[pageNum];
        }
    });
}

// Resize handler
function resizeBook() {
    console.log("Resizing book");
    const flipbook = document.getElementById('flipbook');
    const pageWidth = $('.flipbook-container').width() / 2;
    const pageHeight = $('.flipbook-container').height();
    
    $(flipbook).turn('size', pageWidth * 2, pageHeight);
    $(flipbook).turn('resize');
}

// Xử lý sự kiện resize
window.addEventListener('resize', resizeBook);

// Thêm nút điều chỉnh chất lượng vào UI để người dùng có thể kiểm soát
window.changeRenderQuality = function(quality) {
    switch(quality) {
        case 'low':
            scale = 0.8;
            break;
        case 'medium':
            scale = 1.0;
            break;
        case 'high':
            scale = 1.2;
            break;
    }
    
    // Xóa cache khi thay đổi chất lượng
    pagesCache = {};
    
    // Reload trang hiện tại
    const currentPage = $(flipbook).turn('page');
    preRenderPages(currentPage);
    
    // Thông báo cho người dùng
    alert('Đã thay đổi chất lượng hiển thị. Các trang mới sẽ được hiển thị với chất lượng mới.');
}
