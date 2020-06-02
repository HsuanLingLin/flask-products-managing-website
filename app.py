# 引用flask相關資源
import os
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
import time
import datetime
# CRUD
from forms import (
    # 商品表單
    CreateProductForm,
    EditProductForm,
    DeleteProductForm,
    # 留言表單
    CreateCommentForm,
    UpdateCommentForm
)

# 初始化Firebase Firestore
# https://firebase.google.com/docs/firestore/quickstart

import firebase_admin
from firebase_admin import credentials, firestore, auth
from flask_wtf.csrf import CSRFProtect
#DESCENDING = firestore.Query.DESCENDING
# 請更新為你的金鑰
cred = credentials.Certificate("key.json")  # path:key如果放到別的資料夾就寫資料夾的path
firebase_admin.initialize_app(cred)
# 初始化資料庫
db = firestore.client()


app = Flask(__name__)
# shakehand
csrf = CSRFProtect(app)
# 可在每個模板裡透過 csrf_token() 取得到csrf代碼
csrf.init_app(app)

# 設定應用程式的SECRET_KEY='字串' (安全性問題 產生CSRF token的依據)
# 沒加secret key會產生key error錯誤訊息: A secret key is required to use CSRF.
app.config['SECRET_KEY'] = 'qwertyuiop'

# 對應網頁裡application裡的cookie欄位：name是web_login_cookie, value是session_cookie
cookie_name = 'web_login_cookie'

# 通過每個路由時都會觸發的函數
@app.context_processor
def login_checker():
    # user的資料
    auth_user = {
        'is_login': False,
        # 設計一個權限概念
        'is_admin': False,
        'user': {}
    }
    # 取得session_cookie
    session_cookie = request.cookies.get(cookie_name)
    # 驗證session_cookie
    try:
        # 透過session_cookie取得user的資料
        user = auth.verify_session_cookie(session_cookie)
        # 設定為登入狀態
        auth_user['is_login'] = True
        auth_user['user'] = user
        # 取回文件 admins/{EMAIL}，即使文件不存在還是會要回一個空字串
        admin_doc = db.document(f'admins/{user["email"]}').get()
        # 檢查文件是否存在
        if admin_doc.exists:
            # 設定此人是管理者
            auth_user['is_admin'] = True
    except:
        print("驗證失敗")
    # 回傳auth_user給每一個模板
    return dict(auth_user=auth_user)  # dict是context_processor的特別規定

# 登入API
# 如果app.route沒寫就會顯示404, 但出現400 bad request代表無法從前端資料送到後端被csrf擋住
# 所以在main.js產生的csrf token就要派上用場
@app.route('/api/login', methods=['POST'])
def login():
    # 取得前端傳來的資料
    data = request.json
    id_token = data['id_token']
    # 設定session_cookie有效期限
    expires_in = datetime.timedelta(days=7)
    # 把id_token取出換取session_cookie(像簽證這樣)，把它存到使用者瀏覽器裡面
    session_cookie = auth.create_session_cookie(
        id_token, expires_in=expires_in)
    # print('[session_cookie]', session_cookie)
    # 準備回應前端，利用flask裡面的jsonify
    res = jsonify({
        'msg': 'OK',
    })
    # 把session_cookie存到瀏覽器的cookies裡，7天後就過期
    # cookie的期限
    expires = datetime.datetime.now() + expires_in
    # .set_cookie('名稱', '值')，httponly=True (?)
    res.set_cookie(cookie_name, session_cookie, expires=expires, httponly=True)
    # 回應資料給前端
    return res


@app.route('/api/logout', methods=['POST'])
def logout():
    # 取得session cookie
    session_cookie = request.cookies.get(cookie_name)
    # 取得登入者
    user = auth.verify_session_cookie(session_cookie)
    # 取得user_id
    user_id = user['user_id']
    print(user_id)
    # 通知firebase 此 session cookie作廢
    # user_id會顯示在firebase裡authentication的UID
    auth.revoke_refresh_tokens(user_id)
    # 準備回應，不可以已讀不回不然會bad request
    res = jsonify({'msg': '已登出'})
    # 在瀏覽器作廢 session cookie (作廢就是讓cookie過期)，寫到cookie要用expires
    res.set_cookie(cookie_name, expires=0)
    # 回應前端
    return res

