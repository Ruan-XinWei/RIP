import threading
import time

from flask import Flask, render_template, redirect

from config import addLog
from config import getConfig, updateConfig
from forms import *
from rip import rip, init
from route import getAllRoutes, getNetName, addLink, removeLink, addNet

app = Flask(__name__)
app.secret_key = 'secret string'
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

lock = threading.Lock()
lock_run = threading.Lock()
state = '正在运行...'


def updateChoices(last_choices, new_data, is_add):
    """
    更新选项信息

    :param last_choices: 旧数据
    :param new_data: 新数据
    :param is_add: True为添加，False为删除
    :return:
    """
    if is_add:
        return sorted(last_choices + [(key, key) for key in new_data])
    else:
        return sorted(list(set(last_choices) - set([(key, key) for key in new_data])))


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/showRoute', methods=['GET', 'POST'])
def showRoute():
    show_form = ShowRoute()
    all_routes = getAllRoutes()
    show_form.route.choices = [data for data in all_routes]
    return render_template('showRoute.html', form=show_form)


@app.route('/change', methods=['GET', 'POST'])
def change():
    net_exit_form = NetExitForm()
    net_recover_form = NetRecoverForm()
    route_exit_form = RouteExitFrom()
    route_recover_form = RouteRecoverFrom()
    add_link_form = AddLinkFrom()
    remove_link_form = RemoveLinkFrom()
    net_add_form = NetAddFrom()
    set_form = SetForm()

    global state

    net_exit_form.net_list.choices = [(key, key) for key in sorted(set(getNetName()) - set(getConfig()['网络故障']))]
    net_recover_form.net_list.choices = [(key, key) for key in sorted(getConfig()['网络故障'])]
    route_exit_form.route_list.choices = [(key, key) for key in sorted(set(getAllRoutes()) - set(getConfig()['路由器故障']))]
    route_recover_form.route_list.choices = [(key, key) for key in sorted(getConfig()['路由器故障'])]

    all_routes = getAllRoutes()
    all_net = getNetName()
    add_link_form.route.choices = [data for data in all_routes]
    add_link_form.net.choices = [data for data in all_net]
    remove_link_form.route.choices = [data for data in all_routes]
    remove_link_form.net.choices = [data for data in all_net]

    if net_exit_form.net_exit_submit.data and net_exit_form.validate():
        net_recover_form.net_list.choices = updateChoices(net_recover_form.net_list.choices,
                                                          net_exit_form.net_list.data, True)
        net_exit_form.net_list.choices = updateChoices(net_exit_form.net_list.choices, net_exit_form.net_list.data,
                                                       False)
        UpdateThread(0, '网络故障', net_recover_form.net_list.choices).start()

    if net_recover_form.net_recover_submit.data and net_recover_form.validate():
        net_exit_form.net_list.choices = updateChoices(net_exit_form.net_list.choices, net_recover_form.net_list.data,
                                                       True)
        net_recover_form.net_list.choices = updateChoices(net_recover_form.net_list.choices,
                                                          net_recover_form.net_list.data, False)
        UpdateThread(0, '网络故障', net_recover_form.net_list.choices).start()

    if route_exit_form.route_exit_submit.data and route_exit_form.validate():
        route_recover_form.route_list.choices = updateChoices(route_recover_form.route_list.choices,
                                                              route_exit_form.route_list.data, True)
        route_exit_form.route_list.choices = updateChoices(route_exit_form.route_list.choices,
                                                           route_exit_form.route_list.data, False)
        UpdateThread(0, '路由器故障', route_recover_form.route_list.choices).start()
        # return redirect('change')

    if route_recover_form.route_recover_submit.data and route_recover_form.validate():
        route_exit_form.route_list.choices = updateChoices(route_exit_form.route_list.choices,
                                                           route_recover_form.route_list.data, True)
        route_recover_form.route_list.choices = updateChoices(route_recover_form.route_list.choices,
                                                              route_recover_form.route_list.data, False)
        UpdateThread(0, '路由器故障', route_recover_form.route_list.choices).start()

    if add_link_form.add_link_submit.data and add_link_form.validate():
        # addLink(add_link_form.route.data, add_link_form.net.data)
        UpdateThread(1, add_link_form.route.data, add_link_form.net.data).start()
        # return redirect('change')

    if remove_link_form.remove_link_submit.data and remove_link_form.validate():
        # removeLink(remove_link_form.route.data, remove_link_form.net.data)
        UpdateThread(2, remove_link_form.route.data, remove_link_form.net.data).start()
        # return redirect('change')

    if net_add_form.net_add_submit.data and net_add_form.validate():
        # print(net_add_form.net_name.data, net_add_form.net_address.data)
        net_exit_form.net_list.choices = sorted(
            net_exit_form.net_list.choices + [(net_add_form.net_name.data, net_add_form.net_name.data)])
        add_link_form.net.choices = sorted(add_link_form.net.choices + [net_add_form.net_name.data])
        remove_link_form.net.choices = sorted(remove_link_form.net.choices + [net_add_form.net_name.data])
        UpdateThread(3, net_add_form.net_name.data, net_add_form.net_address.data).start()

    if (set_form.start.data or set_form.end.data) and set_form.validate():
        if set_form.start.data:
            addLog('准备开始', 'success')
            lock_run.release()
            addLog('开始成功', 'success')
            state = '正在运行...'
        else:
            print('准备暂停')
            addLog('准备暂停', 'success')
            lock_run.acquire()
            print('暂停成功')
            addLog('暂停成功', 'success')
            state = '暂停中...'

    return render_template('change.html',
                           net_exit_form=net_exit_form,
                           net_recover_form=net_recover_form,
                           route_recover_form=route_recover_form,
                           route_exit_form=route_exit_form,
                           add_link_form=add_link_form,
                           remove_link_form=remove_link_form,
                           net_add_form=net_add_form,
                           set_form=set_form,
                           state=state)


@app.errorhandler(500)
def error_handler_500(e):
    addLog(e, 'danger')
    return redirect('change')


@app.errorhandler(404)
def error_handler_404(e):
    init(init_log=True)
    addLog(e, 'danger')
    return redirect('main')


class RunThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self) -> None:
        init(init_route_table=True, init_log=True, init_config=True)
        while True:
            try:
                rip(10, lock, lock_run)
            except Exception as e:
                print(e)


class UpdateThread(threading.Thread):
    def __init__(self, choice, first='', second=''):
        """
        :param choice: 0-更新配置文件，1-添加线路，2-移除线路，3-添加新网络
        :param first: 第一个参数
        :param second: 第二个参数
        """
        threading.Thread.__init__(self)
        self.choice = choice
        self.first = first
        self.second = second
        self.now = time.ctime()

    def run(self) -> None:
        print('准备运行 UpdateThread', self.name)
        lock.acquire()
        print('运行成功 UpdateThread', self.name)
        if self.choice == 0:
            self.second = [data[0] for data in self.second]
            updateConfig(self.first, self.second)
            addLog('{}, {}'.format(self.first, self.second), 'success')
        elif self.choice == 1:
            addLink(self.first, self.second)
        elif self.choice == 2:
            removeLink(self.first, self.second)
        elif self.choice == 3:
            addNet(self.first, self.second)
        else:
            print('选择错误')
        print('准备结束 UpdateThread')
        lock.release()
        print('结束成功 UpdateThread')


RunThread().start()
