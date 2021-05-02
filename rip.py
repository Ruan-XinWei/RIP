import json
import os
import sys
import threading
import time
import datetime
from threading import Thread
from route import Route
from route import getAllRoutes, getMap, initRoutes
from route import dir_data_path, cache_path
from config import config_path, getConfig, addLog

# 间隔时间
TIME = 5
# 超过此时间（分钟），没有收到其他相邻路由器的信息，则将已有的路由信息距离设为16
MAX_INTERVAL_TIME = 1
# 不能找到
NOTFOUND = -1
# 路由器更新时间
route_update_time = os.path.join(dir_data_path, 'route_update_time.json')


def getFileTime(filename):
    """
    获取指定格式文件名的时间戳

    :param filename: 指定格式的文件名：如2021_03_08_22_41_10_路由器A.json
    :return: str，时间戳，如2021_03_08_22_41_10
    """
    return filename[:filename.rfind('_')]


def getFileName(filename):
    """
    获取指定格式文件名的路由器名

    :param filename: 指定格式的文件名：如2021_03_08_22_41_10_路由器A.json
    :return: str，路由器名，如路由器A
    """
    return os.path.splitext(filename)[0][filename.rfind('_') + 1:]


def getCache(route, name):
    """
    获取文件名为name的Cache

    :param route: 路由器名
    :param name: cache文件名
    :return: list，如[{'下一跳路由器': '*', '目的网络': '网络3', '距离': 1}, ...]
    """
    with open(os.path.join(cache_path, route, name), mode='r', encoding='utf-8') as f:
        return json.loads(f.read())


def getUpdateTime():
    """
    获取 路由表相邻路由表更新时间

    例如：{'初始化时间': '2021_03_09_10_56_43', '路由器A': {'路由器B': '2021_03_09_10_56_43', ...

    :return: dict
    """
    with open(route_update_time, mode='r', encoding='utf-8') as f:
        return json.loads(f.read())


def checkNetName(route_table, net_name):
    """
    检查在路由表中是否有net_name的目的网络

    :param net_name: 目的网络
    :param route_table: 路由表
    :return: int，路由表中的序号，-1代表没有找到，其他则是找到了
    """
    for i in range(len(route_table)):
        data = route_table[i]
        if data['目的网络'] == net_name:
            return i
    return NOTFOUND


def checkTime(old_time, new_time, minute_time):
    """
    检查时间是否满足要求

    例如：checkTime('2021_03_09_10_51_41', '2021_03_09_10_56_42', 3) = False

    :param minute_time: int, 相差的时间（按分钟算）
    :param old_time: str, 旧时间
    :param new_time: str, 新时间
    :return: bool，True表示满足要求
    """
    old_time = datetime.datetime.strptime(old_time, "%Y_%m_%d_%H_%M_%S")
    new_time = datetime.datetime.strptime(new_time, "%Y_%m_%d_%H_%M_%S")
    return (new_time - old_time) <= datetime.timedelta(minutes=minute_time)


def updateCache(name):
    """
    通过cache更新路由表

    :param name: 路由器名
    :return:
    """
    now_time = time.strftime("%Y_%m_%d_%H_%M_%S")
    # print('now_time:', now_time)
    route = Route(name)
    # print('正在处理 {}...'.format(name))
    now_route_table = route.getRoutes()
    # print("此时路由表", now_route_table)
    for root, dirs, files in os.walk(os.path.join(cache_path, name)):
        for file in files:
            if getFileTime(file) <= now_time:
                cache = getCache(name, file)
                # 更新下一跳路由器，并且距离+1
                for data in cache:
                    data['下一跳路由器'] = getFileName(file)
                    if data['距离'] < 16:
                        data['距离'] += 1
                    else:
                        data['距离'] = 16

                # 更新 路由器收到相邻路由的时间
                update_time = getUpdateTime()
                update_time[name][getFileName(file)] = now_time
                with open(route_update_time, mode='w', encoding='utf-8') as f:
                    f.write(json.dumps(update_time, sort_keys=True, indent=4, separators=(',', ': '),
                                       ensure_ascii=False))

                # print(cache)
                # 遍历新cache
                for data in cache:
                    # 查找 路由表中的目的网络 == data['目的网络'] 的位置
                    index = checkNetName(now_route_table, data['目的网络'])
                    # 如果没有找到，则将这条记录加到路由表中
                    if index == NOTFOUND:
                        # print('添加: ', data)
                        now_route_table.append(data)
                        addLog('{} <strong>添加</strong> {}'.format(name, data), 'active')
                    # 如果找到了，则看是否下一跳路由器 是否就是 发来的路由器
                    elif now_route_table[index]['下一跳路由器'] == getFileName(file):  # 是路由器发来的新记录
                        # print("替换新路由：", now_route_table[index], data)
                        now_route_table[index] = data
                        # addLog('{} <strong>获得</strong> {} 的新路由表 {}'.format(name, getFileName(file), data), 'active')
                    # 如果 下一跳路由器 是 其他路由器，则比较是否是最短路径
                    elif now_route_table[index]['距离'] > data['距离']:  # 新发来的更短
                        # print("更新距离：", now_route_table[index], data)
                        now_route_table[index] = data
                        addLog('{} <strong>更新距离</strong> {}'.format(name, data), 'active')
                    else:  # 新发来的更长，不更新
                        # print('没更新')
                        pass
                    time.sleep(0.1)
            os.remove(os.path.join(root, file))
            # print('删除 {}'.format(file))
    # print(now_route_table)
    route.updateRoute(now_route_table)


