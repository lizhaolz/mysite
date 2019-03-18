from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db.models import ObjectDoesNotExist
from ckeditor.widgets import CKEditorWidget
from .models import Comment


class CommentForm(forms.Form):
    content_type = forms.CharField(widget=forms.HiddenInput)
    object_id = forms.IntegerField(widget=forms.HiddenInput)
    text = forms.CharField(widget=CKEditorWidget(config_name='comment_ckeditor'), error_messages={'required': '评论内容不能为空'})
    reply_comment_id = forms.IntegerField(widget=forms.HiddenInput(attrs={'id': 'reply_comment_id'}))

    def __init__(self, *args, **kwargs):     # *args为其他参数， **kwargs为关键字参数
        if 'user' in kwargs:  # 因为从blog_detail方法实例化的comment_form不含有user，而从update_comment方法实例化的comment_form含有user
            self.user = kwargs.pop('user')                   # 这里用pop是因为父类构造方法原来不需要user参数，这里一pop，直接剔除
        super(CommentForm, self).__init__(*args, **kwargs)    # 调用父类构造方法，python3可以简写为super().__init__(*args, **kwargs)

    def clean(self):
        # 判断用户是否登陆
        if self.user.is_authenticated:       # 前端页面验证不可靠，所以要重新验证
            self.cleaned_data['user'] = self.user
        else:
            raise forms.ValidationError('用户尚未登陆')
        content_type = self.cleaned_data['content_type']
        object_id = self.cleaned_data['object_id']
        try:
            model_class = ContentType.objects.get(model=content_type).model_class()
            model_obj = model_class.objects.get(pk=object_id)
            self.cleaned_data['content_object'] = model_obj
        except ObjectDoesNotExist:
            raise forms.ValidationError('评论对象不存在')
        return self.cleaned_data

    def clean_reply_comment_id(self):
        reply_comment_id = self.cleaned_data['reply_comment_id']
        if reply_comment_id < 0:
            raise forms.ValidationError('回复出错')
        elif reply_comment_id == 0:
            self.cleaned_data['parent'] = None
        elif Comment.objects.filter(pk=reply_comment_id).exists():
            self.cleaned_data['parent'] = Comment.objects.get(pk=reply_comment_id)
        else:
            raise forms.ValidationError('回复出错')
        return reply_comment_id

