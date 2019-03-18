from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from .models import LikeCount, LikeRecord
from django.http import JsonResponse
from django.db.models import ObjectDoesNotExist


def ErrorResponse(code, message):
    data = {}
    data['status'] = 'ERROR'
    data['code'] = code
    data['message'] = message
    return JsonResponse(data)


def SuccessResponse(like_num):
    data = {}
    data['status'] = 'SUCCESS'
    data['like_num'] = like_num
    return JsonResponse(data)


def like_change(request):
    user = request.user
    if not user.is_authenticated:
        return ErrorResponse(400, '你还未登陆')
    content_type = request.GET.get('content_type')
    object_id = int(request.GET.get('object_id'))
    try:
        content_type = ContentType.objects.get(model=content_type)
        model_class = content_type.model_class()
        model_obj = model_class.objects.get(pk=object_id)
    except ObjectDoesNotExist:
        return ErrorResponse(401, '对象不存在')

    # 处理数据
    if request.GET.get('is_like') == 'true':  # 要点赞 ，因为request请求获得的值都是字符串类型的，所以为字符串'true'
        like_record, created = LikeRecord.objects.get_or_create(content_type=content_type, object_id=object_id, user=user)  # 第二个参数为布尔值，代表它是获取的还是创建的
        if created:  # 如果是创建的，代表这个用户对这个类型，这个id的模型未点过赞，可以点赞
            like_count, created = LikeCount.objects.get_or_create(content_type=content_type, object_id=object_id)
            like_count.like_num += 1
            like_count.save()
            return SuccessResponse(like_count.like_num)
        else:  # 代表这个用户对这个类型，这个id的模型已经点过赞，不能再点
            return ErrorResponse(402, '你已经点赞过')
    else:  # 要取消点赞
        if LikeRecord.objects.filter(content_type=content_type, object_id=object_id, user=user).exists():  # 以前点过赞
            like_record = LikeRecord.objects.get(content_type=content_type, object_id=object_id, user=user)
            like_record.delete()
            # 点赞总数减一
            like_count, created = LikeCount.objects.get_or_create(content_type=content_type, object_id=object_id)
            if not created:  # 不是被创建的，之前点赞总数记录存在
                like_count.like_num -= 1
                like_count.save()
                return SuccessResponse(like_count.like_num)
            else:  # 之前点赞总数记录不存咋
                return ErrorResponse(404, '数据错误')
        else:  # 这个用户之前没点过赞
            return ErrorResponse(403, '你之前未点过赞')
# Create your views here.
