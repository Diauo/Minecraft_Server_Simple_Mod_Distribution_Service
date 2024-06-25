from flask import Flask, jsonify, send_from_directory, send_file
import os
import hashlib
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask("Minecraft MOD分发服务")
MODS_DIR = '/root/minecraft-1.20.1-forge-server/mods'
CLIENT_MODS_DIR = '/root/minecraft-1.20.1-forge-server/clientMods'
mod_cache = {}
last_updated = 0

# 初始化日志目录
log_directory = os.path.join(os.getcwd(), 'log')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# 配置日志记录器
log_file = os.path.join(log_directory, 'app.log')

# 添加控制台日志处理器
console_handler = logging.FileHandler(log_file, encoding='utf-8')
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))

# 获取Flask的默认logger并添加处理器
app.logger.addHandler(console_handler)

# 设置基本配置，防止重复记录
logging.basicConfig(level=logging.DEBUG)

# 确保Flask logger使用与基本配置一致的等级
app.logger.setLevel(logging.DEBUG)

scheduler = BackgroundScheduler()

# 计算MD5
def calculate_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()

# 更新MD5缓存信息
def update_mod_cache():
    app.logger.info('>> 更新mod信息')
    global mod_cache
    mod_cache = {}

    # 更新双端mod的缓存
    for mod in os.listdir(MODS_DIR):
        if os.path.isfile(os.path.join(MODS_DIR, mod)) and mod.endswith('.jar') and not mod.startswith('!'):
            md5 = calculate_md5(os.path.join(MODS_DIR, mod))
            mod_cache[md5] = {
                'name': mod ,
                'type': 'dual'
            }

    # 更新纯客户端mod的缓存
    for mod in os.listdir(CLIENT_MODS_DIR):
        if os.path.isfile(os.path.join(CLIENT_MODS_DIR, mod)) and mod.endswith('.jar'):
            md5 = calculate_md5(os.path.join(CLIENT_MODS_DIR, mod))
            mod_cache[md5] = {
                'name': mod,
                'type': 'client'
            }
            
# 每10分钟运行一次
scheduler.add_job(func=update_mod_cache, trigger="interval", minutes=10)
scheduler.start()

class ModDirEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global last_updated
        if time.time() - last_updated < 1:
            return
        last_updated = time.time()
        update_mod_cache()

# 重新更新缓存
@app.route('/update-cache', methods=['GET'])
def reload_chache():
    app.logger.info('>> 进行缓存更新')
    update_mod_cache()
    return "成功", 200
    
# 获取mod列表
@app.route('/mod-list', methods=['GET'])
def mod_list():
    app.logger.info('>> 获取mod列表')
    mod_list = [{'name': value['name'], 'md5': md5 } for md5, value in mod_cache.items()]
    return jsonify(mod_list)

# 下载mod
@app.route('/mods/<md5>', methods=['GET'])
def download_mod(md5):
    app.logger.info(f">> 获取mod：{md5}")
    mod_info = mod_cache.get(md5)
    if mod_info:
        app.logger.info(f">> 下载mod：{mod_info['name']}")
        directory = CLIENT_MODS_DIR if mod_info['type'] == 'client' else MODS_DIR
        file_path = os.path.join(directory, mod_info['name'])
        return send_from_directory(directory, mod_info['name'], as_attachment=True)
    return "未找到mod", 404

if __name__ == '__main__':
    # 启动时更新mod信息
    app.logger.info('> 初始化mod信息')
    update_mod_cache()
    app.logger.info('> 部署看门狗')
    event_handler = ModDirEventHandler()
    observer = Observer()
    observer.schedule(event_handler, MODS_DIR, recursive=False)
    observer.schedule(event_handler, CLIENT_MODS_DIR, recursive=False)
    observer.start()
    try:
        app.logger.info('> 初始化完成')
        app.run(host='0.0.0.0', port=23432)
    finally:
        app.logger.info('> 服务断开')
        observer.stop()
        observer.join()
        atexit.register(lambda: scheduler.shutdown())
