// TravelGo Dynamic Client JavaScript Engine

document.addEventListener('DOMContentLoaded', () => {
  initSearchTabs();
  initSeatPicker();
  initHotelRoomPicker();
  initCancellationHandler();
  initSNSTest();
});

/**
 * Handles Tab Switching for Bus, Train, Flight, Hotel on Search Card
 */
function initSearchTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const typeInput = document.getElementById('search-type-input');
  
  if (!tabBtns.length) return;

  tabBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      const selectedType = btn.getAttribute('data-type');
      if (typeInput) {
        typeInput.value = selectedType;
      }
      
      // Update form placeholder or destination label depending on type
      const destLabel = document.getElementById('dest-label');
      if (destLabel) {
        if (selectedType === 'hotel') {
          destLabel.innerHTML = '<i class="fas fa-map-marker-alt"></i> City / Location';
        } else {
          destLabel.innerHTML = '<i class="fas fa-location-dot"></i> Destination';
        }
      }
    });
  });
}

/**
 * Handles Dynamic Bus Seat Picker
 */
function initSeatPicker() {
  const seatItems = document.querySelectorAll('.seat-item:not(.booked)');
  const selectedSeatInput = document.getElementById('selected-seat-input');
  const selectedSeatDisplay = document.getElementById('selected-seat-display');
  const totalPriceDisplay = document.getElementById('total-price-display');
  const checkoutBtn = document.getElementById('proceed-checkout-btn');
  const priceInput = document.getElementById('price-input');
  
  if (!seatItems.length) return;

  let selectedSeatNo = null;
  const basePrice = parseFloat(document.getElementById('base-bus-price')?.value || 1250);

  seatItems.forEach(seat => {
    seat.addEventListener('click', () => {
      // Toggle selection (Single seat mode for bus booking)
      seatItems.forEach(s => s.classList.remove('selected'));
      seat.classList.add('selected');
      
      selectedSeatNo = seat.getAttribute('data-seat');
      
      if (selectedSeatInput) selectedSeatInput.value = selectedSeatNo;
      if (selectedSeatDisplay) selectedSeatDisplay.innerText = selectedSeatNo;
      if (totalPriceDisplay) totalPriceDisplay.innerText = '₹' + basePrice.toLocaleString();
      if (priceInput) priceInput.value = basePrice;
      
      if (checkoutBtn) {
        checkoutBtn.removeAttribute('disabled');
        checkoutBtn.classList.remove('btn-outline');
        checkoutBtn.classList.add('btn-primary');
      }
    });
  });
}

/**
 * Handles Room Selection on Hotel Details Page
 */
function initHotelRoomPicker() {
  const roomRadios = document.querySelectorAll('.room-select-radio');
  const selectedRoomInput = document.getElementById('selected-room-input');
  const priceDisplay = document.getElementById('hotel-price-display');
  const formPriceInput = document.getElementById('hotel-form-price');

  if (!roomRadios.length) return;

  roomRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      const roomName = e.target.getAttribute('data-room-name');
      const roomPrice = parseFloat(e.target.getAttribute('data-room-price'));

      if (selectedRoomInput) selectedRoomInput.value = roomName;
      if (priceDisplay) priceDisplay.innerText = '₹' + roomPrice.toLocaleString();
      if (formPriceInput) formPriceInput.value = roomPrice;
    });
  });
}

/**
 * AJAX Booking Cancellation Handler with AWS SNS Alert
 */
function initCancellationHandler() {
  const cancelBtns = document.querySelectorAll('.btn-cancel-booking');

  cancelBtns.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const bookingId = btn.getAttribute('data-booking-id');

      if (!confirm(`Are you sure you want to cancel Booking #${bookingId}? An SNS cancellation notification will be sent.`)) {
        return;
      }

      btn.disabled = true;
      btn.innerText = "Cancelling...";

      try {
        const response = await fetch(`/booking/${bookingId}/cancel`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        const data = await response.json();

        if (data.success) {
          showToast(`Booking #${bookingId} Cancelled! AWS SNS notification triggered.`, 'success');
          
          // Update status badge UI in row
          const statusBadge = document.getElementById(`status-badge-${bookingId}`);
          if (statusBadge) {
            statusBadge.className = 'status-badge status-cancelled';
            statusBadge.innerText = 'CANCELLED';
          }
          btn.style.display = 'none';
        } else {
          showToast(data.message || 'Error cancelling booking', 'danger');
          btn.disabled = false;
          btn.innerText = "Cancel Booking";
        }
      } catch (err) {
        console.error(err);
        showToast('Server communication error', 'danger');
        btn.disabled = false;
        btn.innerText = "Cancel Booking";
      }
    });
  });
}

/**
 * AWS SNS Real-Time Test Trigger Handler
 */
function initSNSTest() {
  const testBtn = document.getElementById('test-sns-btn');
  if (!testBtn) return;

  testBtn.addEventListener('click', async () => {
    testBtn.disabled = true;
    testBtn.innerText = "Sending SNS Alert...";

    try {
      const res = await fetch('/api/sns-test', { method: 'POST' });
      const data = await res.json();
      
      showToast(`AWS SNS Message Sent! Provider: ${data.provider}`, 'success');
      alert(`AWS SNS Test Payload Sent!\n\nTopic ARN: ${data.topic_arn}\nMessage ID: ${data.message_id}\n\nEmail Preview:\n${data.preview}`);
    } catch (e) {
      showToast('Failed to trigger SNS test', 'danger');
    } finally {
      testBtn.disabled = false;
      testBtn.innerText = "Test AWS SNS Notification";
    }
  });
}

/**
 * Renders custom notification toast
 */
function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `sns-toast ${type}`;
  toast.innerHTML = `
    <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
      <i class="fas fa-paper-plane" style="color: var(--primary); font-size: 1.2rem; margin-top: 2px;"></i>
      <div>
        <strong style="display: block; font-size: 0.9rem; margin-bottom: 2px;">AWS SNS Notification</strong>
        <span style="font-size: 0.85rem; color: #cbd5e1;">${message}</span>
      </div>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.4s ease';
    setTimeout(() => toast.remove(), 400);
  }, 4500);
}
