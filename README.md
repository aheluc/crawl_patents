## 概述
本脚本从专利之星上爬取专利文档的摘要和说明书并存入sqlite3数据库
## 配置
在config文件中填写自己的账号和密码
genres可以填写搜索的关键词
max_check_pages是一个关键词抽取多少页专利，一页15个专利
## 使用
需要安装selenium包。
同时需要有Chrome浏览器，并将下载好的chromedriver.exe放入环境变量PATH所在的目录下。
直接用命令 python crawler.py 调用脚本