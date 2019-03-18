import string
import random
import time
from django.shortcuts import render, redirect
from django.contrib import auth
from django.urls import reverse
from django.contrib.auth.models import User
from .forms import LoginForm
from .forms import RegForm
from .forms import ChangeNicknameForm, BindEmailForm, ChangePasswordForm,ForgotPasswordForm
from .models import Profile
from django.http import JsonResponse
from django.core.mail import send_mail


def login(request):
    '''username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    user = auth.authenticate(request, username=username, password=password)
    referer = request.META.get('HTTP_REFERER', reverse('home'))           # 获取他是从哪个页面跳转来的,如果获取不到，就默认为首页 ,reverse(home)的意思是将别名“home"反向解析为链接
    if user is not None:
        auth.login(request, user)
        return redirect(referer)  # 登陆成功的话重定向到它进来的页面
    else:
        return render(request, 'error.html', {'message': '用户名或密码不正确', 'redirect_to': referer})'''
    if request.method == 'POST':            # 判断进入login方法是因为加载页面还是因为提交数据，即是因为bolog_detail页面的登陆按钮引起的（GET）还是login界面的登陆按钮引起的（POST）
        login_form = LoginForm(request.POST)
        if login_form.is_valid():    # login_form有效 自动调用forms.py里的clean方法
            user = login_form.cleaned_data['user']
            auth.login(request, user)
            return redirect(request.GET.get('from', reverse('home')))
    else:
        login_form = LoginForm()
    context = {}
    context['login_form'] = login_form
    return render(request, 'user/login.html', context)


def login_form_modal(request):
    login_form = LoginForm(request.POST)
    data = {}
    if login_form.is_valid():
        user = login_form.cleaned_data['user']
        auth.login(request, user)
        data['status'] = 'SUCCESS'
    else:
        data['status'] = 'ERROR'
    return JsonResponse(data)


def register(request):
    if request.method == 'POST':            # 判断进入login方法是因为加载页面还是因为提交数据，即是因为bolog_detail页面的登陆按钮引起的（GET）还是login界面的登陆按钮引起的（POST）
        reg_form = RegForm(request.POST, request=request)
        # 注册用户
        if reg_form.is_valid():
            username = reg_form.cleaned_data['username']
            email = reg_form.cleaned_data['email']
            password = reg_form.cleaned_data['password']
            user = User.objects.create_user(username, email, password)
            user.save()
            # 清除session
            del request.session['register_code']
            '''
            或者
            user = USer()
            user.username=username
            user.email = email
            user.set_password(password)
            user.save()
            '''
            #  登陆用户
            user = auth.authenticate(username=username, password=password)
            auth.login(request, user)
            return redirect(request.GET.get('from', reverse('home')))  # 虽然是POST方式，但这里的POST说的是数据提交时用的POST方法，而from参数传递时用的GET方法
    else:
        reg_form = RegForm()
    context = {}
    context['reg_form'] = reg_form
    return render(request, 'user/register.html', context)


def logout(request):
    auth.logout(request)
    return redirect(request.GET.get('from', reverse('home')))


def user_info(request):
    context = {}
    return render(request, 'user/user_info.html', context)


def change_nickname(request):
    redirect_ro = request.GET.get('from', reverse('home'))
    if request.method == 'POST':
        form = ChangeNicknameForm(request.POST, user=request.user)
        if form.is_valid():  # 好像不执行form.is_valid()函数，就不能用cleaned_data
            nickname_new = form.cleaned_data['nickname_new']
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.nickname = nickname_new
            profile.save()
            return redirect(redirect_ro)
    else:
        form = ChangeNicknameForm()
    context = {}
    context['form'] = form
    context['page_title'] = '修改昵称'
    context['form_title'] = '修改昵称'
    context['submit_text'] = '修改'
    context['return_back_url'] = redirect_ro
    return render(request, 'form.html', context)


def bind_email(request):
    redirect_to = request.GET.get('from', reverse('home'))
    if request.method == 'POST':
        form = BindEmailForm(request.POST, request=request)
        if form.is_valid():
            email = form.cleaned_data['email']
            request.user.email = email
            request.user.save()
            # 清除session
            del request.session['bind_email_code']
            return redirect(redirect_to)
    else:
        form = BindEmailForm()
    context = {}
    context['form'] = form
    context['page_title'] = '绑定邮箱'
    context['form_title'] = '绑定邮箱'
    context['submit_text'] = '绑定'
    context['return_back_url'] = redirect_to
    return render(request, 'user/bind_email.html', context)


def send_verification_code(request):
    email = request.GET.get('email', '')
    send_for = request.GET.get('send_for', '')
    data = {}
    if email != '':
        # 生成验证码
        code = ''.join(random.sample(string.ascii_letters+string.digits, 4))
        now = int(time.time())
        send_code_time = request.session.get('send_code_time', 0)
        if now - send_code_time < 30:
            data['status'] = 'ERROR'
        else:
            request.session[send_for] = code
            request.session['send_code_time'] = now
            # 发送邮件
            send_mail(
                '绑定邮箱',
                '验证码：%s' % code,
                '1094363895@qq.com',  # 从哪发
                [email],  # 发给谁
                fail_silently=False,  # 忽视错误
            )
            data['status'] = 'SUCCESS'
    else:
        data['status'] = '卧槽'
    return JsonResponse(data)


def change_password(request):
    redirect_to = reverse('home')
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            auth.logout(request)  # 修改密码之后的登出操作
            return redirect(redirect_to)
    else:
        form = ChangePasswordForm()
        context = {}
        context['page_title'] = '修改密码'
        context['form_title'] = '修改密码'
        context['submit_text'] = '修改'
        context['form'] = form
        context['return_back_url'] = redirect_to
        return render(request, 'form.html', context)


def forgot_password(request):
    redirect_to = reverse('home')
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST, request=request)
        if form.is_valid():
            email = form.cleaned_data['email']
            new_password = form.cleaned_data['new_password']
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            # 清除session
            del request.session['forgot_password_code']
            return redirect(redirect_to)
    else:
        form = ForgotPasswordForm()
    context = {}
    context['form'] = form
    context['page_title'] = '重置密码'
    context['form_title'] = '重置密码'
    context['submit_text'] = '重置'
    context['return_back_url'] = redirect_to
    return render(request, 'user/forgot_password.html', context)
