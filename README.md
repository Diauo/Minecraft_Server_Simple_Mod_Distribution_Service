﻿# 中文

1. 服务器mod中以感叹号开头的mod将不会写入分发服务的mod缓存。以实现排除纯服务器mod，避免参与分发

2. clientMods为纯客户端mod，其中的mod不会被我的世界服务器加载，但是会被分发服务读取进入mod缓存并参与分发

3. 服务以mod文件md5进行对比，分发服务每隔10分钟会更新一次mod缓存，并且检测到两个mod目录的文件产生变动时，也会更新mod缓存

# ENG
1. Server mods that begin with an exclamation point will not be written to the distribution service's mod cache. This is to exclude pure server mods from participating in the distribution.

2. clientMods are purely client-side mods, which will not be loaded by the My World server, but will be read by the distribution service into the mod cache and participate in the distribution.

3. The service compares the mod files by md5, the distribution service updates the mod cache every 10 minutes, and also updates the mod cache when it detects a change in the files in both mod directories.
