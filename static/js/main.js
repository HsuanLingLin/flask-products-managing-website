// axios傳輸資料時的基本設定
const axiosConfig = {
    headers: {
        // 固定名稱
        'x-csrf-token': csrf
    }
};
console.log(axiosConfig);

// 事件綁定器：當登入表單送出時，將會觸發以下流程
$('#loginForm').submit(function (event) {
    // 防止表單送出時會重新整理的行為(預設表單送出時會重新整理)
    event.preventDefault();
    const form = {
        // $(): jQery選擇器，#代表抓id
        email: $('#loginEmail').val(),
        password: $('#loginPassword').val(),
    };
    console.log('[登入]', form);
    console.log('[Email]', form.email);
    console.log('[Password]', form.password);
    // 前端登入
    firebase.auth().signInWithEmailAndPassword(
        form.email,
        form.password
    )
        // .then()負責處理登入成功
        .then(function (res) {
            // 'function(res)' = 'res =>'
            // console.log(this) 用不用 '=>' this裡面的東西會長得不一樣
            console.log('[成功]', res)
            // 取得該員的登入成功驗證碼
            res.user.getIdToken()
                .then(idToken => {
                    console.log('[idToken]', idToken)
                    // TODO: 把idToken送到後端(文件沒寫)，要如何跟python(app.py)對接的技術
                    // axios用法:axios.post('路徑', 資料{}, 設定{}) {}:物件的意思
                    // 物件格式，跟字典一樣要有key和value
                    const data = {
                        id_token: idToken
                    }
                    // 收訊差，可能會失敗
                    axios.post('/api/login', data, axiosConfig)
                        // 成功
                        .then(res => {
                            console.log('[res]', res);
                            // 重整畫面
                            window.location.reload();
                        })
                        // 失敗
                        .catch(err => {
                            console.log('[err]', err);
                            // 提示使用者再輸入一次
                            alert('發生錯誤，請重新嘗試。') // 可能是因為連線不佳
                        })
                })
        })
        // .catch()負責處理登入失敗
        .catch(err => {
            console.log('[失敗]', err)
            // 彈出視窗(alert)顯示錯誤
            alert(err.message)
        });
});

// 當註冊表單送出時
$('#signUpForm').submit(function (event) {
    event.preventDefault();
    const form = {
        email: $('#signUpEmail').val(),
        password: $('#signUpPassword').val(),
    };
    console.log('[註冊]', form);
    // 前端註冊
    firebase.auth().createUserWithEmailAndPassword(
        form.email,
        form.password
    )
        // .then()負責處理註冊成功
        .then(function (res) {
            // 'function(res)' = 'res =>'
            // console.log(this) 用不用 '=>' this裡面的東西會長得不一樣
            console.log('[成功]', res)
            // 取得該員的登入成功驗證碼
            res.user.getIdToken()
                .then(idToken => {
                    console.log('[idToken]', idToken)
                    // TODO: 把idToken送到後端(文件沒寫)，要如何跟python(app.py)對接的技術
                    // axios用法:axios.post('路徑', 資料{}, 設定{}) {}:物件的意思
                    // 物件格式，跟字典一樣要有key和value
                    const data = {
                        id_token: idToken
                    }
                    // 收訊差，可能會失敗
                    axios.post('/api/login', data, axiosConfig)
                        // 成功
                        .then(res => {
                            console.log('[res]', res);
                            // 重整畫面
                            window.location.reload();
                        })
                        // 失敗
                        .catch(err => {
                            console.log('[err]', err);
                            // 提示使用者再輸入一次
                            alert('發生錯誤，請重新嘗試。') // 可能是因為連線不佳
                        })
                })
        })
        // .catch()負責處理登入失敗
        .catch(err => {
            console.log('[失敗]', err)
            // 彈出視窗(alert)顯示錯誤
            alert(err.message)
        });
});
// 前端無法對伺服器做出操作，要和伺服器溝通
$('#logoutBtn').click(function () {
    console.log('[登出]');
    // 呼叫登出API
    // axios.post('路徑', {}資料, {}設定)
    axios.post('/api/logout', {}, axiosConfig)
        // 成功
        .then(res => {
            console.log('[res]', res)
            // 登出後不要用重新整理，改成轉跳到首頁
            window.location = '/'
        })
        // 失敗
        .catch(err => {
            console.log('[err]', err);
            alert('發生錯誤，請重新嘗試。')
        });
});