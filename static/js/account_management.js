document.addEventListener('DOMContentLoaded', function() {
    const accountListDiv = document.getElementById('accountList');
    const addAccountForm = document.getElementById('addAccountForm');
    const resultDiv = document.getElementById('result');

    // アカウント一覧を取得して表示
    function fetchAndDisplayAccounts() {
        fetch('/api/accounts')
            .then(response => response.json())
            .then(accounts => {
                accountListDiv.innerHTML = '<h2>アカウント一覧</h2>';
                accounts.forEach(account => {
                    accountListDiv.innerHTML += `
                        <div class="account-item">
                            <span>${account.username}</span>
                            <span>パスワード: ********</span>
                            <label>
                                <input type="checkbox" ${account.postFlag ? 'checked' : ''} onchange="updatePostFlag('${account.username}', this.checked)">
                                投稿を有効にする
                            </label>
                            <button onclick="editAccount('${account.username}')">編集</button>
                            <button onclick="deleteAccount('${account.username}')">削除</button>
                        </div>
                    `;
                });
            })
            .catch(error => {
                console.error('Error fetching accounts:', error);
                resultDiv.textContent = 'アカウント情報の取得に失敗しました。';
            });
    }

    // 新規アカウント追加
    addAccountForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(addAccountForm);
        const accountData = {
            username: formData.get('username'),
            password: formData.get('password'),
            postFlag: formData.get('postFlag') === 'on'
        };

        fetch('/api/accounts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(accountData)
        })
        .then(response => response.json())
        .then(data => {
            resultDiv.textContent = data.message;
            fetchAndDisplayAccounts();
            addAccountForm.reset();
        })
        .catch(error => {
            console.error('Error adding account:', error);
            resultDiv.textContent = 'アカウントの追加に失敗しました。';
        });
    });

    // アカウント編集
    window.editAccount = function(username) {
        // 編集モードの実装（簡略化のため省略）
        console.log('Edit account:', username);
    };

    // アカウント削除
    window.deleteAccount = function(username) {
        if (confirm(`本当に ${username} を削除しますか？`)) {
            fetch(`/api/accounts/${username}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    resultDiv.textContent = data.message;
                    fetchAndDisplayAccounts();
                })
                .catch(error => {
                    console.error('Error deleting account:', error);
                    resultDiv.textContent = 'アカウントの削除に失敗しました。';
                });
        }
    };

    // 投稿フラグの更新
    window.updatePostFlag = function(username, postFlag) {
        fetch(`/api/accounts/${username}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ postFlag: postFlag })
        })
        .then(response => response.json())
        .then(data => {
            resultDiv.textContent = data.message;
        })
        .catch(error => {
            console.error('Error updating post flag:', error);
            resultDiv.textContent = '投稿フラグの更新に失敗しました。';
        });
    };

    // 初期表示
    fetchAndDisplayAccounts();
});