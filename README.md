# pyapi
pyapi是一个基于Flask框架的api项目脚手架，是从实际应用中精简而来，用于快速构建api项目，或者用于Flask框架初学者上手。


## 简要说明
#### 使用蓝图结构
    src/api是蓝图包目录，如果有多个模块，可以创建多个。
    src/api/__init__是关于蓝图的特殊配置，如果多个蓝图有共同逻辑，也可以提取到项目包的__init__中。

#### 统一认证身份
    src/auth.py有用来验证token的装饰器函数。

#### 统一处理返回值
    src/response.py有用来做接口返回的函数。

#### 自动生成接口文档
    src/doc.py有用来生成接口文档的函数，根据注册在Flask中视图函数的注释生成。（思路参考了apidoc项目）
    可以选择全局生成，也可以选择生成指定的蓝图模块文档，示例代码中生成的蓝图文档。

#### 功能插件
    src/logger.py是提供程序日志功能的插件，其实主要用来配置日志参数。
    src/cache.py是缓存插件，有基于内存的MemCache简单缓存和基于Redis的RedisCache缓存。

#### 配置文件
    src/config.py用来配置应用的参数，可以在工厂模式创建程序时选择不同的启动环境。

#### 启动管理
    manage.py用来在开发调试时使用，直接执行就可以了。
    run.sh脚本使用uWSGI进行生产环境下的启动管理，注意如果有多环境，请使用正确的uWSGI程序。（仅在CentOS中正常使用过）

#### 其他
    src/service.py中是一些调用外部服务的函数。
    src/tool.py中是一些常用的工具函数。


## 运行使用
#### 外部环境
    需要安装MySQL作为数据存储。
    可选安装Redis作为数据缓存，src/__init__示例文件中导入的是Redis缓存。也可以使用简单的内存缓存。

#### 安装依赖
    主要依赖都在requirement.txt中。
    值得说明的是由于示例接口中有使用阿里的oss存储头像文件，所以里面有个阿里oss的依赖包。这不是必须的，也可以用其他存储方式。

#### 创建基本库表
    使用Python执行manage.py脚本的init_db选项初始化表结构。

#### 运行程序
    在开发环境中（以pychram举例），配置【Run/Debug configurations】，使用正确的Python环境运行manage.py即可。
    在生产环境中（以CentOS举例），配置run.sh中uWSGI程序的正确路径，配置uWSGI的启动端口，然后运行脚本即可。
    需要注意的是示例脚本中uWSGI是以socket形式启动的，需要配置Web服务器作为代理（如Nginx）。或者将start函数中用于uWSGI启
    动的【-s ${host}:${port}】命令项改为【--http-socket ${host}:${port}】这样就能直接访问了。

#### 开始使用
    可以先使用示例接口里的注册接口进行账号注册，然后体验其他几个接口。

## 相关文档
- [Flask中文文档](https://dormousehole.readthedocs.io/en/latest/)
- [uWSGI中文文档](https://uwsgi-docs-zh.readthedocs.io/zh_CN/latest/index.html)

