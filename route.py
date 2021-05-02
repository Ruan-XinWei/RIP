# -*- coding: utf-8 -*-
import json
import os
import sys
import time

from config import getConfig, addLog

# 缓存目录路径
cache_path = os.path.join(sys.path[0], 'static', 'cache')
# 所有路由表
routes_path = os.path.join(sys.path[0], 'static', 'data', 'routes.json')
# 数据文件夹
dir_data_path = os.path.join(sys.path[0], 'static', 'data')


def getAllData():
    # 网络所有信息
    with open(os.path.join(sys.path[0], 'static', 'data', 'data.json'), mode='r', encoding='utf-8') as f_all:
        return json.loads(f_all.read())


def getAllRoutes():
    """
    获取所有路由器名称
    :return: list
    """
    name = []
    with open(routes_path, mode='r', encoding='utf-8') as f:
        for key in json.loads(f.read()):
            name.append(key)
    return name


def getName():
    """
    获取网络中路由器和网络的名称
    例如：['路由器1', '网络1', '路由器3', '路由器4']
    :return: list
    """
    names = []
    for name in getAllData()['data']:
        names.append(name['name'])
    return names


def getNetName():
    """
    获取所有网络
    例如：['网络1', '网络2', '网络6', '网络4', '网络5', '网络3']

    :return: list
    """
    return sorted(list(set(getName()) - set(getAllRoutes())))


def getMap():
    """
    获取网络拓扑图
    例如：{'路由器1': {'网络1', '路由器3'}, '网络1': {'路由器3', '路由器1', '路由器4'}, '路由器3': {'网络1', '路由器1'}, '路由器4': {'网络1'}}
    :return: dict
    """
    routes_map = {}
    for name in getName():
        routes_map[name] = set()
    # print(routes_map)
    for edge in getAllData()['edges']:
        # 将线两头的网络和路由器都加入拓扑图中
        routes_map[getAllData()['data'][edge['source']]['name']].add(getAllData()['data'][edge['target']]['name'])
        routes_map[getAllData()['data'][edge['target']]['name']].add(getAllData()['data'][edge['source']]['name'])
    # print(routes_map)
    return routes_map


def getNowRoutes():
    """
    获取现在整个路由表
    :return: json
    """
    with open(routes_path, mode='r', encoding='utf-8') as f:
        return json.loads(f.read())


def getIndex(name):
    """
    获取 路由器 或 网络 的 id
    :param name:
    :return:
    """
    for data in getAllData()['data']:
        if data['name'] == name:
            return data['id']


def addLink(route, net):
    """
    给 路由器route 和 网络net 进行连接
    :param route: 路由器名
    :param net: 网络名
    :return:
    """
    if route in getAllRoutes() and net in getNetName():
        data = getAllData()
        for edge in data['edges']:
            if edge["source"] == getIndex(route) and edge["target"] == getIndex(net):
                addLog('已经存在 {}->{} 的路径'.format(route, net), 'info')
                return
        data['edges'].append({
            "source": getIndex(route),
            "target": getIndex(net)
        })
        addLog('添加成功 {}->{}'.format(route, net), 'success')
        with open(os.path.join(dir_data_path, 'data.json'), mode='w', encoding='utf-8') as f:
            f.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '),
                               ensure_ascii=False))
    else:
        addLog('添加失败 {} 或者 {} 不存在'.format(route, net), 'warning')


def removeLink(route, net):
    """
    给 路由器route 和 网络net 进行连接
    :param route: 路由器名
    :param net: 网络名
    :return:
    """
    if route in getAllRoutes() and net in getNetName():
        data = getAllData()
        flag = False
        for i in range(len(data['edges'])):
            edge = data['edges'][i]
            if edge["source"] == getIndex(route) and edge["target"] == getIndex(net):
                data['edges'].remove(data['edges'][i])
                print(i)
                flag = True
                break
        if flag:
            with open(os.path.join(dir_data_path, 'data.json'), mode='w', encoding='utf-8') as f:
                f.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '),
                                   ensure_ascii=False))
            addLog('删除成功 {}->{}'.format(route, net), 'success')
        else:
            addLog('不存在 {}->{} 的路径'.format(route, net), 'info')
    else:
        addLog('删除失败 {} 或者 {} 不存在'.format(route, net), 'warning')


def addNet(net_name, net_address):
    with open(os.path.join(dir_data_path, 'data.json'), mode='r', encoding='utf-8') as f:
        data = json.loads(f.read())
        if net_name not in getNetName():
            data['data'].append({
                "category": 1,
                "id": len(data['data']),
                "name": net_name,
                "value": net_address
            })
            print(data)
            with open(os.path.join(dir_data_path, 'data.json'), mode='w', encoding='utf-8') as fw:
                fw.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '),
                                    ensure_ascii=False))
            addLog('添加新网络成功，{}, {}'.format(net_name, net_address), 'success')
        else:
            addLog('{} 已经存在，添加失败'.format(net_name), 'warning')


def checkRouteName(name):
    """
    检查是否是路由器名
    :param name: 路由器或网络名
    :return: True为路由器名，False为网络名
    """
    for data in getAllData()['data']:
        if data['name'] == name:
            if data['category'] == 0:
                return True
            else:
                return False


