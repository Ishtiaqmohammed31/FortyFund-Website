document.addEventListener('DOMContentLoaded', function() {
    let bookedDates = new Set();
    let bookedDateTimes = {};
    let selectedDate = null;
    let selectedTime = null;
    let currentDate = new Date(); // Start with current month

    // Fetch booked dates from backend
    fetch('/api/booked_dates')
        .then(res => res.json())
        .then(data => {
            bookedDates = new Set(data);
            renderCalendar();
        });

    // Fetch booked date+time pairs from backend
    function fetchBookedDateTimes(cb) {
        fetch('/api/booked_dates_times')
            .then(res => res.json())
            .then(data => {
                bookedDateTimes = data; // { 'YYYY-MM-DD': ['08:00', ...] }
                if (cb) cb();
            });
    }

    function pad(n) { return n < 10 ? '0' + n : n; }

    function renderCalendar() {
        const calendarGrid = document.getElementById('calendar-grid');
        calendarGrid.innerHTML = '';
        document.getElementById('current-month').textContent =
            `${currentDate.toLocaleString('default', { month: 'long' })} ${currentDate.getFullYear()}`;
        const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
        const daysInMonth = lastDay.getDate();
        const dayNames = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
        dayNames.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.className = 'day-header';
            dayHeader.textContent = day;
            calendarGrid.appendChild(dayHeader);
        });
        for (let i = 0; i < firstDay.getDay(); i++) {
            const emptyCell = document.createElement('div');
            emptyCell.className = 'day-cell empty';
            calendarGrid.appendChild(emptyCell);
        }
        for (let day = 1; day <= daysInMonth; day++) {
            const dateObj = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
            const dateStr = `${dateObj.getFullYear()}-${pad(dateObj.getMonth() + 1)}-${pad(day)}`;
            const isWeekend = dateObj.getDay() === 0 || dateObj.getDay() === 6;
            const isFullyBooked = bookedDateTimes[dateStr] && bookedDateTimes[dateStr].length >= 7; // 7 slots per day
            const isSelected = selectedDate === dateStr;
            const dayCell = document.createElement('div');
            dayCell.className = 'day-cell';
            dayCell.textContent = day;
            if (isWeekend || isFullyBooked) {
                dayCell.classList.add('unavailable');
            } else {
                if (isSelected) {
                    dayCell.classList.add('selected');
                }
                dayCell.addEventListener('click', function() {
                    selectedDate = dateStr;
                    document.getElementById('meeting-date').value = dateStr;
                    renderCalendar();
                    updateTimeDropdown();
                });
            }
            calendarGrid.appendChild(dayCell);
        }
    }

    function updateTimeDropdown() {
        const timeDropdown = document.getElementById('meeting-time');
        if (!selectedDate) {
            timeDropdown.value = '';
            Array.from(timeDropdown.options).forEach(opt => { if (opt.value) opt.disabled = false; });
            return;
        }
        const bookedTimes = bookedDateTimes[selectedDate] || [];
        Array.from(timeDropdown.options).forEach(opt => {
            if (!opt.value) return;
            opt.disabled = bookedTimes.includes(opt.value);
            if (opt.disabled && timeDropdown.value === opt.value) {
                timeDropdown.value = '';
            }
        });
    }

    document.getElementById('prev-month').addEventListener('click', function() {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });
    document.getElementById('next-month').addEventListener('click', function() {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });
    document.getElementById('meeting-time').addEventListener('change', function(e) {
        selectedTime = e.target.value;
    });

    // Initial load
    fetchBookedDateTimes(() => {
        renderCalendar();
        updateTimeDropdown();
    });
});

// calender-demo configuration
let toogleBtn = document.querySelector('.next-btn')
let PrevBtn = document.querySelector('.prev-btn')

let demoSection = document.querySelector('.book-appointment')

let calenderSection = document.querySelector('.calender-section')

toogleBtn.addEventListener('click', function(){
    demoSection.style.width = '0%';
        demoSection.style.display = 'none';
        calenderSection.style.width = '60%';
        calenderSection.style.display = 'flex';
})

PrevBtn.addEventListener('click', function(){
    console.log('clicked')
    demoSection.style.width = '60%';
    demoSection.style.display = 'flex';
    calenderSection.style.width = '0%';
    calenderSection.style.display = 'none';
})