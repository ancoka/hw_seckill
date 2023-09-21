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

- 登陆华为商城（[www.vmall.com](https://www.vmall.com)）
- 自动使用配置账号密码登陆
- 秒杀配置等待抢购
- 开始自动抢购
- 多浏览器支持（待实现）

## 运行环境
请安装大于等于python 3.6 的版本及同浏览器版本匹配的浏览器驱动运行此项目

- [Python下载](https://www.python.org/)
- [ChromeDriver下载](https://sites.google.com/chromium.org/driver/downloads)

## 第三方库

- 需要使用到的库已经放在requirements.txt，使用pip安装的可以使用指令  
`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`


## 使用教程  
#### 1. Chrome浏览器
#### 2. 填写config.ini配置信息 
(1)账号信息：`name`、`password` 填写对应的华为账号、密码

(2)商品信息：`name`、`id`、 `color`、`version` 分别为对应的商品名称、商品ID、手机颜色（宣白）、手机版本（16GB+512GB）

> `id`默认填写Mate60Pro+，如需修改请自行修改
> `color` 默认填写宣白，如需修改请自行修改对应手机的颜色
> `version` 默认填写16GB+512GB，如需修改请自行修改对应手机的版本

(3)浏览器：`userDataDir`谷歌浏览器默认用户数据目录：
- MacOS默认路径为：/Users/用户名/Library/Application Support/Google/Chrome/Default
- Windows默认路径为：C:/Users/用户名/AppData/Local/Google/Chrome/User Data
- Linux默认路径为：~/.config/google-chrome/Default


以上都是必须的.


#### 3.运行main.py 
> python main.py

## 打赏 
无