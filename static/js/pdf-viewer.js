// OCR A-Level Computer Science AI Tutor - PDF Viewer

/*
 * HOW TO ADD YOUR OWN PDF TO THE VIEWER:
 * 
 * 1. Upload your PDF file to the 'resources' directory of the project
 *    - You can do this through the admin interface (Admin > Upload)
 *    - Or directly copy the PDF file to the resources folder
 * 
 * 2. Add an entry to the topicToPdfMap below:
 *    - The key should be the topic code (e.g., "1.1.1")
 *    - The value should be an object with:
 *      - file: the filename of your PDF (e.g., "my-notes.pdf")
 *      - page: the starting page number (usually 1)
 * 
 * 3. Example:
 *    "2.1.1": { file: "my-custom-notes.pdf", page: 1 }
 * 
 * 4. If you want to use a single PDF for all topics, you can add it as:
 *    "default": { file: "complete-notes.pdf", page: 1 }
 *    This will be used when no specific mapping is found for a topic
 */

// Elements
let pdfViewer;
let pdfContainer;
let currentPdf = null;
let currentPage = 1;
let totalPages = 0;
let pdfDoc = null;

// Topic to PDF mapping
const topicToPdfMap = {
    // Default PDF for all topics (uncomment and modify to use a single PDF)
    "default": { file: "Comp-Sci-Notes.pdf", page: 1 },
    
    // Component 01: Computer Systems
    "1.1.1": { file: "1.1.1. Structure and Function of the Processor.pdf", page: 1 },
    "1.1.2": { file: "1.1.2. Types of Processor.pdf", page: 1 },
    "1.1.3": { file: "1.1.3. Input, Output and Storage.pdf", page: 1 },
    "1.2.1": { file: "1.2.1. Systems Software.pdf", page: 1 },
    "1.2.2": { file: "1.2.2. Applications Generation.pdf", page: 1 },
    "1.2.3": { file: "1.2.3. Software Development.pdf", page: 1 },
    "1.2.4": { file: "1.2.4. Types of Programming Language.pdf", page: 1 },
    "1.3.1": { file: "1.3.1. Compression, Encryption and Hashing.pdf", page: 1 },
    "1.3.2": { file: "1.3.2. Databases.pdf", page: 1 },
    "1.3.3": { file: "1.3.3. Networks.pdf", page: 1 },
    "1.3.4": { file: "1.3.4. Web Technologies.pdf", page: 1 },
    "1.4.1": { file: "1.4.1. Data Types.pdf", page: 1 },
    "1.4.2": { file: "1.4.2. Data Structures.pdf", page: 1 },
    "1.4.3": { file: "1.4.3. Boolean Algebra.pdf", page: 1 },
    "1.5.1": { file: "1.5.1. Computing Related Legislation.pdf", page: 1 },
    "1.5.2": { file: "1.5.2. Moral and Ethical Issues.pdf", page: 1 },
    
    // Component 02: Algorithms and Programming
    "2.1.1": { file: "2.1.1. Thinking Abstractly.pdf", page: 1 },
    "2.1.2": { file: "2.1.2. Thinking Ahead.pdf", page: 1 },
    "2.1.3": { file: "2.1.3. Thinking Procedurally.pdf", page: 1 },
    "2.1.4": { file: "2.1.4. Thinking Logically.pdf", page: 1 },
    "2.1.5": { file: "2.1.5. Thinking Concurrently.pdf", page: 1 },
    "2.2.1": { file: "2.2.1. Programming Techniques.pdf", page: 1 },
    "2.2.2": { file: "2.2.2. Computational Methods.pdf", page: 1 },
    "2.3.1": { file: "2.3.1. Analysis, Design and Comparison of Algorithms.pdf", page: 1 },
    "2.3.2": { file: "2.3.2. Algorithms for the Main Data Structures.pdf", page: 1 },
    "2.3.3": { file: "2.3.3. Sorting Algorithms.pdf", page: 1 },
    "2.3.4": { file: "2.3.4. Searching Algorithms.pdf", page: 1 },
    "2.3.5": { file: "2.3.5. Path Finding Algorithms.pdf", page: 1 },
    
    // Exam Resources
    "exam": { file: "703604-examiners-report-algorithms-and-programming.pdf", page: 1 }
};

// Initialize PDF viewer
function initPdfViewer() {
    pdfContainer = document.getElementById('pdf-container');
    pdfViewer = document.getElementById('pdf-viewer');
    
    // Initialize PDF.js
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    
    // Set up navigation buttons
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderPage(currentPage);
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderPage(currentPage);
        }
    });
    
    document.getElementById('page-num').addEventListener('change', (e) => {
        const pageNum = parseInt(e.target.value);
        if (pageNum >= 1 && pageNum <= totalPages) {
            currentPage = pageNum;
            renderPage(currentPage);
        }
    });
    
    // Set up the dock toggle button for PDF sidebar
    const pdfSidebar = document.getElementById('pdf-sidebar');
    const mainContent = document.querySelector('.main-content');
    const pageContainer = document.querySelector('.page-with-pdf-and-chat');
    const dockToggleBtn = document.getElementById('pdf-dock-toggle');
    
    // Initialize sidebar state (default is docked)
    // Only change the state if explicitly set to false in localStorage
    const savedState = localStorage.getItem('pdf-sidebar-docked');
    
    // If the user has previously set a preference, use that
    if (savedState === 'false') {
        pdfSidebar.classList.remove('docked');
        pageContainer.classList.remove('notes-docked');
    } else {
        // Otherwise ensure the docked state is applied
        pdfSidebar.classList.add('docked');
        pageContainer.classList.add('notes-docked');
        localStorage.setItem('pdf-sidebar-docked', 'true');
    }
    
    // Set up dock toggle button
    dockToggleBtn.addEventListener('click', () => {
        const isCurrentlyDocked = pdfSidebar.classList.contains('docked');
        
        if (isCurrentlyDocked) {
            // Expand the sidebar
            pdfSidebar.classList.remove('docked');
            pageContainer.classList.remove('notes-docked');
            localStorage.setItem('pdf-sidebar-docked', 'false');
        } else {
            // Dock the sidebar
            pdfSidebar.classList.add('docked');
            pageContainer.classList.add('notes-docked');
            localStorage.setItem('pdf-sidebar-docked', 'true');
        }
        
        // Re-render the current page after a slight delay to allow the layout to update
        setTimeout(() => {
            if (pdfDoc) {
                renderPage(currentPage);
            }
        }, 300);
    });
    
    // Load PDF based on current topic
    loadPdfForTopic(topicCode);
}

