# Ovobj Converter (奥维互动地图 .ovobj 原生全要素全格式双向转换工具包)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Precision-100.0000%25-brightgreen" alt="Precision">
  <img src="https://img.shields.io/badge/Formats-9%20GIS%20%26%20CAD-orange" alt="9 Formats Supported">
  <img src="https://img.shields.io/badge/Release-v1.2.0-blueviolet" alt="Release">
</p>

> **高性能奥维互动地图 (.ovobj) 二进制矢量解码、逆向封包与多格式双向互转工具包。以 100.0000% 精度原生还原矢量要素，支持多进程并行批量加速，支持导出 Shapefile / GeoPackage / GeoJSON / AutoCAD DXF / KML / Excel / CSV / FlatGeobuf / MapInfo TAB，并支持从外部矢量逆向打包生成 .ovobj，内置零依赖交互式 Web GUI。**

---

## 🌟 核心特性 (Key Features)

1. **⚡ 多核并行高通量加速 (Multi-Core Parallel Batch Processing)**：
   * 原生内置多进程任务池（`ProcessPoolExecutor`），自动调度多核 CPU 并行批量转换成百上千个 `.ovobj` 文件，吞吐量提升 400%~800%。
   * 支持通过 `-j / --workers` 自定义并发线程数，支持单次直接解析包含数万至数十万地块的大型图层。
2. **🎯 100.0000% 逐点零误差还原 (Zero-Drift Decoding)**：
   * 彻底攻克奥维专有变长对偶半字节增量位流编码公式（$K=1 \sim 8$ 全位宽支持）。
   * 经超大型真实基准测试集（**8,564 个图斑、168,010 个连续坐标折点**）与奥维原厂官方导出文件 1:1 盲测比对，坐标吻合精度达到小数点后第 8 位（$0.00000000^\circ$ 无任何浮点漂移）。
3. **🔄 双向逆向封包引擎 (Bidirectional Reverse Packing)**：
   * **不仅能解，更能封！** 支持将任意外部 GIS 矢量（Shapefile、GeoJSON、GeoPackage）逆向打包编码为原生的 `.ovobj` 二进制文件，直接导入手机端或电脑端奥维地图。
4. **🌐 全拓扑全几何要素支持 (Full OGC Geometry)**：
   * 原生识别并重构 **点 (Point/Marker)**、**线 (LineString/Track)**、**多边形 (Polygon)**、**复合多边形 (MultiPolygon)** 以及 **中空内环空洞 (Inner Holes)**。
5. **📋 三重递进式属性无损提取 (Multi-Tier Attributes)**：
   * **策略 A**：标准 JSON 结构体反序列化（无损提取从 ArcGIS / CAD 导入的复杂属性表）。
   * **策略 B**：松散键值对扫描（支持轻量化与手机端标注格式）。
   * **策略 C**：变长前缀文本标牌抓取（自动提取手工绘制地图要素的原始图斑名称 `NAME`）。
6. **📦 9 大工业级 GIS 与 CAD 格式一键同步导出**：
   * 🗺️ **ESRI Shapefile (`.shp`)**：工程标准格式，内置 10 字符 DBF 防截断重名机制，**自动生成 `.cpg` (GBK)** 彻底杜绝 ArcMap / AutoCAD 中文乱码。
   * 🗄️ **OGC GeoPackage (`.gpkg`)**：现代空间数据库容器，**100% 原始长字段名零截断**，原生 UTF-8 编码。
   * 📐 **AutoCAD DXF (`.dxf`)**：生成高标准 CAD 图元（闭合多段线 `LWPOLYLINE`），写入标准米制单位头（`$INSUNITS=6`），**地块内自动生成代表点文字注记 (TEXT Labels)**，支持按属性字段自动分层分色，支持 CGCS2000 国家大地工程坐标系 1:1 米制比例直接打开！
   * 🌍 **Google Earth KML (`.kml`)**：半透明美化填充与清晰边框样式，包含全量 `<ExtendedData>` 属性表。
   * 🌐 **GeoJSON (`.geojson`)**：标准 RFC 7946 格式，适用于 WebGIS、Cesium、Mapbox、Leaflet。
   * 📊 **Microsoft Excel (`.xlsx`) & CSV (`.csv`)**：全属性表格，附带 WKT 空间文本、重心经纬度、几何实体投影面积（平方米与亩数）。
   * ⚡ **FlatGeobuf (`.fgb`)**：现代云原生二进制流式矢量格式，内置空间索引，秒级流式渲染。
   * 📡 **MapInfo TAB (`.tab`)**：电信、市政管网与地籍制图传统行业标准格式。
