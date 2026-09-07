# 南京本地地图与地址识别

本目录用于部署系统自己的南京地图和地理编码服务。业务前端不会再向高德或公共 OSM 服务发送地图、搜索或地址数据。

## 数据准备

将以下两个文件放入 `local-map/data/`，文件不纳入 Git：

- `nanjing.osm.pbf`：仅包含南京市行政区范围的 OSM PBF 数据，用于 Nominatim 地址和地点检索。
- `nanjing.mbtiles`：由同一范围数据制作的 OpenMapTiles/MBTiles 矢量切片，用于地图显示。

数据坐标必须使用 WGS84。不要把高德 GCJ-02 坐标写入此数据集。

## 启动

1. 复制 `local-map/.env.example` 的 `LOCAL_GEOCODER_URL` 和 `LOCAL_GEOCODER_TIMEOUT_SECONDS` 至 `audit_api/runtime/secrets/mineru.env` 或系统环境变量。
2. 为前端配置 `VUE_APP_LOCAL_MAP_STYLE_URL`。生产环境建议由 Nginx 反向代理为同源地址，例如 `/local-map/styles/basic/style.json`，不要让浏览器直接访问仅绑定 `127.0.0.1` 的端口。
3. 在本目录执行 `docker compose up -d`。首次导入 PBF 会建立 PostgreSQL 索引，完成前地址搜索不会可用。
4. 重启 Python 审核服务、RuoYi 后端和前端服务。

## 容量与运行条件

南京范围 PBF 与 MBTiles 的体积取决于来源和缩放级别；应预留至少 30 GB 可用磁盘。Nominatim 导入阶段建议 8 GB 以上内存，运行期通常低于导入期。显卡显存与本服务无关。

## 使用边界

- 地址输入自动请求本机 Nominatim 服务，结果会写入 `audit_api/runtime/local_geocoder/geocode_cache.sqlite3` 缓存。
- 地图服务和地理编码服务应放在内网主机或业务服务器，不应配置为公共 OSM/Nominatim 地址。
- 项目坐标统一保存为 WGS84。历史高德坐标属于 GCJ-02，迁移前需进行坐标转换，否则在本地底图上会出现偏移。
