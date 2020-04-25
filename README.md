# Django实战：Django 3.0 + Redis 3.4 + Celery 4.4异步生成静态HTML文件(附源码)

作者: 大江狗  微信公众号:【Python Web与Django开发】

### 项目描述

- 创建两个页面，一个用于创建页面，一个用于动态展示页面详情，并提供静态HMTL文件链接
- 一个页面创建完成后，使用Celery异步执行生成静态HTML文件的任务。
- 使用redis作为Celery的Broker
- 使用flower监控Celery异步任务执行情况


### 第一步：安装Django并创建项目myproject

使用pip命令安装Django.

```bash
pip install django==3.0.4 # 安装Django，所用版本为3.0.4
```

使用django-admin startproject myproject创立一个名为myproject的项目

```bash
django-admin startproject myproject
```
### 第二步：安装redis和项目依赖的第三方包

项目中我们需要使用redis做Celery的中间人(Broker), 所以需要先安装redis数据库。redis网上教程很多，这里就简要带过了。

- **Windows下载地址：**https://github.com/MSOpenTech/redis/releases
- **Linux下安装（Ubuntu系统)**：$ sudo apt-get install redis-server

本项目还需要安装如下依赖包，你可以使用pip命令逐一安装。

``` bash
pip install redis==3.4.1 
pip install celery==4.4.2 
pip install eventlet # celery 4.0+版本以后不支持在windows运行，还需额外安装eventlet库
```

你还可以myproject目录下新建`requirements.txt`加入所依赖的python包及版本，然后使用`pip install -r requirements.txt`命令安装所有依赖。本教程所使用的django, redis和celery均为最新版本。

```
django==3.0.5
redis==3.4.1 
celery==4.4.2  
eventlet # for windows only
```

### 第三步：Celery基本配置

1. 修改`settings.py`新增celery有关的配置。celery默认也是有自己的配置文件的，名为`celeryconfig.py`, 但由于管理多个配置文件很麻烦，我们把celery的配置参数也写在django的配置文件里。

```python
# 配置celery时区，默认时UTC。
if USE_TZ:
    timezone = TIME_ZONE

# celery配置redis作为broker。redis有16个数据库，编号0~15，这里使用第1个。
broker_url = 'redis://127.0.0.1:6379/0'

# 设置存储结果的后台
result_backend = 'redis://127.0.0.1:6379/0'

# 可接受的内容格式
accept_content = ["json"]
# 任务序列化数据格式
task_serializer = "json"
# 结果序列化数据格式
result_serializer = "json"

# 可选参数：给某个任务限流
# task_annotations = {'tasks.my_task': {'rate_limit': '10/s'}}

# 可选参数：给任务设置超时时间。超时立即中止worker
# task_time_limit = 10 * 60

# 可选参数：给任务设置软超时时间，超时抛出Exception
# task_soft_time_limit = 10 * 60

# 可选参数：如果使用django_celery_beat进行定时任务
# beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"

# 更多选项见
# https://docs.celeryproject.org/en/stable/userguide/configuration.html
```

2. 在`settings.py`同级目录下新建`celery.py`，添加如下内容:

```python
# coding:utf-8
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# 指定Django默认配置文件模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# 为我们的项目myproject创建一个Celery实例。这里不指定broker容易出现错误。
app = Celery('myproject', broker='redis://127.0.0.1:6379/0')

# 这里指定从django的settings.py里读取celery配置
app.config_from_object('django.conf:settings')

# 自动从所有已注册的django app中加载任务
app.autodiscover_tasks()

# 用于测试的异步任务
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


```

3. 打开`settings.py`同级目录下的`__init__.py`，添加如下内容, 确保项目启动时即加载Celery实例

```
# coding:utf-8
from __future__ import absolute_import, unicode_literals

# 引入celery实例对象
from .celery import app as celery_app
__all__ = ('celery_app',)
```

网上很多django redis + celery的教程比较老了, 坑很多。比如新版原生的Celery已经支持Django了，不需要再借助什么django-celery和celery-with-redis这种第三方库了, 配置参数名也由大写变成了小写，无需再加CELERY前缀。另外当你通过`app = Celery('myproject')`创建Celery实例时如果不指定Broker，很容易出现*[ERROR/MainProcess] consumer: Cannot connect to amqp://guest:**@127.0.0.1:5672//: [Errno 111] Connection refused*这个错误。

### 第四步：启动redis，测试celery是否配置成功

在Django中编写和执行自己的异步任务前，一定要先测试redis和celery是否安装好并配置成功。

首先你要启动redis服务。windows进入redis所在目录，使用`redis-server.exe`启动redis。Linux下使用`./redis-server redis.conf`启动，也可修改redis.conf将daemonize设置为yes, 确保守护进程开启。

