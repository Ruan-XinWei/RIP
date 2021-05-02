# 需求分析

## 主要算法需求

a.  初始化

    i.  能够自定义初始化网络拓扑结构。
    
    ii. 能够初始化所有路由器的路由表。

b.  路由器

    i.  根据新接受到的路由表，通过距离向量算法，定时更新自己的路由表。
    
    ii. 定时发送自己的路由表给相邻路由器。
    
    iii. 能够及时发现邻接网络的问题，比如正常网络发生故障，故障网络恢复正常。
    
    iv. 检测其他路由器故障，比如曾经接收过某路由器的路由表信息，在一定时间后一直未更新，则将其设为不可达。

c.  配置文件

    i.  能够在运行过程中，更改网络拓扑结构。
    
    ii. 能够在运行过程中，设置网络或者路由器故障、网络或者路由器恢复以及新添加网络。
    
    iii. 能够自定义路由器发送时间、相邻路由器在自定义时间没更新设为不可达。

d.  其他

    i.  能够通过界面控制RIP算法的运行和暂停。
    
    ii. 能够记录每个操作，以及路由表更改情况

## 主要界面展示

a)  动态显示网络拓扑图以及网络拓扑图中的信息

b)  及时显示指定路由器的路由表或所有路由器的路由表。

c)  能够展示基本操作，如设置路由器故障、路由器恢复、设置网络退出、网络恢复、网络加入、添加线路、删除线路和简单设置配置文件

d)  能够动态展示状态信息以及此时所有的路由表信息

# 概要设计

## 系统概要描述

系统的主要部分在于路由器，因为每个路由器都是相同的结构和操作，所以将路由器写成一个类。对于路由器的设计，主要包括路由器缓存和路由器发送路由表、更新路由表等操作。缓存部分，在系统中采用的是使用文件夹的形式来模拟，如路由器A就有一个路由器A的文件夹，用来模拟缓存；操作部分，则都是使用各种编写的函数来进行操作。

系统的主要算法是RIP距离向量算法，因为需要在前端界面能够及时的获取到各种数据，因此，本系统主要有两个线程，一个主线程和一个子线程，使用子线程通过while来运行RIP算法，这样也使得在前端准备暂停RIP算法的时候，只需要通过获取或者释放RIP运行锁，就能够运行或者暂停RIP算法。

系统在存储结构方面，主要使用的是json文件，部分存储格式如下：

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502214035.png" alt="image-20210502212453511" style="display:inline; float:left; width=20px;" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502214055.png" alt="image-20210502212507943" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502214114.png" alt="image-20210502212514818" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215142.png" alt="image-20210502212522008" style="display:inline; float:left" />

系统的Web框架使用的是Flask，将前后端很好地分离的同时，也简化了很多代码编写的工作。

系统的前端框架使用的是Bootstrap，满足响应式布局，展示效果也比较好。

系统展示网络拓扑结构图使用的是ECharts，能够直观形象地将网络拓扑图显示出来

## 初始化算法

a.  自定义初始化网络拓扑结构

    1.  在运行前检查是否设置初始化网络拓扑结构要求；
    
    2.  如果设置了初始化网络拓扑，则读取初始化网络拓扑结构的文件，否则不进行初始化；
    
    3.  读取成功后，将其写入程序需要运行的文件中。

b.  初始化所有路由器的路由表

    1.  获取网络拓扑中的所有路由器；
    
    2.  通过网络拓扑，将所有路由器的邻接网络设置为直连，即距离为1，无下一跳路由器，目的网络设为对应的邻接网络。
    
    3.  写入路由表文件中。

## 路由器主要算法

a)  通过距离向量算法，定时更新

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215143.png" alt="img" style="display:inline; float:left" />

b)  发送自己的路由表给相邻路由器。

    1.  获取邻接网络，排除发生故障的网络（包括自定义故障，以及不可达）
    
    2.  通过正常的邻接网络发送到邻接网络的下一个路由器；

c)  及时发现邻接网络的问题，比如正常网络发生故障，故障网络恢复正常。

    1.  在发送路由表的时候，获取此时的网络拓扑图；
    
    2.  扫描该路由器所有的邻接网络；
    
    3.  比较现在的路由表和现在的网络情况，如果现在的路由表到邻接网络的距离为1，但是现在的网络情况是不能够直达邻接网络，则说明该网络发送了故障，反之则是故障网络恢复正常，则及时更新路由表。