// Load PDF for a specific topic
function loadPdfForTopic(topicCode) {
    // Find the matching PDF file for this topic
    // First try exact match
    let pdfInfo = topicToPdfMap[topicCode];
    
    // If no exact match, try with just the main topic code (e.g., "1.1.1" instead of "1.1.1.a")
    if (!pdfInfo) {
        const topicPrefix = topicCode.split('.').slice(0, 3).join('.');
        pdfInfo = topicToPdfMap[topicPrefix];
    }
    
    // If still no match, try with just the chapter and section (e.g., "1.1" instead of "1.1.1")
    if (!pdfInfo) {
        const chapterSection = topicCode.split('.').slice(0, 2).join('.');
        // Find any PDF that starts with this chapter and section
        for (const key in topicToPdfMap) {
            if (key.startsWith(chapterSection) && key !== "default") {
                pdfInfo = topicToPdfMap[key];
                break;
            }
        }
    }
    
    // If no specific mapping is found, try to use the default PDF
    if (!pdfInfo && topicToPdfMap["default"]) {
        pdfInfo = topicToPdfMap["default"];
    }
    
    if (!pdfInfo) {
        console.error('No PDF mapping found for topic:', topicCode);
        document.getElementById('pdf-status').textContent = 'No notes content available for this topic';
        return;
    }
    
    const pdfPath = `/resources/${pdfInfo.file}`;
    loadPdf(pdfPath, pdfInfo.page);
}

// Load a PDF file
function loadPdf(url, pageNumber = 1) {
    // Show loading message
    document.getElementById('pdf-status').textContent = 'Loading PDF...';
    
    // Load the PDF
    pdfjsLib.getDocument(url).promise.then(pdf => {
        pdfDoc = pdf;
        totalPages = pdf.numPages;
        currentPage = pageNumber || 1;
        
        // Update page count
        document.getElementById('page-count').textContent = totalPages;
        document.getElementById('page-num').max = totalPages;
        
        // Render the page
        renderPage(currentPage);
        
        // Update status
        document.getElementById('pdf-status').textContent = '';
        
        // Show filename
        const filename = url.split('/').pop();
        document.getElementById('pdf-filename').textContent = filename;
        
    }).catch(error => {
        console.error('Error loading PDF:', error);
        document.getElementById('pdf-status').textContent = 'Error loading PDF';
    });
}

// Render a specific page
function renderPage(pageNumber) {
    // Update current page
    currentPage = pageNumber;
    document.getElementById('page-num').value = currentPage;
    
    // Get the page
    pdfDoc.getPage(pageNumber).then(page => {
        // Prepare canvas for rendering
        const canvas = document.getElementById('pdf-canvas');
        const context = canvas.getContext('2d');
        
        // Set scale based on container width
        const containerWidth = pdfContainer.clientWidth;
        const viewport = page.getViewport({ scale: 1 });
        const scale = containerWidth / viewport.width;
        const scaledViewport = page.getViewport({ scale });
        
        // Set canvas dimensions
        canvas.height = scaledViewport.height;
        canvas.width = scaledViewport.width;
        
        // Clear previous content
        context.clearRect(0, 0, canvas.width, canvas.height);
        
        // Render PDF page
        const renderContext = {
            canvasContext: context,
            viewport: scaledViewport
        };
        
        const renderTask = page.render(renderContext);
        
        // Wait for rendering to finish
        renderTask.promise.then(() => {
            console.log(`Page ${pageNumber} rendered successfully`);
        }).catch(error => {
            console.error('Error rendering PDF page:', error);
            document.getElementById('pdf-status').textContent = 'Error rendering page';
        });
    }).catch(error => {
        console.error('Error getting PDF page:', error);
        document.getElementById('pdf-status').textContent = 'Error loading page';
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing PDF viewer');
    
    // Check if we're on a topic page
    if (typeof topicCode !== 'undefined') {
        console.log('Topic code detected:', topicCode);
        
        // Create canvas element if it doesn't exist
        if (!document.getElementById('pdf-canvas')) {
            console.log('Creating PDF canvas');
            const canvas = document.createElement('canvas');
            canvas.id = 'pdf-canvas';
            
            const container = document.querySelector('.pdf-canvas-container');
            if (container) {
                container.appendChild(canvas);
            } else {
                console.error('PDF canvas container not found');
            }
        }
        
        initPdfViewer();
    } else {
        console.log('Not on a topic page, PDF viewer not initialized');
    }
});
