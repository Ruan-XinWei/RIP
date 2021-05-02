import json
import os
import sys

# 自定义配置文件路径
import time

config_path = os.path.join(sys.path[0], 'static', 'config', 'config.json')
# log 文件路径
log_path = os.path.join(sys.path[0], 'static', 'data', 'log.json')


def getConfig():
    """
    获取配置文件
    :return: dict，例如{'网络加入': [], '网络故障': ['网络2'], '路由器故障': []}
    """
    with open(config_path, mode='r', encoding='utf-8') as f:
        return json.loads(f.read())


def updateConfig(name, data):
    """
    更新 name 的配置表

    :param data: 新数据
    :param name: 配置名
    :return:
    """

    with open(config_path, mode='r', encoding='utf-8') as fr:
        tmp = json.loads(fr.read())
        tmp[name] = data
        print(tmp)
        with open(config_path, mode='w', encoding='utf-8') as fw:
            fw.write(json.dumps(tmp, sort_keys=True, indent=4, separators=(',', ': '),
                                ensure_ascii=False))
            # pass


def addLog(info, grade):
    """
    添加Log文件

    :param info: 信息
    :param grade: 等级
        .active	鼠标悬停在行或单元格上时所设置的颜色
        .success	标识成功或积极的动作
        .info	标识普通的提示信息或动作
        .warning	标识警告或需要用户注意
        .danger	标识危险或潜在的带来负面影响的动作
    :return:
    """
    with open(log_path, mode='r', encoding='utf-8') as fr:
        data = json.loads(fr.read())
        data.append({
            "time": time.ctime(),
            "info": info,
            "grade": grade
        })
        if len(data) > 50:
            data.remove(data[0])
        with open(log_path, mode='w', encoding='utf-8') as fw:
            fw.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '),
                                ensure_ascii=False))


if __name__ == '__main__':
    # addLog('test', 'info')
    pass
