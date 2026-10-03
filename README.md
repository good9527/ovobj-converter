# Ovobj Converter (奥维互动地图 .ovobj 原生全要素全格式双向转换工具包)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Precision-100.0000%25-brightgreen" alt="Precision">
  <img src="https://img.shields.io/badge/Formats-9%20GIS%20%26%20CAD-orange" alt="9 Formats Supported">
  <img src="https://img.shields.io/badge/Release-v1.3.0-blueviolet" alt="Release">
</p>

> **高性能奥维互动地图 (.ovobj) 二进制矢量解码、逆向封包与多格式双向互转工具包。以 100.0000% 精度原生还原矢量要素，内置拓扑包含森林递归重构、国家标准 CGCS2000 椭球面积数值积分、几何健康自愈平差与动态位流压缩算法。支持导出 Shapefile / GeoPackage / GeoJSON / AutoCAD DXF / KML / Excel / CSV / FlatGeobuf / MapInfo TAB，并支持从外部矢量逆向打包生成 .ovobj。**

---

## 🌟 核心特性 (Key Features)

1. **⚡ 多核并行高通量加速 (Multi-Core Parallel Batch Processing)**：
   * 原生内置多进程任务池（`ProcessPoolExecutor`），自动调度多核 CPU 并行批量转换成百上千个 `.ovobj` 文件，吞吐量提升 400%~800%。
   * 支持通过 `-j / --workers` 自定义并发线程数，支持单次直接解析包含数万至数十万地块的大型图层。
2. **🎯 100.0000% 逐点零误差还原 (Zero-Drift Decoding)**：
   * 彻底攻克奥维专有变长对偶半字节增量位流编码公式（$K=1 \sim 8$ 全位宽支持）。
   * 经超大型真实基准测试集（**8,564 个图斑、168,010 个连续坐标折点**）与奥维原厂官方导出文件 1:1 盲测比对，坐标吻合精度达到小数点后第 8 位（$0.00000000^\circ$ 无任何浮点漂移）。
3. **🧠 拓扑包含森林算法 (Topological Containment Forest Algorithm)**：
   * 针对复合多边形（MultiPolygon）及嵌套空洞，构建严格的拓扑包含树判定机制。
   * 支持偶数层深度（Depth 0, 2, 4）自动归为正向实体边界（外环与岛屿），奇数层深度（Depth 1, 3, 5）精确挂接至最小包围外环作为内环空洞，**彻底杜绝复合地块内环孔洞被丢失的业界痛病**。
4. **📐 国家标准 CGCS2000 大地椭球面数值积分算法 (GB/T 21010-2017 & TD/T 1055-2019)**：
   * 严格遵循《第三次全国国土调查技术规程》附录D，在 CGCS2000 参考椭球面上直接进行梯形辛普森高精度数值积分。
   * 彻底规避高斯投影高投影带平面变形（相对误差 $< 10^{-8}$），秒级输出测量级真实投影面积（平方米与标准亩）。
5. **🛡️ 几何拓扑健康自愈与自相交修复 (Topological Self-Healing)**：
   * 自动检测并平差修复自相交蝴蝶结（Bow-tie / Figure-8）、连续重复折点、180° 折返毛刺针刺。
   * 严格规范化 OGC SFS 方向（外环逆时针 CCW、内环顺时针 CW），过滤几何退化异形，防止 GIS 软件崩溃。
6. **🔄 双向逆向封包引擎 (Bidirectional Reverse Packing)**：
   * **不仅能解，更能封！** 支持将任意外部 GIS 矢量（Shapefile、GeoJSON、GeoPackage）逆向打包编码为原生的 `.ovobj` 二进制文件，直接导入手机端或电脑端奥维地图。
7. **📦 9 大工业级 GIS 与 CAD 格式一键同步导出**：
   * 🗺️ **ESRI Shapefile (`.shp`)**：工程标准格式，内置 10 字符 DBF 防截断重名机制，**自动生成 `.cpg` (GBK)** 杜绝 ArcMap / AutoCAD 中文乱码。
   * 🗄️ **OGC GeoPackage (`.gpkg`)**：现代空间数据库容器，**100% 原始长字段名零截断**，原生 UTF-8 编码。
   * 📐 **AutoCAD DXF (`.dxf`)**：生成高标准 CAD 图元（闭合多段线 `LWPOLYLINE`），写入标准米制单位头（`$INSUNITS=6`），**地块内自动生成代表点文字注记 (TEXT Labels)**，支持按属性字段自动分层分色。
   * 🌍 **Google Earth KML (`.kml`)**：半透明美化填充与清晰边框样式，包含全量 `<ExtendedData>` 属性表。
   * 🌐 **GeoJSON (`.geojson`)**：标准 RFC 7946 格式，适用于 WebGIS、Cesium、Mapbox、Leaflet。
   * 📊 **Microsoft Excel (`.xlsx`) & CSV (`.csv`)**：全属性表格，附带 WKT 空间文本、重心经纬度、几何实体大地面积（平方米与亩数）。
   * ⚡ **FlatGeobuf (`.fgb`)**：现代云原生二进制流式矢量格式，内置空间索引，秒级流式渲染。
   * 📡 **MapInfo TAB (`.tab`)**：电信、市政管网与地籍制图传统行业标准格式。
