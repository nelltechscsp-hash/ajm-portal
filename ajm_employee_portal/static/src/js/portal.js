// Simple vanilla JS - no Odoo modules needed
(function() {
    'use strict';
    
    function initAJMPortal() {
        // NO AUTO-REDIRECT - let users navigate manually
        
        // Initialize Bootstrap dropdowns if not already initialized
        if (typeof bootstrap !== 'undefined') {
            var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
            dropdownElementList.map(function (dropdownToggleEl) {
                if (!bootstrap.Dropdown.getInstance(dropdownToggleEl)) {
                    return new bootstrap.Dropdown(dropdownToggleEl);
                }
            });
        }
        
        // Menu navigation now handled natively by website.menu records

        const btnCheckIn = document.getElementById('btn-check-in');
        const btnCheckOut = document.getElementById('btn-check-out');

        if (btnCheckIn) {
            btnCheckIn.addEventListener('click', async function(e) {
                e.preventDefault();
                try {
                    btnCheckIn.disabled = true;
                    btnCheckIn.innerHTML = '<i class="fa fa-spinner fa-spin me-2"></i>Checking in...';
                    
                    const response = await fetch('/my/sales/check-in', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            jsonrpc: '2.0',
                            method: 'call',
                            params: {}
                        })
                    });
                    
                    const data = await response.json();
                    const result = data.result;
                    
                    if (result && result.success) {
                        location.reload();
                    } else {
                        alert('Error: ' + (result && result.error ? result.error : 'Unknown error'));
                        btnCheckIn.disabled = false;
                        btnCheckIn.innerHTML = '<i class="fa fa-sign-in me-2"></i>Check In';
                    }
                } catch (error) {
                    console.error('Check-in error:', error);
                    alert('Error checking in. Please try again.');
                    btnCheckIn.disabled = false;
                    btnCheckIn.innerHTML = '<i class="fa fa-sign-in me-2"></i>Check In';
                }
            });
        }

        if (btnCheckOut) {
            btnCheckOut.addEventListener('click', async function(e) {
                e.preventDefault();
                if (!confirm('Are you sure you want to check out?')) {
                    return;
                }
                
                try {
                    btnCheckOut.disabled = true;
                    btnCheckOut.innerHTML = '<i class="fa fa-spinner fa-spin me-2"></i>Checking out...';
                    
                    const response = await fetch('/my/sales/check-out', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            jsonrpc: '2.0',
                            method: 'call',
                            params: {}
                        })
                    });
                    
                    const data = await response.json();
                    const result = data.result;
                    
                    if (result && result.success) {
                        location.reload();
                    } else {
                        alert('Error: ' + (result && result.error ? result.error : 'Unknown error'));
                        btnCheckOut.disabled = false;
                        btnCheckOut.innerHTML = '<i class="fa fa-sign-out me-2"></i>Check Out';
                    }
                } catch (error) {
                    console.error('Check-out error:', error);
                    alert('Error checking out. Please try again.');
                    btnCheckOut.disabled = false;
                    btnCheckOut.innerHTML = '<i class="fa fa-sign-out me-2"></i>Check Out';
                }
            });
        }
    }

    // Run init when DOM is ready, or immediately if already loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAJMPortal);
    } else {
        initAJMPortal();
    }
})();
