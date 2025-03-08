// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Modal functionality
    const modal = document.getElementById('edit-modal');
    const editButtons = document.querySelectorAll('.edit-btn');
    const closeBtn = document.querySelector('.close');
    
    // Open modal with file data when edit button is clicked
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const fileId = this.getAttribute('data-id');
            const fileName = this.getAttribute('data-name');
            
            document.getElementById('edit-file-id').value = fileId;
            document.getElementById('new-name').value = fileName;
            
            modal.style.display = 'block';
        });
    });
    
    // Close modal when clicking the X button
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Flash message close buttons
    const alertCloseButtons = document.querySelectorAll('.close-btn');
    alertCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        const flashMessages = document.querySelectorAll('.alert');
        flashMessages.forEach(message => {
            message.style.opacity = '0';
            message.style.transition = 'opacity 1s';
            setTimeout(() => message.style.display = 'none', 1000);
        });
    }, 5000);
    
    // Search functionality
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const filesList = document.getElementById('files-list');
    
    // Debounce function to limit API calls
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }
    
    // Search files function
    function searchFiles() {
        const query = searchInput.value.trim();
        
        // Show loading state
        filesList.innerHTML = '<div class="loading"><div class="spinner"></div><p>Searching files...</p></div>';
        
        // Fetch search results
        fetch(`/search?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(files => {
                if (files.length === 0) {
                    filesList.innerHTML = `
                        <div class="no-files">
                            <i class="fas fa-search"></i>
                            <p>No files match your search "${query}"</p>
                        </div>
                    `;
                    return;
                }
                
                let fileCards = '';
                files.forEach(file => {
                    let fileIcon = 'fa-file';
                    const fileType = file.type.toLowerCase();
                    
                    if (['jpg', 'jpeg', 'png', 'gif'].includes(fileType)) {
                        fileIcon = 'fa-file-image';
                    } else if (fileType === 'pdf') {
                        fileIcon = 'fa-file-pdf';
                    } else if (['doc', 'docx'].includes(fileType)) {
                        fileIcon = 'fa-file-word';
                    } else if (['xls', 'xlsx'].includes(fileType)) {
                        fileIcon = 'fa-file-excel';
                    } else if (['ppt', 'pptx'].includes(fileType)) {
                        fileIcon = 'fa-file-powerpoint';
                    }
                    
                    fileCards += `
                        <div class="file-card" data-id="${file.id}">
                            <div class="file-icon">
                                <i class="fas ${fileIcon}"></i>
                            </div>
                            <div class="file-info">
                                <h3>${file.name}</h3>
                                <p>Size: ${(file.size / 1024).toFixed(2)} KB</p>
                                <p>Uploaded: ${file.uploaded_at}</p>
                            </div>
                            <div class="file-actions">
                                <button class="btn edit-btn" data-id="${file.id}" data-name="${file.name}">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <form action="/delete/${file.id}" method="POST" class="delete-form">
                                    <button type="submit" class="btn delete-btn">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </form>
                            </div>
                        </div>
                    `;
                });
                
                filesList.innerHTML = fileCards;
                
                // Reattach event listeners to new buttons
                document.querySelectorAll('.edit-btn').forEach(button => {
                    button.addEventListener('click', function() {
                        const fileId = this.getAttribute('data-id');
                        const fileName = this.getAttribute('data-name');
                        
                        document.getElementById('edit-file-id').value = fileId;
                        document.getElementById('new-name').value = fileName;
                        
                        modal.style.display = 'block';
                    });
                });
            })
            .catch(error => {
                console.error('Error searching files:', error);
                filesList.innerHTML = `
                    <div class="no-files">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>An error occurred while searching. Please try again.</p>
                    </div>
                `;
            });
    }
    
    // Attach search event listeners
    searchButton.addEventListener('click', searchFiles);
    searchInput.addEventListener('keyup', debounce(function(e) {
        if (e.key === 'Enter') {
            searchFiles();
        } else if (searchInput.value.trim() === '') {
            // If search is cleared, reload the page to show all files
            window.location.reload();
        }
    }, 500));
    
    // File drag and drop visualization (simulated)
    const uploadSection = document.querySelector('.upload-section');
    
    uploadSection.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });
    
    uploadSection.addEventListener('dragleave', function() {
        this.classList.remove('drag-over');
    });
    
    uploadSection.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
        
        // Simulate file upload - just get the filename
        if (e.dataTransfer.files.length > 0) {
            const filename = e.dataTransfer.files[0].name;
            document.getElementById('filename').value = filename;
            // Show a visual indication
            const uploadForm = document.querySelector('.upload-form');
            uploadForm.classList.add('file-ready');
            setTimeout(() => uploadForm.classList.remove('file-ready'), 1000);
        }
    });
    
    // Add file type detection and validation
    const filenameInput = document.getElementById('filename');
    
    filenameInput.addEventListener('change', function() {
        const filename = this.value.trim();
        const fileExtension = filename.split('.').pop().toLowerCase();
        
        // Visual indication of file type
        let typeIcon = document.createElement('i');
        typeIcon.className = 'fas';
        
        if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExtension)) {
            typeIcon.className += ' fa-file-image';
        } else if (fileExtension === 'pdf') {
            typeIcon.className += ' fa-file-pdf';
        } else if (['doc', 'docx'].includes(fileExtension)) {
            typeIcon.className += ' fa-file-word';
        } else if (['xls', 'xlsx'].includes(fileExtension)) {
            typeIcon.className += ' fa-file-excel';
        } else if (['ppt', 'pptx'].includes(fileExtension)) {
            typeIcon.className += ' fa-file-powerpoint';
        } else {
            typeIcon.className += ' fa-file';
        }
        
        // Remove previous icon if exists
        const previousIcon = filenameInput.parentElement.querySelector('.file-type-icon');
        if (previousIcon) {
            previousIcon.remove();
        }
        
        // Add icon after input
        typeIcon.style.marginLeft = '10px';
        typeIcon.classList.add('file-type-icon');
        filenameInput.parentElement.insertBefore(typeIcon, filenameInput.nextSibling);
    });
    
    // Add statistics summary (simulated)
    const filesSection = document.querySelector('.files-section');
    const files = document.querySelectorAll('.file-card');
    
    if (files.length > 0) {
        let totalSize = 0;
        let fileTypes = {};
        
        files.forEach(file => {
            const sizeText = file.querySelector('.file-info p').textContent;
            const sizeMatch = sizeText.match(/Size: ([\d.]+) KB/);
            if (sizeMatch) {
                totalSize += parseFloat(sizeMatch[1]);
            }
            
            const fileName = file.querySelector('.file-info h3').textContent;
            const fileExt = fileName.split('.').pop().toLowerCase();
            fileTypes[fileExt] = (fileTypes[fileExt] || 0) + 1;
        });
        
        // Create stats element
        const statsDiv = document.createElement('div');
        statsDiv.className = 'file-stats';
        statsDiv.innerHTML = `
            <p><strong>Total files:</strong> ${files.length}</p>
            <p><strong>Total size:</strong> ${totalSize.toFixed(2)} KB</p>
            <p><strong>File types:</strong> ${Object.keys(fileTypes).join(', ')}</p>
        `;
        
        // Insert after header
        const filesHeader = filesSection.querySelector('h2');
        filesSection.insertBefore(statsDiv, filesHeader.nextSibling);
    }
});