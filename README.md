# Hw_Seckill
请安装保证Python版本大于等于3.6

## 特别声明:

* 本仓库发布的`hw_seckill`项目中涉及的任何脚本，仅用于测试和学习研究，禁止用于商业用途，不能保证其合法性，准确性，完整性和有效性，请根据情况自行判断。

* 本项目内所有资源文件，禁止任何公众号、自媒体进行任何形式的转载、发布。

* `ancoka` 对任何脚本问题概不负责，包括但不限于由任何脚本错误导致的任何损失或损害.

* 间接使用脚本的任何用户，包括但不限于建立VPS或在某些行为违反国家/地区法律或相关法规的情况下进行传播, `ancoka` 对于由此引起的任何隐私泄漏或其他后果概不负责。

* 请勿将`hw_seckill`项目的任何内容用于商业或非法目的，否则后果自负。

* 如果任何单位或个人认为该项目的脚本可能涉嫌侵犯其权利，则应及时通知并提供身份证明，所有权证明，我们将在收到认证文件后删除相关脚本。

* 以任何方式查看此项目的人或直接或间接使用`hw_seckill`项目的任何脚本的使用者都应仔细阅读此声明。`ancoka` 保留随时更改或补充此免责声明的权利。一旦使用并复制了任何相关脚本或`hw_seckill`项目，则视为您已接受此免责声明。
  
* 您必须在下载后的24小时内从计算机或手机中完全删除以上内容。  
  
* 本项目遵循`GPL-3.0 License`协议，如果本特别声明与`GPL-3.0 License`协议有冲突之处，以本特别声明为准。

> ***您使用或者复制了本仓库且本人制作的任何代码或项目，则视为`已接受`此声明，请仔细阅读***  
> ***您在本声明未发出之时点使用或者复制了本仓库且本人制作的任何代码或项目且此时还在使用，则视为`已接受`此声明，请仔细阅读***

## 简介
华为Mate60手机发布后，手机非常火爆，一机难求，拼手速压根抢不到手机。于是`ancoka`萌生了一个想法，通过程序自动抢购手机，说干就干，`ancoka`大干一晚终于把脚本撸了出来。
目前程序可能不太稳定，有时会抽风，后期会慢慢优化，目前仅供测试和参考，有问题欢迎指正，不喜勿喷。

## 主要功能

- [x] 登陆华为商城（[www.vmall.com](https://www.vmall.com)）
- [x] 自动使用配置账号密码登陆
- [x] 首次登陆自动发送验证码
- [x] 自动信任浏览器
- [x] 秒杀配置等待抢购
- [x] 开始自动抢购
- [x] 自动提交订单
- [x] 无窗口模式支持
- [x] 多浏览器支持（chrome、firefox、edge、safari）
- [x] 多线程支持
- [ ] 京东APP抢购（规划中）
- [ ] 下单成功通知功能（待实现）

## 运行环境
请安装大于等于python 3.6 的版本及同浏览器版本匹配的浏览器驱动运行此项目

- [Python下载](https://www.python.org/)
- [ChromeDriver下载](https://sites.google.com/chromium.org/driver/downloads)
- [GeckoDriver下载](https://github.com/mozilla/geckodriver/releases)
- [EdgeDriver下载](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)
- [SafariDriver无需下载]，需要设置里打开允许远程自动化

## 第三方库

- 需要使用到的库已经放在requirements.txt，使用pip安装的可以使用指令  
`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`


## 使用教程
#### 1. Chrome | Firefox ｜Edge 浏览器
#### 2. 填写 config.ini 配置信息
(1)账号信息：`name`、`password` 填写对应的华为账号、密码

(2)商品信息：`name`、`id`、 `color`、`version`,`saleType`,`sets` 分别为对应的商品名称、商品ID、商品颜色或款式（宣白）、版本（16GB+512GB）、销售类型、套装规格

> `id`默认填写Mate60Pro+，如需修改请自行修改
> 
> `color` 默认填写宣白，如需修改请自行修改对应商品对颜色或款式，如：手机为颜色、手表为款式
> 
> `version` 默认填写16GB+512GB，如需修改请自行修改对应商品的版本
> 
> `saleType` 销售类型，默认填写全款购买，如需修改请自行修改对应商品持的销售类型
> 
> `sets` 套装规格默认为空，当填写后程序将只抢购套装；需要填写套装对应的SKU信息，不同SKU信息之前采用“,”分割，如：“12GB+512GB 青山黛,木星棕 深棕色真皮表带,雅川青 无线充版”


(3)浏览器：`type`、`driverPath`、 `headless`、 `userAgent` 分别对应浏览器类型、浏览器驱动绝对路径、是否开启无界面模式、userAgent：

> `type` 默认为chrome，可选：chrome、firefox、edge、safari，目前safari还有些问题不建议选择
> 
> `driverPath` 对应浏览器类型的驱动绝对路径，如果设置，则加载该路径的驱动，未设置需要将驱动加到环境变量
> 
> `headless` 是否开启无界面模式，默认为否，无界面模式需要设置userAgent
> 
> `userAgent` 需要填写对应浏览器的userAgent，如Chrome：Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36


(4)程序处理配置：`thread`、`interval` 分别为线程数、提交订单间隔时长：

> `thread` 线程数，默认为1，表示单线程，最大线程数为20
> 
> `interval` 提交订单间隔时长，单位为“秒”，默认为0.001秒，最小为0.001秒

以上都是必须的.


#### 3.运行main.py
> python main.py

## 关注我
!["漫漫编程路"](./wechat.png)

## 打赏
无