def checkErrorRoute(name, now_time, minute_time):
    """
    检查 此路由器的相邻路由器中是否有故障路由器（超时未更新）

    :param now_time: 处理此时间之前
    :param minute_time: 设置间隔时间
    :param name: 路由器名
    :return:
    """
    update_time = getUpdateTime()
    # 依次获取该路由器下的各个路由器
    for dict_key in update_time[name]:
        # 如果不是初始化时间，则说明之前接受过
        if '*' != update_time[name][dict_key]:
            # 如果已经超过规定时间
            if not checkTime(update_time[name][dict_key], now_time, minute_time):
                # 更改路由表
                route = Route(name)
                route_table = route.getRoutes()
                for index in route.findNextRoute(dict_key):
                    route_table[index]['距离'] = 16
                route.updateRoute(route_table)
                addLog('{} 超过 {} 分钟 未再次收到 {} 的路由表，将其设为不可达'.format(name, minute_time, dict_key), 'danger')


def rip(sleep_time, lock, lock_run):
    """
    RIP协议
    """
    print('rip 准备开始')
    lock.acquire()
    lock_run.acquire()
    print('rip 开始成功')
    # 所有路由器名称
    routes = getAllRoutes()
    # 网络拓扑图
    routes_map = getMap()

    for route_name in routes:
        if route_name in getConfig()['路由器故障']:
            continue
        route = Route(route_name)
        # 搜索 此路由器 的邻接网络
        for net in routes_map[route_name]:
            # print(route_name, net)
            # 如果自定义网络故障，则continue
            if net in getConfig()['网络故障']:
                route.updateErrorNet(net, 16)
                addLog('{} 发现 {} 故障'.format(route_name, net), 'danger')
                continue
            else:
                route.updateErrorNet(net, 1)
            # 如果不能到达net，则不能通过net转发
            if route.getDistanceToNet(net) == 16:
                continue
            # 如果没有故障，则恢复相邻网络的连接

            for next_route in routes_map[net]:
                # 如果下一跳不是本路由器，并且通过该网络能够到达下一个路由器，则转发
                if route_name != next_route and Route(next_route).getDistanceToNet(net) != 16:
                    if route in getConfig()['路由器故障']:
                        pass
                    else:
                        route.sendRoutes([next_route])
                        # print('{}->{}->{}'.format(route.name, net, next_route))
        # print('{}发送完毕'.format(route_name))
    # 更新缓存
    for route_name in routes:
        updateCache(route_name)
    # 检查故障路由器
    now_time = time.strftime("%Y_%m_%d_%H_%M_%S")
    for route_name in routes:
        checkErrorRoute(route_name, now_time, MAX_INTERVAL_TIME)
    print('rip 准备结束')
    lock.release()
    lock_run.release()
    print('rip 结束成功')
    time.sleep(sleep_time)


def init(init_data=False, init_cache=False, init_route_table=False, init_config=False, init_log=False,
         init_update_time=True):
    """
    初始化

    :param init_log: bool，初始化日志
    :param init_data: bool，初始化数据
    :param init_update_time: bool，初始化路由器对于指定路由的更新时间
    :param init_cache: bool，bool，初始化创建cache文件夹
    :param init_route_table: bool，初始化路由表
    :param init_config: bool，初始化创建配置文件
    :return:
    """
    # 初始化日志文件
    if init_log:
        with open(os.path.join(dir_data_path, 'log.json'), mode='w', encoding='utf-8') as f:
            f.write(json.dumps([], sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False))
        addLog('初始化 日志文件 成功', 'success')
    # 初始化数据
    if init_data:
        with open(os.path.join(dir_data_path, 'init_data.json'), mode='r', encoding='utf-8') as f:
            data = json.loads(f.read())
            with open(os.path.join(dir_data_path, 'data.json'), mode='w', encoding='utf-8') as fw:
                fw.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '),
                                    ensure_ascii=False))
    # 初始化创建配置文件
    if init_config:
        with open(config_path, mode='w', encoding='utf-8') as f:
            config = {
                "网络故障": [],
                "路由器故障": [],
                "网络加入": [],
                "线路故障": []
            }
            f.write(json.dumps(config, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False))
    # 初始化创建cache文件夹
    if init_cache:
        routes = getAllRoutes()
        for route_name in routes:
            Route(route_name)
    # 初始化路由表
    if init_route_table:
        initRoutes()
        addLog('初始化 路由表 成功', 'success')
    # 初始化更新时间
    if init_update_time:
        with open(route_update_time, mode='w', encoding='utf-8') as f:
            update_time = {}
            # init_time = time.strftime("%Y_%m_%d_%H_%M_%S")
            init_time = '*'
            routes = getAllRoutes()
            for route_i in routes:
                update_time[route_i] = {}
            for route_i in routes:
                for route_j in routes:
                    if route_i != route_j:
                        # update_time[route_i].append(time_dict)
                        update_time[route_i][route_j] = init_time
            # update_time['初始化时间'] = init_time
            f.write(json.dumps(update_time, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False))
    print('初始化成功')


if __name__ == '__main__':
    init(init_data=True, init_route_table=True)
    # while True:
    #     rip(1)
