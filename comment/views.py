from django.shortcuts import render, redirect
from .models import Comment
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.http import JsonResponse
from django.utils.timezone import localtime
from .forms import CommentForm


def update_comment(request):
    '''
    referer = request.META.get('HTTP_REFERER', reverse('home'))  # 得到从哪个url来的请求，默认值为反向解析的别名为home的url
    user = request.user
    # 数据检查
    if not user.is_authenticated:
        return render(request, 'error.html', {'message': '用户未登陆', 'redirect_to': referer})
    text = request.POST.get('text', '').strip()          # strip()去掉空格
    if text == '':
        return render(request, 'error.html', {'message': '评论内容为空', 'redirect_to': referer})
    try:
        content_type = request.POST.get('content_type', '')
        object_id = request.POST.get('object_id', '')
        model_class = ContentType.objects.get(model=content_type).model_class()     # 这里之所以不用ContentType.objects.get_for_model(obj)，是因为得到的content_type是字符串，而不是对象类型
        model_obj = model_class.objects.get(pk=object_id)
    except Exception as e:
        return render(request, 'error.html', {'message': '评论对象不存在', 'redirect_to': referer})
    comment = Comment()
    comment.user = user
    comment.text = text
    comment.content_object = model_obj
    comment.save()
    return redirect(referer)
    '''
    referer = request.META.get('HTTP_REFERER', reverse('home'))
    comment_form = CommentForm(request.POST, user=request.user)
    data = {}
    if comment_form.is_valid():
        # 检查通过，保存数据
        comment = Comment()
        comment.user = comment_form.cleaned_data['user']
        comment.text = comment_form.cleaned_data['text']
        comment.content_object = comment_form.cleaned_data['content_object']
        parent = comment_form.cleaned_data['parent']
        if not parent is None:
            comment.root = parent.root if not parent.root is None else parent
            comment.parent = parent
            comment.reply_to = parent.user
        comment.save()
        # 发送邮件通知
        comment.send_mail()
        # return redirect(referer),这里的data都是Ajax提交的数据
        data['status'] = 'SUCCESS'
        data['username'] = comment.user.get_nickname_or_username()
        data['comment_time'] = localtime(comment.comment_time).strftime('%Y-%m-%d %H:%M:%S')
        data['text'] = comment.text
        data['content_type'] = ContentType.objects.get_for_model(comment).model
        # 判断是否是回复
        if not parent is None:
            data['reply_to'] = comment.reply_to.get_nickname_or_username()
        else:
            data['reply_to'] = ''
        data['pk'] = comment.pk
        data['root_pk'] = comment.root.pk if not comment.root is None else ''
    else:
        # return render(request, 'error.html', {'message': comment_form.errors, 'redirect_to': referer})
        data['status'] = 'ERROR'
        data['message'] = list(comment_form.errors.values())[0][0]  # 字典转列表，抛出第一个错误信息
    return JsonResponse(data)
# Create your views here.