document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const scheduleForm = document.getElementById('scheduleForm');
    const resultDiv = document.getElementById('result');
    const startAutoPostButton = document.getElementById('startAutoPost');
    const stopAutoPostButton = document.getElementById('stopAutoPost');
    const currentStatusSpan = document.getElementById('currentStatus');
    const nextPostTimeSpan = document.getElementById('nextPostTimeValue');

    // 動画アップロードフォームの送信処理
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitForm('/upload', new FormData(uploadForm));
    });

    // スケジュール設定フォームの送信処理
    scheduleForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(scheduleForm);
        const scheduleData = {
            post_times: [],
            accounts: Array.from(formData.getAll('account')),
            caption: formData.get('caption')
        };

        // 投稿時刻の処理
        for (let i = 1; i <= 3; i++) {
            const timeInput = document.getElementById(`postTime${i}`);
            if (timeInput && timeInput.value) {
                scheduleData.post_times.push(timeInput.value);
            }
        }

        console.log('送信するスケジュールデータ:', scheduleData); // デバッグ用ログ

        submitJson('/set_schedule', scheduleData);
    });

    // 自動投稿開始ボタンのクリックイベント
    startAutoPostButton.addEventListener('click', function() {
        submitJson('/api/auto_post_status', { status: 'start' });
    });

    // 自動投稿停止ボタンのクリックイベント
    stopAutoPostButton.addEventListener('click', function() {
        submitJson('/api/auto_post_status', { status: 'stop' });
    });

    // フォームデータを送信する関数
    function submitForm(url, formData) {
        fetch(url, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            resultDiv.textContent = data.message || data.error;
            updateAutoPostStatus();
            updateNextPostTime();
        })
        .catch(error => {
            console.error('エラー:', error);
            resultDiv.textContent = 'エラーが発生しました。もう一度お試しください。';
        });
    }

    // JSONデータを送信する関数
    function submitJson(url, data) {
        console.log('送信するデータ:', data); // デバッグ用ログ
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log('サーバーからの応答:', data); // デバッグ用ログ
            resultDiv.textContent = data.message || data.error;
            updateAutoPostStatus();
            updateNextPostTime();
        })
        .catch(error => {
            console.error('エラー:', error);
            resultDiv.textContent = 'エラーが発生しました。もう一度お試しください。';
        });
    }

    // 自動投稿の状態を更新する関数
    function updateAutoPostStatus() {
        fetch('/api/auto_post_status')
        .then(response => response.json())
        .then(data => {
            currentStatusSpan.textContent = data.status === 'running' ? 'アクティブ' : '停止中';
        })
        .catch(error => {
            console.error('自動投稿状態の取得に失敗しました:', error);
        });
    }

    // 次回投稿時間を更新する関数
    function updateNextPostTime() {
        fetch('/api/next_post_time')
        .then(response => response.json())
        .then(data => {
            nextPostTimeSpan.textContent = data.next_post_times || '未設定';
        })
        .catch(error => {
            console.error('次回投稿時間の取得に失敗しました:', error);
        });
    }

    // 定期的に自動投稿の状態と次回投稿時間を更新
    setInterval(() => {
        updateAutoPostStatus();
        updateNextPostTime();
    }, 60000); // 1分ごとに更新

    // 初期状態を取得
    updateAutoPostStatus();
    updateNextPostTime();
});