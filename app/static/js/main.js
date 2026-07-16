// Client-side interactions - Student Course Management Portal

document.addEventListener("DOMContentLoaded", function() {
    
    // 1. Hide Loading Spinner on Page Load
    const loader = document.getElementById('loader-wrapper');
    if (loader) {
        // Fade out transition
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.style.display = 'none';
        }, 300);
    }
    
    // 2. Sidebar Mobile Drawer Toggle
    const toggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (toggleBtn && sidebar) {
        // Create backdrop if it doesn't exist
        let backdrop = document.querySelector('.sidebar-backdrop');
        if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.className = 'sidebar-backdrop';
            document.body.appendChild(backdrop);
        }
        
        // Open/Close
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            backdrop.classList.toggle('show');
        });
        
        // Close on backdrop click
        backdrop.addEventListener('click', function() {
            sidebar.classList.remove('show');
            backdrop.classList.remove('show');
        });
    }
    
    // 3. Auto-Dismiss Alert Messages
    const alerts = document.querySelectorAll('.alert-dismissible-custom');
    alerts.forEach(function(alert) {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 4000); // 4 seconds visible
    });
    
    // 4. Form Submission Loader Show
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        // Exclude search forms or quick toggles if desired, otherwise show loader on submission
        if (!form.classList.contains('no-loader')) {
            form.addEventListener('submit', function() {
                if (loader) {
                    loader.style.display = 'flex';
                    loader.style.opacity = '1';
                }
            });
        }
    });
});