# 產品建立後要顯示在首頁中
@app.route('/')
def index_page():
    # 取得資料庫的商品列表資料
    # 取得到products集合內的所有文件, order_by是可以按順序排
    # 反向排有兩種方法，第一種：使用firestore內建的direction=firestore.Query.DESCENDING
    # 第二種：直接將list反向：product_list.reverse()
    docs = db.collection('products').order_by('created_at', direction=firestore.Query.DESCENDING
                                              ).get()
    # 用list把dict包住 建立商品列表
    product_list = []
    for doc in docs:
        # print(doc.id)  # 取得文件id (e.g., BGG6wuhRTS9n0bHb1E6Z)
        # 取得文件的資料
        product = doc.to_dict()  # firestore 裡 read data 的方法就是 to_dict()
        # 把文件id存到商品字典內，未來編輯資料會需要id，要抓到單一資料要知道id
        product['id'] = doc.id
        # print(product)
        # 把單一商品存至列表內
        product_list.append(product)
    # 反向排列商品
    # product_list.reverse()
    # 首頁路由
    return render_template('index.html', product_list=product_list)


@app.route('/product/create', methods=['GET', 'POST'])
def create_product_page():
    # 取得login_checker產生的auth_user
    auth_user = login_checker()['auth_user']
    # 如果不是管理者
    if not auth_user['is_admin']:
        # 轉跳回首頁
        return redirect('/')
    # 建立商品頁的路由
    # 建立商品表單的實例
    create_product_form = CreateProductForm()

    # 設定表單送出後的處理
    # validate_on_submit 檢查該填的有沒有填
    if create_product_form.validate_on_submit():
        print('[表單被送出了]')
        # 取得表單內部的資料
        # 表單.欄位名稱.data => 欄位的值 (data是固定的)
        new_product = {
            'title': create_product_form.title.data,
            'price': create_product_form.price.data,
            'img_url': create_product_form.img_url.data,
            'is_on_sale': create_product_form.is_on_sale.data,
            'category': create_product_form.category.data,
            'description': create_product_form.description.data,
            'created_at': time.time()  # timestamp
        }
        print('[new_product]', new_product)
        # 新產品資料先存在暫存內
        session['new_product'] = new_product
        # 新商品資料記錄到資料庫的products集合(collection)內
        # 跟firestore溝通只能用字典格式(dictionary)
        db.collection('products').add(new_product)  # 用add會自動幫你取名文件2的名稱
        # Collection|
        #           |- document
        # 閃現一個訊息
        flash(f'{create_product_form.title.data}被建立了', 'success')
        # 跳轉頁面到產品建立成功頁
        # 利用flask裡面的函數 redirect 到產品建立的成功頁
        # return redirect('/product/create-finished')
        # 如果怕網址太長，可以用url_for裡面放要跳轉的函式名稱
        return redirect(url_for('create_finished_page'))
    # 將新商品的資料儲存在session內以便下個頁面可顯示新資料
    return render_template('product/create.html',
                           create_product_form=create_product_form,
                           )


@app.route('/product/create-finished')
def create_finished_page():
    session['new_product']
    # 商品建立成功的路由
    return render_template('product/create_finished.html')

