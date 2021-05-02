from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import InputRequired


class ShowRoute(FlaskForm):
    route = SelectField('路由器名称', validators=[InputRequired()])  # , render_kw={'disabled':'true'}
    all = BooleanField('获取全部路由表', render_kw={'onclick': 'select_all()'})
    submit = SubmitField('提交', render_kw={'type': 'button', 'onclick': 'load_json()'})


class NetExitForm(FlaskForm):
    net_list = SelectMultipleField()
    net_exit_submit = SubmitField('提交')


class NetRecoverForm(FlaskForm):
    net_list = SelectMultipleField()
    net_recover_submit = SubmitField('提交')


class NetAddFrom(FlaskForm):
    net_name = StringField('网络名称')
    net_address = StringField('网络地址')
    net_add_submit = SubmitField('添加')


class RouteExitFrom(FlaskForm):
    route_list = SelectMultipleField()
    route_exit_submit = SubmitField('提交', render_kw={'data-toggle': "modal", 'data-target': "#route_exit_submit"})


class RouteRecoverFrom(FlaskForm):
    route_list = SelectMultipleField()
    route_recover_submit = SubmitField('提交')


class AddLinkFrom(FlaskForm):
    route = SelectField('路由器')
    net = SelectField('网络')
    add_link_submit = SubmitField('添加')


class RemoveLinkFrom(FlaskForm):
    route = SelectField('路由器')
    net = SelectField('网络')
    remove_link_submit = SubmitField('删除')


class SetForm(FlaskForm):
    state = StringField('运行状态')
    start = SubmitField('开始')
    end = SubmitField('暂停')