def initRoutes():
    """
    初始化路由表
    :return: bool
    """
    routes = {}
    names = getName()
    for name in names:
        if checkRouteName(name):
            routes[name] = []
    for route in routes:
        for next_name in getMap()[route]:
            routes[route].append({
                "下一跳路由器": "*",
                "目的网络": next_name,
                "距离": 16 if next_name in getConfig()['网络故障'] else 1
            })
    with open(os.path.join(sys.path[0], 'static', 'data', 'routes.json'), mode='w', encoding='utf-8') as f:
        f.write(json.dumps(routes, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False))
    # print('初始化路由表成功')


def checkDir(dir_path, make=True):
    """
    检查文件夹是否存在
    :param make: bool，默认为True，如果为True，文件夹不存在则创建一个文件夹
    :param dir_path: 文件夹路径
    :return: bool，是否存在
    """
    if os.path.exists(dir_path):
        # print('{} 存在'.format(dir_path))
        return True
    elif make:
        # print('{} 不存在'.format(dir_path))
        os.mkdir(dir_path)
        # print('{} 创建成功'.format(dir_path))
        return True
    else:
        # print('{} 不存在，并且没有创建'.format(dir_path))
        return False


class Route:
    def __init__(self, name=""):
        if name == "":
            name = "默认路由器"
        self.name = name
        # 创建路由器cache
        if os.path.exists(os.path.join(cache_path, self.name)):
            pass
            # print('已经存在 {}'.format(self.name))
        else:
            # print('不存在 {}，正在创建...'.format(os.path.join(cache_path, self.name)))
            os.mkdir(os.path.join(cache_path, self.name))
            # print('创建成功 {}'.format(self.name))

    def getRoutes(self):
        """
        获取自己的路由表，返回列表格式
        :return: 列表
        """
        with open(routes_path, mode='r', encoding='utf-8') as f:
            return json.loads(f.read())[self.name]

    def getDistanceToNet(self, net):
        """
        获取在当前路由表中，到net的距离，如果不存在net，则返回16
        :param net: 网络名称
        :return: int，距离
        """
        for i in range(len(self.getRoutes())):
            if self.getRoutes()[i]['目的网络'] == net:
                return self.getRoutes()[i]['距离']
        return 16

    def sendRoutes(self, nextRoutes):
        """
        发送当前路由表给相邻路由器，将路由表存入对应路由器缓存中

        :param nextRoutes: list，所有相邻路由器
        :return: 是否全部发送成功
        """
        flag = True
        for nextRoute in nextRoutes:
            filename = ""
            if checkDir(os.path.join(cache_path, nextRoute)):
                now_time = time.strftime("%Y_%m_%d_%H_%M_%S")
                with open(os.path.join(cache_path, nextRoute, '{}_{}.json'.format(now_time, self.name)), mode='w',
                          encoding='utf-8') as f:
                    filename = f.name
                    f.write(json.dumps(self.getRoutes(), sort_keys=True, indent=4, separators=(',', ': '),
                                       ensure_ascii=False))
                    # print('{}->{}，发送成功 {}'.format(self.name, nextRoute, filename[filename.rfind('\\') + 1:]))
            else:
                print('{}->{}，发送失败 {}'.format(self.name, nextRoute, filename[filename.rfind('\\'):]))
                flag = False
        return flag

    def updateRoute(self, routes):
        """
        更新路由表

        :param routes: 新路由表信息
        :return:
        """
        with open(routes_path, mode='r', encoding='utf-8') as f:
            data = json.loads(f.read())
            data[self.name] = routes
            # print(data)
            with open(routes_path, mode='w', encoding='utf-8') as f_write:
                f_write.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '),
                                         ensure_ascii=False))
                return True
        return False

    def findNextRoute(self, name):
        """
        查找本路由表中下一跳路由 == name 的 列表序号
        :param name: 下一跳路由器
        :return: list
        """
        result = []
        for i in range(len(self.getRoutes())):
            if self.getRoutes()[i]['下一跳路由器'] == name:
                result.append(i)
        return result

    def setToNetDistance(self, net, distance):
        """
        设置 此路由器 到 net 的 距离 为 distance

        :param net: 网络名
        :param distance: 距离
        :return:
        """
        route_table = self.getRoutes()
        for value in route_table:
            if value['目的网络'] == net:
                value['距离'] = distance
        self.updateRoute(route_table)

    def updateErrorNet(self, net, distance):
        """
        更新有关 路由器错误 情况（仅当路由器是邻接路由的时候）

        :param net: 网络名称
        :param distance: 距离
        :return:
        """
        flag = False
        route_table = self.getRoutes()
        for value in route_table:
            if value['目的网络'] == net:
                value['下一跳路由器'] = '*'
                value['距离'] = distance
                flag = True
                break
        if not flag:
            route_table.append({
                "下一跳路由器": "*",
                "目的网络": net,
                "距离": distance
            })
        self.updateRoute(route_table)

# Route('路由器A').sendRoutes(['路由器B', '路由器C', '路由器D'])
