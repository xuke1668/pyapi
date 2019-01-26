# coding: utf-8
"""
接口文档
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
利用注释生成接口文档
"""
import re
from flask import current_app, url_for, render_template_string


html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <title>接口文档</title>
    <link href="//lib.sinaapp.com/js/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .menu {
            height: 100%;
            overflow-y: scroll;
        }
        .sidenav > li > a {
            padding: 10px 8px;
            font-size: 12px;
            font-weight: 600;
            color: #4A515B;
            background: #E9E9E9;
            background: linear-gradient(top, #FAFAFA 0%,#E9E9E9 100%);
            filter: progid:DXImageTransform.Microsoft.gradient(startColorstr='#FAFAFA', endColorstr='#E9E9E9');
            border: 1px solid #D5D5D5;
            border-radius: 4px;
        }
        .sidenav > li > a:hover {
            color: #FFF;
            background: #3C4049;
            background: linear-gradient(top, #4A515B 0%,#3C4049 100%);
            filter: progid:DXImageTransform.Microsoft.gradient(startColorstr='#4A515B', endColorstr='#3C4049');
            border-color: #2B2E33;
        }
        .sidenav > li > a:hover > span {
            color: #FFF;
        }
        .sidenav > li > a > span {
            color: #4A515B;
        }
        .sidenav > li {
            margin-bottom: 4px;
        }
        .nav-item a {
            font-size: 10px;
            color: #4A515B;
        }
    </style>
</head>

<body>
    <div class="container-fluid">
        <div class="row">
            <div id="topnav" class="col-md-12 navbar navbar-default">
                <div class="container-fluid">
                    <div class="navbar-header">
                        <a id="brand" class="navbar-brand" href="#">{{ config.get("APP_NAME") }} 接口文档</a>
                    </div>
                    <div class="navbar-header pull-right">
                        <span class="navbar-brand">当前版本：{{ config.get("APP_VERSION") }}</span>
                        <span class="navbar-brand">更新时间：{{ config.get("APP_UPDATE_TIME") }}</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="row">
            <div id="sidenav" class="col-md-2 menu">
                <ul class="nav nav-pills nav-stacked sidenav">
                    {%- for mod, mod_data in api_data.items() %}
                    <li>
                        <a href="#{{ mod }}" class="nav-header collapsed" data-toggle="collapse">
                            {{ mod }}
                            <span class="pull-right"></span>
                        </a>
                        <ul id="{{ mod }}" class="nav collapse">
                            {%- for api in mod_data %}
                            <li class="nav-item">
                                <a href="javascript:void(0)" onclick="locateEle('{{ api['key'] }}')">
                                    {{ api['name'] }}
                                </a>
                            </li>
                            {%- endfor %}
                        </ul>
                    </li>
                    {%- endfor %}
                    <li>
                        <a href="#common" class="nav-header collapsed" data-toggle="collapse">
                            接口约定
                            <span class="pull-right"></span>
                        </a>
                        <ul id="common" class="nav collapse">
                            <li class="nav-item">
                                <a href="javascript:void(0)" onclick="locateEle('common-params')">
                                    公共参数
                                </a>
                            </li>
                            <li class="nav-item">
                                <a href="javascript:void(0)" onclick="locateEle('response_code')">
                                    返回码
                                </a>
                            </li>
                        </ul>
                    </li>
                </ul>
            </div>
            <div class="col-md-10 pull-right">
                {%- for mod, mod_data in api_data.items() %}
                <section>
                    <h1>{{ mod }}</h1>
                    {%- for api in mod_data %}
                    <article id="{{ api['key'] }}" data-group="{{ mod }}" >
                        <h3>接口地址: {{ api['url'] }}</h3>
                        <p>描述：{{ api['desc'] }}</p>
                        <p>权限：{{ api['priv'] }}</p>
                        <table class="table table-bordered table-hover table-condensed">
                            <tr><th colspan="4">请求参数</th></tr>
                            {%- if api['params'] %}
                            <tr><th width="35%">字段</th><th width="8%">类型</th><th width="7%">必需</th><th width="50%">描述</th></tr>
                            {%- else %}
                            <tr><td colspan="4">无</td></tr>
                            {%- endif %}
                            {%- for p in api['params'] %}
                            <tr><td>{{ p['name'] |safe }}</td><td>{{ p['type'] }}</td><td>{{ p['option'] }}</td><td>{{ p['desc'] }}</td></tr>
                            {%- endfor %}
                        </table>
                        <table class="table table-bordered table-hover table-condensed">
                            <tr><th colspan="3">返回值</th></tr>
                            {%- if api['return'] %}
                            <tr><th width="35%">字段</th><th width="8%">类型</th><th width="57%">描述</th></tr>
                            {%- else %}
                            <tr><td colspan="3">无</td></tr>
                            {%- endif %}
                            {%- for r in api['return'] %}
                            <tr><td>{{ r['name'] |safe }}</td><td>{{ r['type'] }}</td><td>{{ r['desc'] }}</td></tr>
                            {%- endfor %}
                        </table>
                        <div>
                            <p>数据示例：</p>
                            <code>{{ api['example'] |safe }}</code>
                        </div>
                    </article>
                    <hr>
                    {%- endfor %}
                </section>
                {%- endfor %}
                <section>
                    <h1>接口约定</h1>
                    <article id="common-params">
                        <h3>公共参数</h3>
                        <table class="table table-bordered table-hover table-condensed">
                            {%- if not common_param_list %}
                            <tr>
                                <td>无</td>
                            </tr>
                            {%- else %}
                            <tr><th colspan="4">公共参数</th></tr>
                            <tr><th width="35%">字段</th><th width="8%">类型</th><th width="7%">必需</th><th width="50%">描述</th></tr>
                            {%- for field in common_param_list %}
                            <tr><td>{{ field.name }}</td><td>{{ field.type }}</td><td>{{ field.required }}</td><td>{{ field.desc }}</td></tr>
                            {%- endfor %}
                            {%- endif %}
                        </table>
                    </article>
                    
                    <article id="response_code">
                        <h3>返回码</h3>
                        <table class="table table-bordered table-hover">
                            {%- if not response_code_list %}
                            <tr>
                                <td>无</td>
                            </tr>
                            {%- else %}
                            <tr>
                                <th>返回码</th>
                                <th>含义描述</th>
                            <tr>
                            {%- for err, code in response_code_list.items() %}
                            <tr>
                                <td><strong>{{ code[0] }}</strong></td>
                                <td>{{ code[1] }}</td>
                            </tr>
                            {%- endfor %}
                            {%- endif %}
                        </table>
                    </article>
                </section>
            </div>
        </div>
    </div>
    <script src="//lib.sinaapp.com/js/jquery/3.1.0/jquery-3.1.0.min.js"></script>
    <script src="//lib.sinaapp.com/js/bootstrap/3.3.7/js/bootstrap.min.js"></script>
    <script>
        /* 定位后避开顶部导航 */
        function locateEle(id){
            var ele = $("#" + id);
            var ele_top = ele.offset().top;
            while(ele=ele.offset().parent){ ele_top += ele.offset().top; }
            var topnav_top = $('#topnav').outerHeight() + 20;
            if (window.scrollY > 0) {
                ele_top -= topnav_top;   /* 去掉顶部栏高度 */
            }else{
                ele_top -= topnav_top * 2;   /* 去掉顶部栏高度 */
            }
            window.scrollTo(0, ele_top);
        }
        /* 重新定位以固定菜单 */
        function locateNav(){
            var doc_top = Math.max(document.body.scrollTop, document.documentElement.scrollTop);
            if (doc_top > topnav_top) {
                topnav.css({position: 'fixed', top: '0px', zIndex: '999'});
            } else {
                topnav.removeAttr('style');
            }
            if (doc_top + topnav_height + 20 > sidenav_top) {
                sidenav.css({position: 'fixed', top: topnav_height + 20 + 'px', zIndex: '999', height: window.innerHeight - 40 - topnav_height + 'px'});
            } else {
                sidenav.css({height: window.innerHeight - 40 - topnav_height + 'px'});
            }
        }

        $(function(){
            window.topnav = $('#topnav');
            window.topnav_height = topnav.outerHeight();
            window.topnav_top = topnav.offset().top - parseFloat(topnav.css('marginTop').replace(/auto/, 0));

            window.sidenav = $('#sidenav');
            window.sidenav_height = sidenav.outerHeight();
            window.sidenav_top = sidenav.offset().top - parseFloat(sidenav.css('marginTop').replace(/auto/, 0));

            locateNav(); /* 刷新页面后立马进行一次定位 */
            window.onscroll = locateNav;
        });
    </script>
</body>
</html>
"""


def generate_doc(view_functions=None, common_param_list=None, response_code_list=None):
    """生成接口文档"""

    view_functions = view_functions if view_functions else current_app.view_functions.items()
    common_param_list = common_param_list if common_param_list else []
    response_code_list = response_code_list if response_code_list else []

    re_ignore = re.compile(r"\s*#ignore_doc\s*")
    re_group = re.compile(r"\s*#group\s*(.*)\s*")                                   # 接口归属分组
    re_name = re.compile(r"\s*#name\s*(.*)\s*")                                     # 接口名称
    re_desc = re.compile(r"\s*#desc\s*(.*)\s*")                                     # 接口描述
    re_priv = re.compile(r"\s*#priv\s*(.*)\s*")                                     # 接口权限
    re_params = re.compile(r"\s*#param\s*(.*)\s*")                                  # 接口参数
    re_rets = re.compile(r"\s*#return\s*(.*)\s*")                                   # 接口返回值
    re_example = re.compile(r"(?<=#example)\s*(.*)\s*$", re.S | re.M)               # 接口示例（一直取到最后）
    re_params_field = re.compile(r"^([a-zA-Z0-9_\\.\-\[\]]+)\s*(?:<([^<>]*)>)?\s*(?:<([^<>]*)>)?\s*(.*)$")    # 参数字段内容分隔
    re_return_field = re.compile(r"^([a-zA-Z0-9_\\.\-\[\]]+)\s*(?:<([^<>]*)>)?\s*(.*)$")  # 返回值字段内容分隔
    em = re.compile(r"([a-zA-Z0-9_\[\]]+\.)")                                       # 多级字段匹配

    api_data = {}
    for k, v in view_functions:
        if k == "static":
            continue

        doc = v.__doc__ or ""
        if re_ignore.findall(doc):
            continue

        name = re_name.findall(doc) or [k]
        desc = re_desc.findall(doc) or [""]
        priv = re_priv.findall(doc) or ["-"]
        group = re_group.findall(doc) or ["未分类"]
        params = re_params.findall(doc) or []
        rets = re_rets.findall(doc) or []
        example = re_example.findall(doc) or [""]

        params_data = []
        for p in params:
            p_match = re_params_field.match(p)
            if p_match:
                p_name, p_type, p_option, p_desc = p_match.group(1, 2, 3, 4)
                p_name = em.sub(r"<small><em>\1</em></small>", p_name)
                params_data.append({"name": p_name, "type": p_type, "option": p_option if p_option else '必需', "desc": p_desc})

        return_data = []
        for r in rets:
            r_match = re_return_field.match(r)
            if r_match:
                r_name, r_type, r_desc = r_match.group(1, 2, 3)
                r_name = em.sub(r"<small><em>\1</em></small>", r_name)
                return_data.append({"name": r_name, "type": r_type, "desc": r_desc})

        api = {"key": k.replace(".", "-"), "name": name[0], "url": url_for(k), "desc": desc[0], "priv": priv[0],
               "params": params_data, "return": return_data,
               "example": "&nbsp;&nbsp;&nbsp;&nbsp;" + example[0].replace("\n", "<br>").replace(" ", "&nbsp;")
               }
        api_data.setdefault(group[0], []).append(api)

    return render_template_string(html, api_data=api_data, common_param_list=common_param_list, response_code_list=response_code_list)
