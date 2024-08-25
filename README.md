# 🏅葫芦侠一键签到

> **💯42个版块精准签到**
> 
> **❇️多账号支持**
> 
> **📝企业微信群机器人推送**
> 
> **🕗每日定时执行**

### 食用指南

+ 利用**Github Action**实现每日自动签到，按照```main.yml```配置即可。
+ 为了安全起见，建议将敏感信息（如企业微信群机器人URL和账号信息）存储在Github Secrets中，并在```main.yml```中引用。

### 配置步骤

1. **Fork本项目**：
   - 点击右上角`Fork`按钮，将本项目Fork到你的仓库。

2. **设置Github Secrets**：
   - 进入你的仓库，点击`Settings`。
   - 选择`Secrets and variables` -> `Actions`。
   - 点击`New repository secret`，添加名为`WECHAT_ROBOT_URL`的Secret，值为你企业微信群机器人的URL。
   - 点击`New repository secret`，添加名为`ACCOUNTS`的Secret，值为你的账号信息，格式如下：
     ```
     account1,password1
     account2,password2
     ```

3. **在Github Actions中创建```main.yml```**：
   - 进入你的仓库，点击`Actions`。
   - 点击`New workflow`，选择`Set up a workflow yourself`。
   - 将以下内容粘贴到 `main.yml` 文件中：
     ```yaml
     name: huluxia_signin
     on:
       schedule:    # 定时触发
         - cron: '0 16 * * *'  # 24点
       workflow_dispatch:  # 支持手动触发
     jobs:
       build:
         runs-on: ubuntu-latest
         steps:
           - name: Checkout
             uses: actions/checkout@v3
           - name: '初始化python环境'
             uses: actions/setup-python@v4
             with:
                python-version: 3.10.11
           - name: '安装依赖'
             run: |
               pip install --upgrade pip
               pip install -r ./requirements.txt
           - name: '开始运行'
             id: signin-outputs
             env:
               WECHAT_ROBOT_URL: ${{ secrets.WECHAT_ROBOT_URL }}
               ACCOUNTS: ${{ secrets.ACCOUNTS }}
             run: |
               python ./main.py
     ```


### 消息推送方式

目前仅支持**企业微信群机器人推送**。如果你有其他推送需求或希望增加其他推送方式（如邮件、Telegram等），欢迎提交PR或提出Issue。

### 效果图

![企业微信群机器人自动推送效果图](http://cdn.u1.huluxia.com/g4/M03/76/E0/rBAAdmQyQ7WAJmWYAAPy7GWC2XA434.jpg)

### 使用声明

本项目仅供学习和交流使用，请勿用于任何商业用途。使用者需自行承担因使用本项目而产生的任何风险和责任。

<br/>

**🚩By [BoltLv4215](https://github.com/BoltLv4215 "点个Star和Follow吧！")**<br/>
###### **最后编辑于2024年8月25日**
