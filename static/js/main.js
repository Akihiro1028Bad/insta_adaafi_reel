document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const scheduleForm = document.getElementById('scheduleForm');
    const postCountSelect = document.getElementById('postCount');
    const timeSlotsDiv = document.getElementById('timeSlots');
    const resultDiv = document.getElementById('result');

    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitForm('/upload', new FormData(uploadForm));
    });

    scheduleForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(scheduleForm);
        const scheduleData = {
            accounts: Array.from(formData.getAll('account')),
            caption: formData.get('caption'),
            posts: getTimeSlots()
        };
        submitJson('/set_schedule', scheduleData);
    });

    postCountSelect.addEventListener('change', updateTimeSlots);

    function updateTimeSlots() {
        const count = parseInt(postCountSelect.value);
        timeSlotsDiv.innerHTML = '';
        for (let i = 0; i < count; i++) {
            timeSlotsDiv.innerHTML += `
                <div class="time-slot">
                    <label for="startTime${i}">開始時刻 ${i+1}:</label>
                    <input type="time" id="startTime${i}" name="startTime${i}" required>
                    <label for="endTime${i}">終了時刻 ${i+1}:</label>
                    <input type="time" id="endTime${i}" name="endTime${i}" required>
                </div>
            `;
        }
    }

    function getTimeSlots() {
        const slots = [];
        const timeSlots = document.querySelectorAll('.time-slot');
        timeSlots.forEach((slot, index) => {
            slots.push({
                start_time: slot.querySelector(`#startTime${index}`).value,
                end_time: slot.querySelector(`#endTime${index}`).value
            });
        });
        return slots;
    }

    function submitForm(url, formData) {
        fetch(url, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            resultDiv.textContent = data.message || data.error;
        })
        .catch(error => {
            console.error('Error:', error);
            resultDiv.textContent = 'エラーが発生しました。もう一度お試しください。';
        });
    }

    function submitJson(url, data) {
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            resultDiv.textContent = data.message || data.error;
        })
        .catch(error => {
            console.error('Error:', error);
            resultDiv.textContent = 'エラーが発生しました。もう一度お試しください。';
        });
    }

    // 初期化時に時間枠を表示
    updateTimeSlots();
});