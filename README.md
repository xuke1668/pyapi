# pyapi
pyapi是一个基于Flask框架的api项目脚手架，是从实际应用中精简而来，用于快速构建api项目，或者用于Flask框架初学者上手。


## 简要说明
#### 使用蓝图结构
    src/api是蓝图包目录，如果有多个模块，可以创建多个。
    src/api/__init__是关于蓝图的特殊配置，如果多个蓝图有共同逻辑，也可以提取到src下的__init__中以app形式注册挂载。

#### 统一认证身份
    src/auth.py有用来生成和清除token的方法，以及验证token的装饰器函数。

#### 统一处理返回值
    src/response.py有用来做接口返回数据json化处理的函数，以及全局定义的参数及返回值列表。

#### 功能插件
    src/logger.py是提供程序日志功能的插件，其实主要用来配置日志参数。
    src/cache.py是缓存插件，有基于内存的MemCache简单缓存和基于Redis的RedisCache缓存。
    src/doc.py是生成接口文档的插件，根据注册在Flask中视图函数的注释自动生成接口文档，并注册为/doc/页面，可以按需要指定生成接口文档的蓝图。

#### 配置文件
    src/config.py用来配置应用的参数。

#### 服务或工具函数
    src/service.py中是一些调用外部服务的函数。
    src/tool.py中是一些常用的工具函数。

#### 启动管理
    run.sh脚本使用uWSGI进行生产环境下的启动管理，注意如果有多环境，请使用正确的uWSGI程序。
    app.py用来指定工厂函数的创建，可以在命令行执行flask run命令启动，同时也配合run.sh以uWSGI模式运行项目，两者都可以通过环境变量控制启动模式。


## 运行使用
#### 外部组件依赖
    需要安装MySQL作为数据存储。
    可选安装Redis作为数据缓存，src/__init__示例文件中导入的是Redis缓存。也可以使用简单的内存缓存。

#### 安装依赖包
    主要依赖都在requirement.txt中。
    值得说明的是由于示例接口中有使用阿里的oss存储头像文件，所以里面有个阿里oss的依赖包。但这不是必须的，也可以用其他存储方式。

#### 创建基本库表
    app.py中有基本的数据库管理命令，可以在命令行执行flask init_db初始化库表结构。

#### 运行程序
    在开发环境中（以pychram举例），配置【Run/Debug configurations】，选择正确的解释器，在module模式内输入【flask】，脚本参数输入【run】，如需要prod环境可在环境变量里加入【APP_ENV=prod】。
    在生产环境中（以CentOS/Ubuntu举例），配置run.sh中uWSGI程序的正确路径，配置uWSGI的启动端口，然后运行脚本即可。脚本内默认使用prod环境启动，如需要dev环境可在run.sh脚本中修改app_env配置。
    需要注意的是示例脚本中uWSGI是以socket形式启动的，需要配置Web服务器作为代理（如Nginx）。或者将run.sh的start函数中用于uWSGI启动的【-s ${host}:${port}】命令项改为【--http-socket ${host}:${port}】这样就能直接访问了。

#### 开始使用
    可以先使用示例接口里的注册接口进行账号注册，然后将接口返回的token字段放到请求头中，然后再请求其他几个接口。
    如果是以测试模式启动的话，可以访问{{host}}/doc/页面查看示例接口的文档。

## 相关文档
- [Flask中文文档](https://dormousehole.readthedocs.io/en/latest/)
- [uWSGI中文文档](https://uwsgi-docs-zh.readthedocs.io/zh_CN/latest/index.html)


## 买杯咖啡支持一下
<img src="./pay4coffee.png" width="400" height="200" alt="买杯咖啡支持一下" align=center />