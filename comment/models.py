import threading
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
# Create your models here.


#  创建多线程类
class SendMail(threading.Thread):
    def __init__(self, subject, text, email, fail_silently=False):
        self.subject = subject
        self.text = text
        self.email = email
        self.fail_silently = fail_silently
        threading.Thread.__init__(self)

    def run(self):
        send_mail(self.subject, '', settings.EMAIL_HOST_USER, [self.email], fail_silently=self.fail_silently,
                  html_message=self.text)  # html_message 可以解释文本中html标签


class Comment(models.Model):
    text = models.TextField()
    comment_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name="comments", on_delete=models.CASCADE)  # 通过user外键可以反向解析得到这个user相关的评论内容，
    # 例如user.comment_set.all()就可以得到，本质是user对象.comment(模型名称小写)+_set+.all()就可以得到，那么当规定了related_name参数后，直接可以用user.related_name参数.all()得到
    # 即related_name是反向解析的方法的别名

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type',
                                       'object_id')  # content_type 和 object_id都不用填写，这两都是为content_object服务
    root = models.ForeignKey('self', null=True, related_name="root_comment", on_delete=models.CASCADE)  # 获取所有回复的根
    parent = models.ForeignKey('self', null=True, related_name="parent_comment",
                               on_delete=models.CASCADE)  # null=True代表允许为空，因为第一条评论的parent为空
    reply_to = models.ForeignKey(User, null=True, related_name="replies",
                                 on_delete=models.CASCADE)  # related_name就是它反向解析的名字，

    # 另外一个原因，加related_name是为了解决user字段和reply_to字段都关联User外键的冲突问题，related_name的值若为‘+’，则代表不创建反向关系

    def send_mail(self):
        if self.parent is None:
            # 评论我的博客
            subject = '有人评论了你的博客'
            email = self.content_object.get_email()
        else:
            # 回复评论
            subject = '有人回复了你的评论'
            email = self.reply_to.email
        if email != '':
            context = {}
            context['comment_text'] = self.text
            context['url'] = self.content_object.get_url()
            text = render_to_string('comment/send_mail.html', context)
            send_email = SendMail(subject, text, email)  # 多线程发送邮件
            send_email.start()

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['-comment_time']