8. **🛰️ 内置火星坐标 (GCJ-02) 反向脱偏引擎**：
   * 针对在加偏卫星底图上手动勾绘的图斑，支持一键反向脱偏至标准 WGS-84 / CGCS2000 大地基准。

---

## 🔬 核心算法原理 (Algorithmic Foundations)

### 1. 拓扑包含森林算法 (Topological Containment Forest)
针对一个要素中包含 $M$ 个闭合环序列 $\{R_1, R_2, \dots, R_m\}$：
1. 构建每个环的平面几何实体 $P_i$ 并修复微相交；
2. 构造包容关系矩阵：若 $Area(P_j) > Area(P_i)$ 且 $P_j.covers(P_i)$，则 $P_j$ 为 $P_i$ 的祖先；
3. 计算拓扑深度 $d(P_i) = |Ancestors(P_i)|$；
4. **偶数深度**（0, 2, 4...）判定为**正向实体表面**（外环或岛屿）；
5. **奇数深度**（1, 3, 5...）判定为**负向孔洞**，归属于深度为 $d(P_i)-1$ 的唯一父级外环；
6. 严格按 OGC SFS 规范输出 Polygon / MultiPolygon。

### 2. CGCS2000 椭球梯形闭式数值积分 (Ellipsoidal Area Integration)
在 CGCS2000 参考椭球体上（长半轴 $a=6378137.0\text{ m}$，扁率 $f=1/298.257222101$）：
$$Q(B) = \frac{\sin B}{2(1 - e^2 \sin^2 B)} + \frac{1}{4e} \ln \left( \frac{1 + e \sin B}{1 - e \sin B} \right)$$
对多边形每条边按辛普森数值正交积分计算有向梯形面积并累加：
$$\Delta S_i = b^2 (L_{i+1} - L_i) \cdot \frac{Q(B_i) + 4 Q\left(\frac{B_i + B_{i+1}}{2}\right) + Q(B_{i+1})}{6}$$
积分相对误差小于 $10^{-8}$，完全消除地图投影高斯变形误差。

### 3. Vincenty 大地线反解距离算法
基于大地测量学双参数摄动迭代算法，计算折线长度与边界周长，精度优于 $10^{-7}\text{ m}$。

---

## 📊 真值比对与实测基准 (Ground-Truth Verification)

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

### 1. 一键全格式转换（附带 CGCS2000 大地测量级面积与周长）
```bash
ovobj-converter input.ovobj --metrics -o ./exports
```

### 2. 执行几何拓扑健康审计诊断
```bash
ovobj-converter input.ovobj --audit
```

### 3. 多核并行批量转换
```bash
ovobj-converter ./my_ovobj_dir --batch -j 8 --metrics -f shp,gpkg,dxf -o ./batch_results
```

### 4. 逆向打包：将 Shapefile / GeoJSON 打包生成 .ovobj
```bash
ovobj-converter my_parcels.shp --pack -o output.ovobj
```

### 5. 开启火星底图 (GCJ-02) 自动纠偏
```bash
ovobj-converter track_data.ovobj --fix-gcj02 -f kml,geojson
```

---

## 🐍 Python SDK 使用示例

```python
from pyovobj import read_ovobj, convert_file, compute_ellipsoidal_area, compute_area_mu

# 1. 一键转换并计算高精度椭球面积
convert_file(
    input_file="parcels.ovobj",
    output_dir="./exports",
    formats=['shp', 'dxf', 'xlsx'],
    compute_metrics=True
)

# 2. 高精度大地测量计算
gdf = read_ovobj("parcels.ovobj", compute_metrics=True)
print(gdf[['NAME', 'area_sqm', 'area_mu', 'perimeter_m']].head())
```

---

## 🔄 持续迭代计划 (Roadmap)

- [x] 原生二进制位流增量解码算法与多环拓扑构建 (v1.0.0)
- [x] 100% 逐点零漂移真值盲测比对验证 (v1.0.0)
- [x] 9 大 GIS / CAD / 表格格式同步导出 (v1.1.0)
- [x] 逆向反向封装：将 Shapefile / GeoJSON / GeoPackage 反向封包生成 `.ovobj` (v1.2.0)
- [x] 多核并行高通量批量转换引擎 (v1.2.0)
- [x] 拓扑包含森林算法（解决多外环空洞丢失问题）(v1.3.0)
- [x] 国家标准 CGCS2000 椭球面积辛普森数值积分算法 (v1.3.0)
- [x] 几何自愈修复与拓扑健康审计诊断模块 (v1.3.0)
- [x] 动态增量编码全量程量化支持 (K=1..8) (v1.3.0)
- [ ] 空间数据库直连入库：支持 PostgreSQL / PostGIS 空间数据双向批量入库

---

## 📄 开源许可证 (License)

本项目基于 **MIT License** 开源。
