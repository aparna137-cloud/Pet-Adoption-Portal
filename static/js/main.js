// ===================================================================
// PET ADOPTION PORTAL - CLIENT INTERACTION SCRIPTS
// ===================================================================

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto dismiss alert messages after 6 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => alert.remove());
        }
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 400);
        }, 6000);
    });

    // 2. Client-side validation for Financial & Income Form (SEL-04, SEL-07, BUG-001)
    const incomeForm = document.getElementById('income-form');
    if (incomeForm) {
        incomeForm.addEventListener('submit', (e) => {
            const amountInput = document.getElementById('income-amount');
            const categoryInput = document.getElementById('income-category');
            const dateInput = document.getElementById('income-date');
            const errorContainer = document.getElementById('income-error');

            if (errorContainer) {
                errorContainer.innerHTML = '';
                errorContainer.style.display = 'none';
            }

            // Check for empty fields (SEL-04)
            if (!categoryInput.value.trim() || !amountInput.value.trim() || !dateInput.value.trim()) {
                e.preventDefault();
                showError('Please fill out all required fields (Category, Amount, and Date).', errorContainer);
                return;
            }

            const amountValue = parseFloat(amountInput.value);

            // Check for valid number
            if (isNaN(amountValue)) {
                e.preventDefault();
                showError('Please enter a valid numeric amount.', errorContainer);
                return;
            }

            // Check for negative amount (SEL-07 & BUG-001)
            if (amountValue < 0) {
                e.preventDefault();
                showError('Amount cannot be negative. Please enter an amount of 0 or greater.', errorContainer);
                return;
            }
        });
    }

    // 3. Client-side validation for Adoption Request Form (SEL-06, BUG-001)
    const adoptForm = document.getElementById('adopt-request-form');
    if (adoptForm) {
        adoptForm.addEventListener('submit', (e) => {
            const incomeInput = document.getElementById('applicant-income');
            const messageInput = document.getElementById('adopt-message');
            const errorContainer = document.getElementById('adopt-error');

            if (errorContainer) {
                errorContainer.innerHTML = '';
                errorContainer.style.display = 'none';
            }

            if (!messageInput.value.trim()) {
                e.preventDefault();
                showError('Please enter a message explaining why you would like to adopt.', errorContainer);
                return;
            }

            if (incomeInput && incomeInput.value.trim()) {
                const incomeVal = parseFloat(incomeInput.value);
                if (incomeVal < 0) {
                    e.preventDefault();
                    showError('Monthly income cannot be a negative amount.', errorContainer);
                    return;
                }
            }
        });
    }

    function showError(message, container) {
        if (container) {
            container.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> ${message}</div>`;
            container.style.display = 'block';
        } else {
            alert(message);
        }
    }

    // 4. Modal toggling helpers
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    };

    // Close modal on click outside
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-backdrop')) {
            e.target.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
});