启动redis服务后，你要先运行`python manage.py runserver`命令启动Django服务器（无需创建任何app)，然后再打开一个终端terminal窗口输入celery命令，启动worker。

```
# Linux下测试
Celery -A myproject worker -l info

# Windows下测试
Celery -A myproject worker -l info -P eventlet
```
如果你能看到[tasks]下所列异步任务清单如debug_task，以及最后一句celery@xxxx ready, 说明你的redis和celery都配置好了，可以开始正式工作了。
```bash

-------------- celery@DESKTOP-H3IHAKQ v4.4.2 (cliffs)
--- ***** -----
-- ******* ---- Windows-10-10.0.18362-SP0 2020-04-24 22:02:38

- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         myproject:0x456d1f0
- ** ---------- .> transport:   redis://127.0.0.1:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 4 (eventlet)
  -- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
  --- ***** -----
   -------------- [queues]
                .> celery           exchange=celery(direct) key=celery


[tasks]
  . myproject.celery.debug_task

[2020-04-24 22:02:38,484: INFO/MainProcess] Connected to redis://127.0.0.1:6379/0
[2020-04-24 22:02:38,500: INFO/MainProcess] mingle: searching for neighbors
[2020-04-24 22:02:39,544: INFO/MainProcess] mingle: all alone
[2020-04-24 22:02:39,572: INFO/MainProcess] pidbox: Connected to redis://127.0.0.1:6379/0.
[2020-04-24 22:02:39,578: WARNING/MainProcess] c:\users\missenka\pycharmprojects\django-static-html-generator\venv\lib\site-packages\celery\fixups\django.py:203: UserWarning: Using sett
ings.DEBUG leads to a memory
            leak, never use this setting in production environments!
  leak, never use this setting in production environments!''')
[2020-04-24 22:02:39,579: INFO/MainProcess] celery@DESKTOP-H3IHAKQ ready.
```

### 第五步：Django中创建新应用staticpage

cd进入`myproject`文件夹，使用`python manage.py startapp staticpage`创建一个名为`staticpage`的app。我们将创建一个简单的`Page`模型，并编写两个视图(对应两个URLs)，一个用于添加页面，一个用于展示页面详情。staticpage目录下我们将要编辑或创建5个.py文件，分别是models.py, urls.py, views.py, forms.py和tasks.py，其中前4个都是标准的Django项目文件，内容如下所示。最后一个tasks.py用于存放我们自己编写的异步任务，稍后我会详细讲解。

```python
# staticpage/models.py
from django.db import models
import os
from django.conf import settings

class Page(models.Model):
    title = models.CharField(max_length=100, verbose_name="标题")
    body = models.TextField(verbose_name="正文")

    def __int__(self):
        return self.title

    # 静态文件URL地址，比如/media/html/page_8.html
    def get_static_page_url(self):
        return os.path.join(settings.MEDIA_URL, 'html', 'page_{}.html'.format(self.id))

# staticpage/urls.py
from django.urls import path, re_path
from . import views


urlpatterns = [

    # Create a page 创建页面
    path('', views.page_create, name='page_create'),

    # Page detail 展示页面详情。动态URL地址为/page/8/
    re_path(r'^page/(?P<pk>\d+)/$', views.page_detail, name='page_detail'),

    ]

# staticpage/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import PageForm
from .models import Page
from .tasks import generate_static_page

def page_create(request):
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            page = form.save()
            generate_static_page.delay(page.id, page.title, page.body)
            return redirect(reverse('page_detail', args=[str(page.pk)]))
    else:
        form = PageForm()

    return render(request, 'staticpage/base.html', {'form': form})


def page_detail(request, pk):
    page = get_object_or_404(Page, id=pk)
    return render(request, 'staticpage/detail.html', {'page': page})

# staticpage/forms.py
from django import forms
from .models import Page


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        exclude = ()
```

从`page_create`视图函数中你可以看到我们在一个page实例存到数据库后调用了`generate_static_page`函数在后台完成静态HTML页面的生成。如果我们不使用异步的化，我们要等静态HTML文件完全生成后才能跳转到页面详情页面, 这有可能要等好几秒。`generate_static_page`就是我们自定义的异步任务，代码如下所示。Celery可以自动发现每个Django app下的异步任务，不用担心。

```python
# staticpage/tasks.py

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

```

本例中我们生成的静态HTML文件位于media文件夹下的html子文件夹里，这样做有两个好处：

- 与Django的静态文件存储规范保持一致：用户产生的静态文件都放在media文件下，网站本身所依赖的静态文件都放于static文件夹下。
- 把所有产生的静态文件放在一个目录里与动态文件相分开，利于后续通过nginx部署。