# pid 就是firebase裡的文件id
@app.route('/product/<pid>/show', methods=['GET', 'POST'])
def show_product_page(pid):
    # 商品詳情頁的路由
    # 取得資料庫指定pid的商品資料
    doc = db.collection('products').document(pid).get()
    product = doc.to_dict()
    product['id'] = doc.id  # pid 要有商品id
    # print('[商品]', product)
    # comments_set = f'products/{pid}/comments'
    # 取得商品留言集合
    comment_docs = db.collection(
        f'products/{pid}/comments').order_by('created_at').get()
    # 建立留言清單
    comment_list = []
    # 取得留言集合的文件取出
    for comment_doc in comment_docs:
        # 一個留言
        comment = comment_doc.to_dict()
        comment['id'] = comment_doc.id
        # 把更新這個留言的表單存到留言內, 要有前綴prefix才不會掉入flask坑，
        # 因為每個update form 都長一樣，不知道差異，所以只會更新到第一則
        comment['form'] = UpdateCommentForm(prefix=comment['id'])
        # 判定留言更新表單送出
        if comment['form'].validate_on_submit():
            # 更新留言流程
            edited_comment = {
                # 使用者留言表單所填的內容
                'content': comment['form'].content.data
            }
            # 更新到資料庫對應的文件
            doc_path = f'products/{pid}/comments/{comment["id"]}'
            db.document(doc_path).update(edited_comment)
            # 顯示訊息
            flash('留言已更新', 'warning')
            # 跳轉畫面
            return redirect(url_for('show_product_page', pid=pid))
        # 填入留言內容預設值
        comment['form'].content.data = comment['content']
        print('[留言]', comment)
        # 把留言資料放到清單內
        comment_list.append(comment)
    # 新增留言表單
    create_comment_form = CreateCommentForm(prefix='create-comment')
    if create_comment_form.validate_on_submit():
        # 新增留言表單被送出
        # 新留言
        new_comment = {
            'email': create_comment_form.email.data,
            'content': create_comment_form.content.data,
            'created_at': time.time()
        }
        print('[新留言]', new_comment)
        # 新增留言至資料庫
        # products(集合)/pid(文件)/comments(集合): 奇數是集合，偶數是文件, comments這個集合會自己被創建
        db.collection(f'products/{pid}/comments').add(new_comment)
        # 顯示訊息
        flash('新增留言成功', 'success')
        # 轉跳畫面(即使是同一頁也要做轉跳動作)
        # return redirect(f'/product/{pid}/show')
        return redirect(url_for('show_product_page', pid=pid))
    return render_template('product/show.html',
                           product=product,
                           create_comment_form=create_comment_form,
                           comment_list=comment_list)


# 要設定method
@app.route('/product/<pid>/edit', methods=['GET', 'POST'])
def edit_product_page(pid):
    # 取得login_checker產生的auth_user
    auth_user = login_checker()['auth_user']
    # 如果不是管理者
    if not auth_user['is_admin']:
        # 轉跳回首頁
        return redirect('/')
    # 編輯商品頁的路由
    # 取得資料庫指定pid的商品資料
    # 集合collection叫product, 單一個商品是document
    # step1: 取得對應pid文件
    doc = db.collection('products').document(pid).get()  # 集合一定要先寫
    print(doc)
    product = doc.to_dict()
    print(product)
    # 建立編輯商品表單的實例
    edit_form = EditProductForm()
    # 檢測是否編輯表單被送出且符合驗證
    if edit_form.validate_on_submit():
        # 產生被更新後的商品資料
        edited_product = {
            'title': edit_form.title.data,
            'price': edit_form.price.data,
            'img_url': edit_form.img_url.data,
            'category': edit_form.category.data,
            'description': edit_form.description.data,
            'is_on_sale': edit_form.is_on_sale.data
        }
        print('[更新後的商品]', edited_product)
        # 更新到資料庫
        db.collection('products').document(pid).update(edited_product)
        # 閃現一個訊息
        flash(f'{edit_form.title.data}已完成更新', 'warning')
        # 轉跳回首頁
        return redirect('/')
    # 給予某些輸入框預設值
    edit_form.category.data = product['category']
    edit_form.is_on_sale.data = product['is_on_sale']
    edit_form.description.data = product['description']
    # 建立刪除商品表單的實例
    delete_form = DeleteProductForm()
    # 如果刪除表單送出
    if delete_form.validate_on_submit():
        print('[刪除商品]', pid)
        # step1. 刪除指定pid的文件
        db.collection('products').document(pid).delete()
        # 目前流行作法：加一個欄位is_active，刪除不是真的刪除(後續要查驗就要留存證據)
        # 如果is_active == True才渲染出來，false就不渲染
        # .delete()會做成.update()，然後set is_active = false
        # 對使用者是刪除，但對管理者是有留存的
        # step2. 閃現訊息，單雙引號要不同不然會撞到
        flash(f'已移除{product["title"]}', 'danger')
        # step3. 跳轉到首頁
        return redirect('/')
    return render_template('product/edit.html',
                           edit_form=edit_form,
                           delete_form=delete_form,
                           product=product)


if __name__ == '__main__':
    # 為了在heroku部署的設定
    port = int(os.environ.get('PORT', 5000))
    # 應用程式開始運行
    app.run(debug=True, port=port, host='0.0.0.0')
