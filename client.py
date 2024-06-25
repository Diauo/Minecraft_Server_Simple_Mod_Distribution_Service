import requests
import os
import hashlib
import json
import re

SERVER_URL = ""
CLIENT_MODS_DIR = ""
config_filename = "modUpdateConfig.json"


def init():
    global CLIENT_MODS_DIR
    global SERVER_URL

    if not os.path.exists(config_filename):
        # 文件不存在，创建并设置初始值
        config_data = {}

        # 要求用户输入一个文件路径和URL
        path = input("请输入Minecraft mod目录: ")
        url = input("请输入Mod分发服务地址(回车使用默认): ")
        if not url:
            url = ""

        config_data["path"] = path
        config_data["url"] = url

        CLIENT_MODS_DIR = path
        SERVER_URL = url

        # 将数据写入modUpdateConfig.json
        with open(config_filename, "w", encoding="utf-8") as config_file:
            json.dump(config_data, config_file, indent=4)
    else:
        # 文件存在，从中读取路径和URL
        with open(config_filename, "r", encoding="utf-8") as config_file:
            config_data = json.load(config_file)

        path = config_data.get("path", None)
        url = config_data.get("url", None)

        if path and url:
            if not os.path.exists(path):
                print("配置文件中的地址无效，请确认")
                path = input("请输入Minecraft mod目录: ")
                if not os.path.exists(path):
                    input("路径无效！程序终止（回车结束）")
                    exit()
                config_data["path"] = path
                # 将数据写入modUpdateConfig.json
                with open(config_filename, "w", encoding="utf-8") as config_file:
                    json.dump(config_data, config_file, indent=4)
            CLIENT_MODS_DIR = path
            SERVER_URL = url
            print(f"配置加载成功: \nMinecraft mod目录: {path} \nMod分发服务地址: {url}")
        else:
            if not path:
                print(f"从配置文件中读取Minecraft mod目录失败")
                path = input("请输入Minecraft mod目录: ")
                config_data["path"] = path
                CLIENT_MODS_DIR = path

            if not url:
                print(f"从配置文件中读取Mod分发服务地址失败")
                url = input("请输入Mod分发服务地址: ")
                config_data["url"] = url
                SERVER_URL = url

            # 更新配置文件
            with open(config_filename, "w", encoding="utf-8") as config_file:
                json.dump(config_data, config_file, indent=4)


def get_mod_list():
    response = requests.get(f"{SERVER_URL}/mod-list")
    return (
        {mod["md5"]: mod["name"] for mod in response.json()}
        if response.status_code == 200
        else []
    )


def download_mod(mod_md5, mod_name):
    response = requests.get(f"{SERVER_URL}/mods/{mod_md5}")
    mod_name = re.sub(r'[\\/:*?"<>|]', "_", mod_name)
    if response.status_code == 200:
        with open(os.path.join(CLIENT_MODS_DIR, mod_name), "wb") as f:
            f.write(response.content)


def del_mod(mod_name):
    os.remove(os.path.join(CLIENT_MODS_DIR, mod_name))


def calculate_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()


def get_local_mods():
    return {
        calculate_md5(os.path.join(CLIENT_MODS_DIR, mod)): mod
        for mod in os.listdir(CLIENT_MODS_DIR)
        if mod.endswith(".jar") and not mod.startswith("!")
    }


def sync_mods():
    server_mods = get_mod_list()
    if not server_mods:
        input(f"从{SERVER_URL}读取mod信息失败，程序终止（回车结束）")
        exit()
    local_mods = get_local_mods()

    for md5 in server_mods:
        if md5 not in local_mods:
            name = server_mods[md5]
            print(f"更新mod: {name}")
            download_mod(md5, name)

    print("删除过时mod。。。")
    select = ""
    for md5 in local_mods:
        if md5 not in server_mods:
            name = local_mods[md5]
            if select == "A":
                print(f"删除mod: {name}")
                del_mod(name)
            else:
                select = input(
                    f"{name} 已经过期，是否删除？Y=删除，N=保留，A=全部删除 \n>:"
                )
                if (select == "A" or select == "a") or (select == "Y" or select == "y"):
                    print(f"删除mod: {name}")
                    del_mod(name)
                else:
                    continue


if __name__ == "__main__":
    try:
        init()
        sync_mods()
        input("更新完成，按回车退出")
    except Exception as e:
        print(e)
        input("程序异常！结束运行")