本项目中还用到了3个模板，分别是base.html, detail.html和template.html。base.html和detail.html是没有任何样式的, 仅用于动态显示内容，template.html用来生成静态文件，是带样式的，这样你就可以很快区分动态页面和静态页面。由于我们后台生成静态文件至少需要5秒钟，我们在detail.html用了点javascript实现等5秒倒计时完成后显示生成的静态HTML文件地址。

3个模板均位于`staticpage/templates/staticpage/`文件夹下，代码如下所示：

```html
# base.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>添加页面</title>
</head>
<body>
     <h2>添加页面</h2>
     <form name="myform"  method="POST" action=".">
         {% csrf_token %}
        {{ form.as_p }}
         <button type="submit">Submit</button>
     </form>
</body>
</html>

# detail.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ page.title }}</title>
</head>
<body>
     <h2>{{ page.title }}</h2>
     <p>{{ page.body }}</p>

     <p>倒计时: <span id="Time">5</span></p>
     <p id="static_url" style="display:none;"> <small><a href='{{ page.get_static_page_url }}'>跳转到静态文件</a></small></p>


<script>
 //使用匿名函数方法
 function countDown(){
 var time = document.getElementById("Time");
 var p = document.getElementById("static_url");
 //获取到id为time标签中的内容，现进行判断
 if(time.innerHTML == 0){
 //等于0时, 显示静态HTML文件URL
 p.style.display = "block";
 }else{
 time.innerHTML = time.innerHTML-1;
 }
 }
 //1000毫秒调用一次
 window.setInterval("countDown()",1000);
 </script>

</body>
</html>

# template.html 生成静态文件模板
{% load static %}
<html lang="en">
<head>
<title>{% block title %}Django文档管理{% endblock %} </title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
</head>

<body>
<nav class="navbar navbar-inverse navbar-static-top bs-docs-nav">

  <div class="container">
    <div class="navbar-header">
        <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#myNavbar">
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>                        
      </button>
        <a class="navbar-brand" href="#"><strong>Django + Celery + Redis异步生成静态文件</strong></a>
     </div>

      <div class="collapse navbar-collapse" id="myNavbar">
       <ul class="nav navbar-nav navbar-right">
		 {% if request.user.is_authenticated %}

          <li class="dropdown">
              <a class="dropdown-toggle btn-green" data-toggle="dropdown" href="#"><span class="glyphicon glyphicon-user"></span>  {{ request.user.username }} <span class="caret"></span></a>
            <ul class="dropdown-menu">
              <li><a  href="#">My Account</a></li>
              <li><a  href="#">Logout</a></li>
            </ul>
          </li>  
         {% else %}		  
            <li class="dropdown"><a class="dropdown-toggle btn-green" href="#"><span class="glyphicon glyphicon-user"></span> Sign Up</a></li>
			<li class="dropdown"><a class="dropdown-toggle" href="#" ><span class="glyphicon glyphicon-log-in"></span> Login</a></li>
		 {% endif %}
       </ul>

    </div>

  </div>
</nav>    

 <!-- Page content of course! -->
<main id="section1" class="container-fluid">
 
<div class="container">
    <div class="row">
     <div class="col-sm-3  col-hide">
         <ul>
             <li> <a href="{% url 'page_create' %}">添加页面</a> </li>
         </ul>
     </div>

     <div class="col-sm-9">
          <h3>{{ page.title }}</h3>
         {{ page.body }}
     </div>
</div>


</div> 
</main>


<footer class="footer">
  {% block footer %}{% endblock %}
</footer>
<!--End of Footer-->


<script src="https://code.jquery.com/jquery-3.3.1.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>

</body>
</html>
```

### 第六步：在Django中注册app并添加app的URLConf

```python
# myproject/settings.py
# 注册app
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'staticpage',
]

# 设置STATIC_URL和STATIC_ROOT

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# 设置MEDIA_ROOT和MEDIA_URL
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# myproject/urls.py
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("staticpage.urls")),
]

# Django自带服务器默认不支持静态文件，需加入这两行。
if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

### 第七步：启动Django服务器和Celery服务

如果一切顺利，连续使用如下命令, 即可启动Django测试服务器。打开http://127.0.0.1:8000/即可看到我们项目开头的动画啦。注意：请确保redis和celery已同时开启。

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

如果你要监控异步任务的运行状态（比如是否成功，是否有返回结果), 还可以安装flower这个Celery监控工具。

```python
pip install flower
```

安装好后，你有如下两种方式启动服务器。启动服务器后，打开[http://localhost:5555](http://localhost:5555/)即可查看监控情况。

```bash
# 从terminal终端启动, proj为项目名
$ flower -A proj --port=5555  
# 从celery启动
$ celery flower -A proj --address=127.0.0.1 --port=5555
```



