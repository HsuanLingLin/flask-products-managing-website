from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, NumberRange
from wtforms.widgets.html5 import NumberInput

category_options = [
    # value, label 下拉式選單會看到電子產品類
    ('electronics', '電子產品類'),
    ('handmade', '手作類'),
    ('industrial', '工業類'),
    ('sports', '運動用品類'),
    ('outdoors', '戶外用品類'),
    ('toys', '玩具類'),
    ('others', '其他')
]

price_minimum = 0
price_maximum = 100000


class CreateProductForm(FlaskForm):
    # 建立商品的表單
    # 名稱(title)
    title = StringField('商品標題', validators=[DataRequired()])
    # 縮圖網址(img_url)
    img_url = StringField('商品圖片', validators=[DataRequired()])
    # 價格(price)
    price = IntegerField('商品價格', validators=[
        DataRequired(),
        NumberRange(
            min=price_minimum,
            max=price_maximum,
            message=f'商品價格必須在{price_minimum}-{price_maximum}之間'
        )
    ])  # form.price.label 數字可以給最大和最小
    # 是否銷售中(on_sale) -> use boolean field
    is_on_sale = BooleanField('是否銷售中')
    # 類別(category) [(值, 提示文字), (), ()] -> use select field 下拉式選單可以作區別
    category = SelectField('商品類別', choices=category_options)
    # 敘述(description) -> Text Area 是可以換行的框框
    description = TextAreaField('商品敘述')
    # 送出表單按鈕(submit)
    submit = SubmitField('建立商品')


class EditProductForm(FlaskForm):
    # 更新商品的表單
    # 名稱(title)
    title = StringField('商品標題', validators=[DataRequired()])
    # 縮圖網址(img_url)
    img_url = StringField('商品圖片', validators=[DataRequired()])
    # 價格(price)
    price = IntegerField('商品價格', validators=[
        DataRequired(),
        NumberRange(
            min=price_minimum,
            max=price_maximum,
            message=f'商品價格必須在{price_minimum}-{price_maximum}之間'
        )
    ])
    # 是否銷售中(on_sale)
    is_on_sale = BooleanField('是否銷售中')
    # 類別(category[Electronics, Handmade, Industrial, Sports, Toys, Others])
    category = SelectField('商品類別', choices=category_options)
    # 敘述(description)
    description = TextAreaField('商品敘述')
    # 送出表單按鈕(submit)
    submit = SubmitField('更新商品')


class DeleteProductForm(FlaskForm):
    # 移除商品的表單
    # 確認刪除
    confirm = BooleanField('確認是否移除?', validators=[DataRequired()])
    # 送出按鈕
    submit = SubmitField('移除商品')


class CreateCommentForm(FlaskForm):
    # 新增留言的表單
    email = StringField('Email', validators=[DataRequired()])
    content = TextAreaField('留言內容', validators=[DataRequired()])
    submit = SubmitField('發佈留言')


class UpdateCommentForm(FlaskForm):
    # 更新留言的表單
    content = TextAreaField('留言內容', validators=[DataRequired()])
    submit = SubmitField('發佈留言')
