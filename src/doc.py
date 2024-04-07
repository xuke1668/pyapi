# coding: utf-8
"""
接口文档
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
利用注释生成接口文档
"""
import re
from functools import partial

from flask import url_for, render_template_string


PAGE_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <title>接口文档</title>
    <link href="//lib.sinaapp.com/js/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .menu { height: 100%; overflow-y: scroll; }
        .sidenav > li > a {
            padding: 10px 8px;
            font-size: 14px;
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
        .sidenav > li > a:hover > span { color: #FFF; }
        .sidenav > li > a > span { color: #4A515B; }
        .sidenav > li { margin-bottom: 4px; }
        .nav-item a { font-size: 12px; color: #4A515B; }
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
                        <span class="navbar-brand">模块：{{ api_data |length }} 个</span>
                        <span class="navbar-brand">接口：{{ api_count }} 个</span>
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
                            {{ mod }} 模块
                            <span class="pull-right"></span>
                        </a>
                        <ul id="{{ mod }}" class="nav collapse">
                            {%- if mod_data.common_request_param_list or mod_data.common_response_code_list %}
                            <li>
                                <a href="javascript:void(0)"  onclick="locateEle('{{ mod }}_common')">
                                    接口约定
                                </a>
                            </li>
                            <li>
                                <ul>
                                    {%- if mod_data.common_request_param_list %}
                                    <li class="nav-item">
                                        <a href="javascript:void(0)"  onclick="locateEle('{{ mod }}_common_request_param')">
                                            公共参数
                                        </a>
                                    </li>
                                    {% endif %}
                                    
                                    {%- if mod_data.common_response_code_list %}
                                    <li class="nav-item">
                                        <a href="javascript:void(0)"  onclick="locateEle('{{ mod }}_common_response_code')">
                                            返回码
                                        </a>
                                    </li>
                                    {% endif %}
                                </ul>
                            </li>
                            {%- endif %}
                            
                            {%- for group, api_list in mod_data.api_doc_data.items() %}
                            <li>
                                <a href="javascript:void(0)" onclick="locateEle('{{ mod }}_{{ group }}')">
                                    接口详情-{{ group }} 
                                </a>
                            </li>
                            <li>
                                <ul>
                                {%- for api in api_list %}
                                    <li class="nav-item">
                                        <a href="javascript:void(0)" onclick="locateEle('{{ mod }}_{{ group }}_{{ api['key'] }}')">
                                            {{ api['name'] }}
                                        </a>
                                    </li>
                                {%- endfor %}
                                </ul>
                            </li>
                            {%- endfor %}
                        </ul>
                    </li>
                    {%- endfor %}
                </ul>
            </div>
            <div class="col-md-10 pull-right">
                {%- for mod, mod_data in api_data.items() %}
                <h1> {{ mod }} 模块</h1>
                {%- if mod_data.common_request_param_list or mod_data.common_response_code_list %}
                <section>
                    <h2 id="{{ mod }}_common">{{ mod }} / 接口约定</h1>
                    {%- if mod_data.common_request_param_list %}
                    <article id="{{ mod }}_common_request_param">
                        <h3>公共参数</h3>
                        <table class="table table-bordered table-hover table-condensed">
                            <tr><th colspan="4">公共参数</th></tr>
                            <tr><th width="35%">字段</th><th width="8%">类型</th><th width="7%">必需</th><th width="50%">描述</th></tr>
                            {%- for field_name, field in mod_data.common_request_param_list.items() %}
                            <tr>
                                <td><strong>{{ field_name }}</strong></td>
                                <td>{{ field.type }}</td>
                                <td>{{ field.required }}</td>
                                <td>{{ field.desc }}</td>
                            </tr>
                            {%- endfor %}
                        </table>
                    </article>
                    {%- endif %}
                    
                    {%- if mod_data.common_response_code_list %}
                    <article id="{{ mod }}_common_response_code">
                        <h3>返回码</h3>
                        <table class="table table-bordered table-hover">
                            <tr>
                                <th>返回码</th>
                                <th>含义描述</th>
                            <tr>
                            {%- for err, code in mod_data.common_response_code_list.items() %}
                            <tr>
                                <td><strong>{{ code[0] }}</strong></td>
                                <td>{{ code[1] }}</td>
                            </tr>
                            {%- endfor %}
                        </table>
                    </article>
                    {%- endif %}
                </section>
                {%- endif %}
                
                <section>
                    {%- for group, api_list in mod_data.api_doc_data.items() %}
                    <h2 id="{{ mod }}_{{ group }}">{{ mod }} / {{ group }}</h1>
                    {%- for api in api_list %}
                    <article id="{{ mod }}_{{ group }}_{{ api['key'] }}" data-group="{{ mod }}" >
                        <h3>接口: {{ api['url'] }}</h3>
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
                            <p>请求示例：</p>
                            {% if api['input_example'] %}
                                <code>&nbsp;&nbsp;&nbsp;{{ api['input_example'] |safe }}</code>
                            {% else %}
                                <p>无</p>
                            {% endif %}
                            <p>返回示例：</p>
                            {% if api['output_example'] %}
                                <code>&nbsp;&nbsp;&nbsp;{{ api['output_example'] |safe }}</code>
                            {% else %}
                                <p>无</p>
                            {% endif %}
                        </div>
                    </article>
                    <hr>
                    {%- endfor %}
                    {%- endfor %}
                </section>
                {%- endfor %}
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


class ApiDoc(object):
    def __init__(self, app=None, blueprint_names=None, api_doc_url="/doc/"):
        """blueprint_names指定生成的蓝图名称列表，不指定时生成所有flask app下注册的接口"""
        self.api_doc_endpoint = "api_doc"
        self.api_doc_url = api_doc_url
        self.html = PAGE_HTML
        self.app = app
        if app is not None:
            self.init_app(app, blueprint_names)

    def init_app(self, app, blueprint_names):
        api_data = self.collect_api(blueprint_names)
        api_doc_func = partial(self.generate_doc, api_data=api_data)
        api_doc_endpoint = app.name + "_" + self.api_doc_endpoint
        app.add_url_rule(self.api_doc_url, view_func=api_doc_func, endpoint=api_doc_endpoint, methods=["GET"])

    def collect_api(self, blueprint_names):
        api_data = dict()
        api_mod = [self.app.blueprints.get(bp_name) for bp_name in blueprint_names] if blueprint_names else [self.app]
        for mod in api_mod:
            if not mod:
                continue
            common_request_param_list = getattr(mod, "COMMON_REQUEST_PARAM_LIST", dict())
            common_response_code_list = getattr(mod, "COMMON_RESPONSE_CODE_LIST", dict())
            view_functions = [(k, v) for k, v in self.app.view_functions.items() if blueprint_names is None or k.startswith(mod.name + ".")]
            api_data[mod.name] = {
                "view_functions": view_functions,
                "common_request_param_list": common_request_param_list,
                "common_response_code_list": common_response_code_list
            }
        return api_data

    def generate_doc(self, api_data=None):
        """生成接口文档"""
        api_data = api_data if api_data is not None else dict()

        re_ignore = re.compile(r"\s*#ignore_doc\s*")
        re_group = re.compile(r"\s*#group\s*(.*)\s*")  # 接口归属分组
        re_name = re.compile(r"\s*#name\s*(.*)\s*")  # 接口名称
        re_desc = re.compile(r"\s*#desc\s*(.*)\s*")  # 接口描述
        re_priv = re.compile(r"\s*#priv\s*(.*)\s*")  # 接口权限
        re_params = re.compile(r"\s*#param\s*(.*)\s*")  # 接口参数
        re_rets = re.compile(r"\s*#return\s*(.*)\s*")  # 接口返回值
        re_input_example = re.compile(r"(?<=#input_example)\s*(.*)?\s*(?=#output_example)", re.S | re.M)  # 接口输入示例
        re_output_example = re.compile(r"(?<=#output_example)\s*(.*)?\s*$", re.S | re.M)  # 接口返回示例（一直取到最后）
        re_params_field = re.compile(r"^([a-zA-Z0-9_\\.\-\[\]]+)\s*(?:<([^<>]*)>)?\s*(?:<([^<>]*)>)?\s*(.*)$")  # 参数字段内容分隔
        re_return_field = re.compile(r"^([a-zA-Z0-9_\\.\-\[\]]+)\s*(?:<([^<>]*)>)?\s*(.*)$")  # 返回值字段内容分隔
        em = re.compile(r"([a-zA-Z0-9_\[\]]+\.)")  # 多级字段匹配

        api_count = 0
        for data in api_data.values():
            api_doc_data = {}
            for endpoint, func in data.get("view_functions", []):
                if endpoint == "static":
                    continue

                doc = func.__doc__ or ""
                if re_ignore.findall(doc):
                    continue

                name = re_name.findall(doc) or [endpoint]
                desc = re_desc.findall(doc) or [""]
                priv = re_priv.findall(doc) or ["-"]
                group = re_group.findall(doc) or ["未分类"]
                params = re_params.findall(doc) or []
                rets = re_rets.findall(doc) or []
                input_example = re_input_example.findall(doc) or [""]
                output_example = re_output_example.findall(doc) or [""]

                params_data = []
                for p in params:
                    p_match = re_params_field.match(p)
                    if p_match:
                        p_name, p_type, p_option, p_desc = p_match.group(1, 2, 3, 4)
                        p_name = em.sub(r"<small><em>\1</em></small>", p_name)
                        params_data.append({"name": p_name, "type": p_type, "option": p_option if p_option else "必需", "desc": p_desc})

                return_data = []
                for r in rets:
                    r_match = re_return_field.match(r)
                    if r_match:
                        r_name, r_type, r_desc = r_match.group(1, 2, 3)
                        r_name = em.sub(r"<small><em>\1</em></small>", r_name)
                        return_data.append({"name": r_name, "type": r_type, "desc": r_desc})

                api_info = {
                    "key": endpoint.replace(".", "_"),
                    "name": name[0],
                    "url": url_for(endpoint),
                    "desc": desc[0],
                    "priv": priv[0],
                    "params": params_data,
                    "return": return_data,
                    "input_example": input_example[0].replace("\n", "<br>").replace(" ", "&nbsp;"),
                    "output_example": output_example[0].replace("\n", "<br>").replace(" ", "&nbsp;")
                }
                api_count += 1
                api_doc_data.setdefault(group[0], []).append(api_info)
            data["api_doc_data"] = api_doc_data
        return render_template_string(self.html, api_data=api_data, api_count=api_count)