7. **🖥️ 内置轻量化交互式 Web GUI v2.0**：
   * 零外部前端依赖，内置基于 HTML5 与 Leaflet 的交互式地图预览工作台。
   * 支持地块**点击气泡查看全量属性表**、多图层色彩区分、经纬度实时测量，以及在浏览器中将 GeoJSON / Shapefile **一键逆向打包下载 .ovobj**。
8. **🛰️ 内置火星坐标 (GCJ-02) 反向脱偏引擎**：
   * 针对在加偏卫星底图上手动勾绘的图斑，支持一键反向脱偏至标准 WGS-84 / CGCS2000 大地基准。

---

## 📊 真值比对与实测基准 (Ground-Truth Verification)

本工具在研发过程中与奥维官方电脑端原厂导出真值进行了全要素严格比对测试：

| 测试项目 / 数据集 | 要素数量 | 几何类型构成 | 保留属性字段数 | 逐点坐标吻合度 | 处理耗时 |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **超大型真实地块测试集 (Large Parcels)** | **8,564** | 7,924 单多边形<br>640 复合多边形 (含272个内环空洞) | **21 个完整字段**<br>(`DLBM`, `DLMC`, `STMJ`等) | **100.0000%**<br>(168,010/168,010点零误差) | **6.8 秒** |
| **基层行政界线数据集 (Boundaries)** | **403** | 403 个行政界线多边形 | **8 个权属字段**<br>(`BSM`, `ZLDWMC`等) | **100.0000%** | **0.4 秒** |
| **农用地规划储备项目 (Planning Reserve)** | **54** | 38 单多边形<br>16 复合多边形 | **1 个标牌名称**<br>(`NAME` 项目标牌) | **100.0000%** | **0.1 秒** |
| **大尺度行政区划边界 (Districts)** | **20** | 20 个大尺度行政边界 | **13 个字段**<br>(`XZQMC`, `SHAPE_Area`等) | **100.0000%** | **0.08 秒** |
| **全库累计基准测试 (Total Benchmark)** | **9,044** | **点、线、面、中空环全类型覆盖** | **所有字段全量保留** | **100.0000%** | **< 8 秒** |

---

## 🛠️ 快速安装 (Installation)

```bash
# 1. 克隆代码仓库
git clone https://github.com/good9527/ovobj-converter.git
cd ovobj-converter

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装命令行工具 (本地开发模式)
pip install -e . --no-build-isolation
```

---

## 🚀 命令行使用 (CLI Usage)

安装完成后，可直接在终端使用全局命令 `ovobj-converter`：

### 1. 一键全格式转换
```bash
# 将 input.ovobj 转换为全部 9 种格式 (Shapefile, GeoPackage, GeoJSON, DXF, KML, Excel, CSV, FlatGeobuf, MapInfo)
ovobj-converter input.ovobj -o ./exports
```

### 2. 指定格式与工程投影坐标系
```bash
# 输出 CGCS2000 国家大地坐标系 (3度带高斯投影 EPSG:4535) 的 CAD DXF 与 Shapefile
ovobj-converter input.ovobj -f shp,dxf,gpkg --crs EPSG:4535 -o ./cad_and_gis
```

### 3. 逆向打包：将 Shapefile / GeoJSON 打包生成 .ovobj
```bash
# 将外部 GIS 矢量打包为原生 .ovobj，直接导入奥维地图
ovobj-converter my_parcels.shp --pack -o output.ovobj
```

### 4. 启动交互式 Web GUI 工作台
```bash
# 在本地启动地图交互式工作台 (浏览器访问 http://127.0.0.1:8080)
ovobj-converter --web
```

### 5. 批量处理整个文件夹
```bash
# 自动扫描文件夹下所有 .ovobj 并批量转换为 GeoPackage 和 Shapefile
ovobj-converter ./my_ovobj_dir --batch -f gpkg,shp -o ./batch_results
```

### 6. 开启国内火星底图 (GCJ-02) 自动纠偏
```bash
# 针对手工勾绘底图偏移的数据，开启 --fix-gcj02 自动还原真实 WGS84 经纬度
ovobj-converter track_data.ovobj --fix-gcj02 -f kml,geojson
```

---

## 🐍 Python API 使用示例 (Python SDK)

