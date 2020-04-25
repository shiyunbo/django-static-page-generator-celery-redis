import os, time
from django.template.loader import render_to_string
from django.conf import settings
from celery import shared_task


@shared_task
def generate_static_page(page_id, page_title, page_body):
    # 模拟耗时任务，比如写入文件或发送邮件等操作。
    time.sleep(5)

    # 获取传递的参数
    page = {'title': page_title, 'body': page_body}
    context = {'page': page, }

    # 渲染模板，生成字符串
    content = render_to_string('staticpage/template.html', context)

    # 定义生成静态文件所属目录，位于media文件夹下名为html的子文件夹里。如目录不存在，则创建。
    directory = os.path.join(settings.MEDIA_ROOT, "html")
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 拼接目标写入文件地址
    static_html_path = os.path.join(directory, 'page_{}.html'.format(page_id))

    # 将渲染过的字符串写入目标文件
    with open(static_html_path, 'w', encoding="utf-8") as f:
            f.write(content)