d)  检测其他路由器故障，比如曾经接收过某路由器的路由表信息，在一定时间后一直未更新，则将其设为不可达。

    1.  设置一个更新文件，记录路由器获得其他路由器发送过来的路由表信息的时间；
    
    2.  获取自定义的最长间隔时间；
    
    3.  如果此时与上次获取路由表信息的时间超过最长间隔时间，则更新路由表，将其设置为不可达。

## 配置文件主要算法

在运行过程中，对网络拓扑结构进行各种更改操作的原理大致相同，这里将以添加网络为例，进行算法描述。

1.  在界面上通过JavaScript随机获取一个网络，主要通过 Math.random() 随机产生数字，然后网络名通过汉字编码将数字转换成汉字，网络地址则可以直接使用随机产生的数字。

2.  通过提交表单的方式，提交到后台，后台根据数据，通过获取写锁，检查此时是否正在使用此配置文件，如果写锁获取成功，则将该配置文件更新。

3.  前端再通过Ajax异步加载，显示出此操作过程。

## 其他算法

a)  界面控制RIP算法的运行和暂停

因为该系统使用了一个线程在后台来专门执行RIP算法，并且RIP算法在每次运行前都会获取RIP的运行锁，在运行后就会释放RIP的运行锁，然后再Sleep，所以后台RIP算法的运行和暂停通过锁的方式来控制后台RIP算法的运行和暂停，主要算法流程如下：

1.  前端通过按钮向后台发起运行或暂停的命令

2.  后台获取到该命令，就获取RIP的运行锁

3.  等到获取成功后，RIP就暂停，此时通过Ajax异步加载，将此操作返回给前端显示。

b)  能够记录每个操作，以及路由表更改情况

本功能通过一个json文件来记录其操作，编写一个更新函数，在每次需要记录的时候就进行调用，并且在记录过多的时候，就开始覆盖之前的最久远数据，记录主要有五种级别，分别是active，success，info，warning，danger，在前端显示的时候，更加不同的级别显示不同的效果。

# 详细设计

## 路由器设计

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215144.png" alt="image-20210502213153921" style="display:inline; float:left" />

## 距离向量算法

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215145.png" alt="image-20210502213540598" style="display:inline; float:left" />

## Rip获取和释放锁

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215146.png" alt="image-20210502214142016" style="display:inline; float:left" />

## 初始化

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215147.png" alt="image-20210502214237098" style="display:inline; float:left" />

## 路由器发送路由表

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215148.png" alt="image-20210502214317293" style="display:inline; float:left" />

## 邻接路由器长时间未更新，将其设为不可达

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215149.png" alt="image-20210502214355543" style="display:inline; float:left" />

## 添加日志

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215150.png" alt="image-20210502214419605" style="display:inline; float:left" />

## 添加新链路

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215151.png" alt="image-20210502214435977" style="display:inline; float:left" />

## 主要运行线程

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215152.png" alt="image-20210502214513989" style="display:inline; float:left" />

# 调试设计

## 调试程序开始和暂停

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215153.png" alt="image-20210502214600465" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215154.png" alt="image-20210502214607024" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215155.png" alt="image-20210502214612836" style="display:inline; float:left" />

## 设置网络不可达

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215156.png" alt="image-20210502214623233" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215157.png" alt="image-20210502214634402" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215158.png" alt="image-20210502214639285" style="display:inline; float:left" />

## 添加网络

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215159.png" alt="image-20210502214654757" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215200.png" alt="image-20210502214659429" style="display:inline; float:left" />

## 添加线路

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215201.png" alt="image-20210502214711689" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215202.png" alt="image-20210502214717197" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215203.png" alt="image-20210502214721966" style="display:inline; float:left" />

## 程序整体运行截图

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215204.png" alt="image-20210502214730261" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215205.png" alt="image-20210502214735483" style="display:inline; float:left" />

<img src="https://gitee.com/ruanxinwei/image/raw/master/RIP/20210502215206.png" alt="image-20210502214740230" style="display:inline; float:left" />