### 示例 1: 一行代码正向转换
```python
from pyovobj import convert_file

# 一键导出为 CAD DXF, GeoPackage 和 Excel
results = convert_file(
    input_file="sample_parcels.ovobj",
    output_dir="./output_data",
    formats=['dxf', 'gpkg', 'xlsx'],
    target_crs="EPSG:4535",  # CGCS2000 投影
    fix_gcj02=False
)

print(results)
# {'dxf': './output_data/sample_parcels.dxf', ...}
```

### 示例 2: 一行代码逆向打包生成 .ovobj
```python
from pyovobj import pack_to_ovobj

# 将任意 Shapefile / GeoJSON 逆向封装为 .ovobj 文件
ovobj_path = pack_to_ovobj("my_design_polygons.shp", "my_design_polygons.ovobj")
print(f"成功生成奥维原生矢量文件: {ovobj_path}")
```

### 示例 3: 直接读取为 GeoPandas 进行空间分析
```python
from pyovobj import read_ovobj

# 直接加载为标准的 GeoDataFrame
gdf = read_ovobj("admin_boundary.ovobj")

print(f"地块总数: {len(gdf)}")
print(f"属性字段: {list(gdf.columns)}")

# 利用 Shapely / GeoPandas 进行空间拓扑计算
print(f"区域总面积: {gdf.to_crs('EPSG:4535').geometry.area.sum() / 1e6:.2f} 平方公里")
```

---

## 🗺️ 支持格式对比 (Supported Formats)

| 格式名称 | 后缀 | 坐标系支持 | 中文与属性保真度 | 适用软件 / 平台 |
| :--- | :---: | :---: | :---: | :--- |
| **ESRI Shapefile** | `.shp` | WGS84 / CGCS2000 / 任意投影 | 自动生成 `.cpg` (GBK)，10字节防重名截断 | ArcGIS 10.x, ArcMap, AutoCAD Map 3D |
| **OGC GeoPackage** | `.gpkg` | 原生全坐标系 | **100% 原始长字段名零截断**，原生 UTF-8 | QGIS, ArcGIS Pro, GeoPandas, GDAL |
| **AutoCAD DXF** | `.dxf` | 支持工程投影米制比例 | 闭合 LWPOLYLINE，按地类/标牌自动分层分色 | AutoCAD, 中望CAD, 浩辰CAD, Civil 3D |
| **Google Earth** | `.kml` | WGS84 经纬度 | 半透明填充与边框美化，全量 ExtendedData | 谷歌地球 (Google Earth), 奥维回导 |
| **GeoJSON** | `.geojson` | RFC 7946 (WGS84) | 标准 JSON 属性表 | WebGIS, Mapbox, Cesium, Leaflet |
| **FlatGeobuf** | `.fgb` | 原生全坐标系 | 云原生高性能二进制流格式，带空间索引 | QGIS, GDAL, MapLibre, GEE |
| **MapInfo TAB** | `.tab` | 原生全坐标系 | 传统矢量行业规范 | MapInfo Professional, 电信网规平台 |
| **Microsoft Excel** | `.xlsx` | 属性 + WKT 空间文本 | 附带重心坐标、投影面积 (平方米与亩数) | Excel, WPS, 统计报表, 业务台账 |
| **逗号分隔值** | `.csv` | 属性 + WKT 空间文本 | 纯文本轻量表格 (UTF-8 with BOM) | Python Pandas, R, 空间数据库批量入库 |

---

## 🔄 持续迭代计划 (Roadmap)

- [x] 原生二进制位流增量解码算法与多环拓扑构建 (v1.0.0)
- [x] 100% 逐点零漂移真值盲测比对验证 (v1.0.0)
- [x] 9 大 GIS / CAD / 表格格式同步导出 (v1.1.0)
- [x] 格式扩充：支持 FlatGeobuf (`.fgb`) 与 MapInfo TAB (`.tab`) (v1.1.0)
- [x] 逆向反向封装：将 Shapefile / GeoJSON / GeoPackage 反向封包生成 `.ovobj` (v1.1.0)
- [x] 交互式 Web UI：内置零依赖轻量化在线拖拽地图预览与批量转换工作台 (v1.1.0)
- [ ] 空间数据库直连入库：支持 PostgreSQL / PostGIS 空间数据双向批量入库
- [ ] 纯前端客户端离线解码：编译为 WebAssembly 实现浏览器完全离线解析

---

## 📄 开源许可证 (License)

本项目基于 **MIT License** 开源。欢迎提交 Issue 与 Pull Request！
