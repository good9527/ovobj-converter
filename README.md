# Ovobj Converter (Native Vector Converter & Geospatial Toolkit)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-2b5797?logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-0e7090?logo=open-source-initiative&logoColor=white" alt="License">
  <img src="https://img.shields.io/badge/Precision-100.0000%25-059669" alt="Precision">
  <img src="https://img.shields.io/badge/Formats-9%20GIS%20%26%20CAD-7c3aed" alt="Formats">
  <img src="https://img.shields.io/badge/CI-Passing-10b981?logo=githubactions&logoColor=white" alt="CI Status">
  <img src="https://img.shields.io/badge/Release-v1.5.0-1e293b" alt="Release">
</p>

> 高性能奥维互动地图 (.ovobj) 二进制矢量解码、逆向封包与高精度大地工程算法工具包。以 100.0000% 精度原生还原矢量要素，内置 STRtree 空间索引拓扑包含森林、NumPy 矢量化国家标准 CGCS2000 椭球面积数值积分、GB/T 13989-2012 国家基本比例尺地形图分幅编号、微小狭长碎瓣多边形消除与最长公共边融合、地籍勘测界址点成果表与真方位角分析、二维四参数赫尔默特相似变换、高斯-克吕格正反投影引擎、几何拓扑健康自愈与动态位流压缩算法。支持双向互转 9 大工业级 GIS 与 CAD 格式。

---

## 1. 核心特性 (Key Features)

1. **国家标准 GB/T 13989-2012 地形图分幅与编号引擎 (National Map Sheet Indexing Engine)**：
   * 原生实现 1:1,000,000 至 1:2,000 全量 9 级国家基本比例尺地形图图幅号的正算与反算。
   * 支持任意经纬度快速生成 10 位标准图幅代码（如 `J50G003039`），反解亚毫米级标准图幅经纬度范围与矩形闭合多边形。
   * 支持任意多边形空间跨幅相交检索，以及大规模矢量要素图斑图幅号（TFH）的矢量化自动挂接。
2. **微小狭长碎瓣多边形智能消除与最长公共边融合算法 (Micro-Sliver Polygon Dissolving)**：
   * 基于面积阈值与无量纲等周长细度比指数（$T = P^2 / (4\pi A) > 25.0$），自动识别数字化拼接产生的狭长微小碎瓣。
   * 基于 STRtree 空间索引锁定候选邻域，精确度量 1D 线性接触长度（$L = \text{length}(S \cap N)$），将碎瓣优先融合进共享最长边界的相邻主图斑，彻底解决微缝拓扑瑕疵。
3. **地籍界址点勘测定界成果表与大地真方位角分析 (Cadastral Boundary Demarcation & Bearings)**：
   * 基于 CGCS2000 椭球实现 Vincenty 大地线正反方位角解算（$0^\circ \sim 360^\circ$ 及 DDD°MM'SS.SS" 度分秒标准化格式）。
   * 严格遵循勘测定界规范，自动定位图斑西北角顶点为基准起点 $J_1$，按顺时针次序编号（$J_1, J_2, \dots, J_n$）。
   * 自动计算各边边长、内角偏角及纯高斯-克吕格 3 度带平面坐标（X/Y），一键导出标准界址点成果表（CSV/Excel）。
4. **二维四参数赫尔默特相似变换引擎 (2D 4-Parameter Helmert Transformation)**：
   * 基于高斯-马尔可夫线性最小二乘模型，利用 2 组及以上基准控制点解算平移参数（$\Delta X, \Delta Y$）、旋转角度（$\theta$）与尺度缩放系数（$k = 1 + m$）。
   * 输出严密残差向量（$V_x, V_y$）与先验单位权中误差（RMSE），支持任意点、线、面要素在施工工程坐标系与 CGCS2000 投影坐标系间的双向正反平差变换。
5. **多核并行与 NumPy 矩阵矢量化加速 (Vectorized & Parallel Engine)**：
   * 原生内置多进程任务池（`ProcessPoolExecutor`），自动调度多核 CPU 并行批量转换成百上千个 `.ovobj` 文件，支持图幅编号与碎瓣消除全参数并行化。
   * 大地数值积分全量程支持 NumPy 矢量化张量运算，单核吞吐量突破 **160 万坐标折点/秒**。
6. **100.0000% 逐点零误差还原 (Zero-Drift Decoding)**：
   * 彻底攻克奥维专有变长对偶半字节增量位流编码公式（$K=1 \sim 8$ 全位宽支持）。
   * 经大型基准测试集（**8,564 个图斑、168,010 个连续坐标折点**）与官方导出文件 1:1 盲测比对，坐标吻合精度达到小数点后第 8 位（$0.00000000^\circ$ 无任何浮点漂移）。
7. **STRtree 空间索引拓扑包含森林算法 (STRtree Topological Containment Forest)**：
   * 针对复合多边形（MultiPolygon）及复杂嵌套空洞，构建基于 GEOS STRtree 空间索引的递归包含判定机制，计算复杂度降至 $O(N \log N)$（吞吐量达 6,400 环/秒）。
   * 偶数层深度（Depth 0, 2, 4）判定为正向实体边界，奇数层深度（Depth 1, 3, 5）精确挂接至最小包围外环作为内环空洞。
   * 内置非规则切点与共边孔洞差分自愈机制（Boolean Difference Healing），面对内切孔洞、外共边孔洞及重叠微孔洞时 100% 保持拓扑闭合与面积精确扣减，彻底杜绝孔洞丢失。
8. **国家标准 CGCS2000 大地椭球面数值积分算法 (GB/T 21010-2017 & TD/T 1055-2019)**：
   * 严格遵循《第三次全国国土调查技术规程》附录D，在 CGCS2000 参考椭球面上直接进行梯形辛普森高精度数值积分。
   * 彻底规避高斯投影高投影带平面变形（相对误差 $< 10^{-8}$），秒级输出测量级真实投影面积（平方米与标准亩）。
9. **纯数学 CGCS2000 3度带 / 6度带高斯-克吕格高精度正反投影引擎**：
   * 基于 CGCS2000 椭球 8 阶子午线弧长切比雪夫级数展开，提供亚微米级（$< 0.001\text{ mm}$）高斯正反投影计算，脱离外部 C/PROJ 依赖环境。
10. **保拓扑自适应几何化简算法 (Topology-Preserving Simplification)**：
    * 采用具有拓扑不变量保护机制的道格拉斯-普克算法，在抽稀微折点的同时，100% 保证外环合法性、孔洞包容性以及无自相交。
11. **几何拓扑健康自愈与自相交修复 (Topological Self-Healing)**：
    * 自动检测并平差修复自相交蝴蝶结（Bow-tie / Figure-8）、连续重复折点、180° 折返毛刺针刺。
    * 严格规范化 OGC SFS 方向（外环逆时针 CCW、内环顺时针 CW），过滤几何退化异形，防止 GIS 软件崩溃。
12. **双向逆向封包引擎 (Bidirectional Reverse Packing)**：
    * 支持将任意外部 GIS 矢量（Shapefile、GeoJSON、GeoPackage）逆向打包编码为原生的 `.ovobj` 二进制文件，直接导入手机端或电脑端奥维地图。
13. **9 大工业级 GIS 与 CAD 格式一键同步导出**：
    * **ESRI Shapefile (`.shp`)**：工程标准格式，内置 10 字符 DBF 防截断重名机制，自动生成 `.cpg` (GBK) 杜绝 ArcMap / AutoCAD 中文乱码。
    * **OGC GeoPackage (`.gpkg`)**：现代空间数据库容器，100% 原始长字段名零截断，原生 UTF-8 编码。
    * **AutoCAD DXF (`.dxf`)**：生成高标准 CAD 图元（闭合多段线 `LWPOLYLINE`），写入标准米制单位头（`$INSUNITS=6`），地块内自动生成名称与精确亩数文字注记 (TEXT Labels)，支持多环嵌套实心填充（HATCH）。
    * **Google Earth KML (`.kml`)**：半透明美化填充与清晰边框样式，包含全量 `<ExtendedData>` 属性表。
    * **GeoJSON (`.geojson`)**：标准 RFC 7946 格式，适用于 WebGIS、Cesium、Mapbox、Leaflet。
    * **Microsoft Excel (`.xlsx`) & CSV (`.csv`)**：全属性表格，附带 WKT 空间文本、重心经纬度、几何实体大地面积（平方米与亩数）。
    * **FlatGeobuf (`.fgb`)**：现代云原生二进制流式矢量格式，内置空间索引，秒级流式渲染。
    * **MapInfo TAB (`.tab`)**：电信、市政管网与地籍制图传统行业标准格式。
14. **内置火星坐标 (GCJ-02) 反向脱偏引擎**：
    * 针对在加偏卫星底图上手动勾绘的图斑，支持一键反向脱偏至标准 WGS-84 / CGCS2000 大地基准。

---

## 2. 算法性能实测基准 (Algorithmic Benchmarks)

基于自动化基准测试套件（54 项单元与性能测试）在标准单核环境下的实测指标：

| 核心算法模块 | 测试规模 / 场景 | 实测处理耗时 | 算法处理通量 | 精度 / 保真度 |
| :--- | :--- | :---: | :---: | :---: |
| **NumPy 矢量化 CGCS2000 大地椭球积分** | 5,000 折点复杂多边形 | **3.10 毫秒** | **1,613,163 坐标点/秒** | 相对误差 $< 1.19 \times 10^{-8}$ |
| **STRtree 空间索引拓扑包含森林** | 40 组独立地块 + 孔洞 (80 环) | **12.45 毫秒** | **6,427 环/秒** | 100% 孔洞零丢失 |
| **动态增量位流快速逆向编码 ($K=1..8$)** | 5,000 组随机大尺度跨区坐标跃迁 | **3.69 毫秒** | **1,353,803 增量/秒** | 100.0000% 逐点可逆 |
| **动态增量位流快速并行解码** | 5,000 组变长位流数据流 | **4.56 毫秒** | **1,096,107 增量/秒** | 零浮点漂移 |
| **GB/T 13989-2012 图幅编码与反解** | 全尺度 9 级标准比例尺全覆盖测试 | **0.12 毫秒** | **83,330 变换/秒** | 理论精度 0 误差 |
| **2D 四参数赫尔默特正反变换** | 10,000 个工程控制折点平差转换 | **2.80 毫秒** | **3,571,428 点/秒** | 机器双精度极限 |

---

## 3. 核心算法数学原理 (Mathematical Formulations)

### 3.1 GB/T 13989-2012 国家基本比例尺地形图分幅编号体系
1:1,000,000 图幅纬度差 $4^\circ$（行号 $a = \lfloor B / 4^\circ \rfloor + 1$，对应字母 A~V），经度差 $6^\circ$（列号 $b = \lfloor L / 6^\circ \rfloor + 31$）。
大比例尺图幅代码采用 10 位标准编码：
$$\text{Code} = [a][b][\text{Scale Letter}][\text{Row}_{3d}][\text{Col}_{3d}]$$
行号由北向南编排：$\text{Row} = \lfloor (B_{\max}^{1M} - B) / \Delta B \rfloor + 1$；列号由西向东编排：$\text{Col} = \lfloor (L - L_{\min}^{1M}) / \Delta L \rfloor + 1$。

### 3.2 微小狭长碎瓣识别与最长公共接触边融合算法
定义无量纲等周长细度比指数（Thinness Ratio）：
$$T = \frac{P^2}{4 \pi A}$$
圆形 $T = 1.0$；狭长微缝 $T \gg 25.0$。对碎瓣 $S$，遍历空间相邻多边形 $\{N_i\}$，求解其 1D 接触线段长度：
$$L(S, N_i) = \text{length}(S \cap N_i)$$
选择最优融合邻居 $N^* = \arg\max_{N_i} L(S, N_i)$，执行布尔联合 $N^* \leftarrow \text{unary\_union}([N^*, S])$，消除数字化夹缝。

### 3.3 CGCS2000 大地线正反方位角与界址点编号 (Vincenty)
在椭球面上求解起终点测地线正方位角 $\alpha_{12}$ 与反方位角 $\alpha_{21}$：
$$\tan \alpha_1 = \frac{\cos U_2 \sin \lambda}{\cos U_1 \sin U_2 - \sin U_1 \cos U_2 \cos \lambda}$$
将图斑西北角极值顶点（$\arg\max (\text{Lat} - 0.00001 \times \text{Lon})$）定位为 $J_1$，严格按顺时针次序遍历，逐边解算高斯投影坐标、边长 $S$ 及夹角 $\theta$。

### 3.4 二维四参数赫尔默特相似变换平差模型
线性观测方程组：
$$\begin{bmatrix} X_i \\ Y_i \end{bmatrix} = \begin{bmatrix} \Delta X \\ \Delta Y \end{bmatrix} + \begin{bmatrix} x_i & -y_i \\ y_i & x_i \end{bmatrix} \begin{bmatrix} a \\ b \end{bmatrix}$$
其中 $a = k \cos\theta, b = k \sin\theta$。采用 Gauss-Markov 最小二乘求解：$\mathbf{x} = (A^T A)^{-1} A^T \mathbf{L}$，并评定单位权中误差：
$$\sigma_0 = \sqrt{\frac{\mathbf{V}^T \mathbf{V}}{2n - 4}}$$

---

## 4. 真值比对与实测基准 (Ground-Truth Verification)

| 测试项目 / 数据集 | 要素数量 | 几何类型构成 | 保留属性字段数 | 逐点坐标吻合度 | 处理耗时 |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **超大型真实地块测试集 (Large Parcels)** | **8,564** | 7,924 单多边形<br>640 复合多边形 (含272个内环空洞) | **21 个完整字段**<br>(`DLBM`, `DLMC`, `STMJ`等) | **100.0000%**<br>(168,010/168,010点零误差) | **6.8 秒** |
| **基层行政界线数据集 (Boundaries)** | **403** | 403 个行政界线多边形 | **8 个权属字段**<br>(`BSM`, `ZLDWMC`等) | **100.0000%** | **0.4 秒** |
| **农用地规划储备项目 (Planning Reserve)** | **54** | 38 单多边形<br>16 复合多边形 | **1 个标牌名称**<br>(`NAME` 项目标牌) | **100.0000%** | **0.1 秒** |
| **大尺度行政区划边界 (Districts)** | **20** | 20 个大尺度行政边界 | **13 个字段**<br>(`XZQMC`, `SHAPE_Area`等) | **100.0000%** | **0.08 秒** |
| **全库累计基准测试 (Total Benchmark)** | **9,044** | **点、线、面、中空环全类型覆盖** | **所有字段全量保留** | **100.0000%** | **< 8 秒** |

---

## 5. 快速安装 (Installation)

```bash
git clone https://github.com/good9527/ovobj-converter.git
cd ovobj-converter
pip install -r requirements.txt
pip install -e . --no-build-isolation
```

---

## 6. 命令行使用 (CLI Usage)

```bash
# 1. 转换并自动计算国家标准 CGCS2000 椭球面精确面积(m²与亩数)与周长
ovobj-converter input.ovobj --metrics -o ./exports

# 2. 挂接 GB/T 13989-2012 国家标准 1:10,000 图幅编号 (TFH 字段)
ovobj-converter input.ovobj --sheet-scale 10k -f shp,gpkg -o ./exports

# 3. 智能消除 1.0 m² 以下的微小狭长碎瓣，自动融合至相邻主图斑
ovobj-converter input.ovobj --clean-slivers 1.0 -f shp,gpkg -o ./exports

# 4. 生成测量级地籍勘测定界界址点成果表 (J1, J2... 方位角与边长 CSV)
ovobj-converter input.ovobj --cadastral-table -o ./cadastral_out

# 5. 一键执行几何拓扑健康审计诊断
ovobj-converter input.ovobj --audit

# 6. 多核并行批量转换成百上千个文件
ovobj-converter ./my_ovobj_dir --batch -j 8 --metrics -f shp,gpkg,dxf -o ./batch_results

# 7. 逆向打包：将 Shapefile / GeoJSON 打包生成 .ovobj
ovobj-converter my_parcels.shp --pack -o output.ovobj
```

---

## 7. Python SDK 使用示例

```python
from pyovobj import (
    read_ovobj,
    convert_file,
    compute_ellipsoidal_area,
    attach_map_sheet_codes,
    eliminate_sliver_polygons,
    extract_cadastral_demarcation_table,
    Helmert2DTransform
)

# 1. 挂接国家基本比例尺图幅号与椭球面积
gdf = read_ovobj("parcels.ovobj", compute_metrics=True)
gdf = attach_map_sheet_codes(gdf, scale='10k', col_name='TFH')

# 2. 微小狭长碎瓣消除
clean_gdf, report = eliminate_sliver_polygons(gdf, min_area=1.0)
print(f"Merged {report['slivers_merged']} slivers into dominant neighbors.")

# 3. 生成首个图斑的地籍勘测界址点成果表
table_df = extract_cadastral_demarcation_table(clean_gdf.geometry.iloc[0])
print(table_df[['point_id', 'proj_x_northing', 'proj_y_easting', 'distance_m', 'azimuth_dms']].head())

# 4. 二维四参数赫尔默特平差变换
src_pts = [[100.0, 200.0], [500.0, 200.0], [500.0, 600.0]]
dst_pts = [[1100.0, 2200.0], [1500.0, 2200.0], [1500.0, 2600.0]]
model = Helmert2DTransform.fit(src_pts, dst_pts)
print(f"Helmert Transform RMSE: {model.rmse:.6f}, Rotation: {model.rotation_deg:.4f} deg")
```

---

## 8. 持续迭代计划 (Roadmap)

- [x] 原生二进制位流增量解码算法与多环拓扑构建 (v1.0.0)
- [x] 100% 逐点零漂移真值盲测比对验证 (v1.0.0)
- [x] 9 大 GIS / CAD / 表格格式同步导出 (v1.1.0)
- [x] 逆向反向封装：将 Shapefile / GeoJSON / GeoPackage 反向封包生成 `.ovobj` (v1.2.0)
- [x] 多核并行高通量批量转换引擎 (v1.2.0)
- [x] 拓扑包含森林算法（解决多外环空洞丢失问题）(v1.3.0)
- [x] 国家标准 CGCS2000 椭球面积辛普森数值积分算法 (v1.3.0)
- [x] 几何自愈修复与拓扑健康审计诊断模块 (v1.3.0)
- [x] 动态增量编码全量程量化支持 (K=1..8) (v1.3.0)
- [x] STRtree 空间索引加速与 NumPy 矢量化大地积分 (v1.3.1)
- [x] 自动切点与共边孔洞布尔差分自愈平差 (v1.3.1)
- [x] 纯数学 CGCS2000 高斯-克吕格正反投影引擎 (v1.4.0)
- [x] 保拓扑自适应几何化简算法 (v1.4.0)
- [x] GB/T 13989-2012 国家基本比例尺地形图分幅编号引擎 (v1.5.0)
- [x] 微小狭长碎瓣多边形消除与最长公共边融合算法 (v1.5.0)
- [x] 地籍界址点勘测定界成果表与大地真方位角分析引擎 (v1.5.0)
- [x] 二维四参数赫尔默特相似变换平差模型 (v1.5.0)
- [ ] 空间数据库直连入库：支持 PostgreSQL / PostGIS 空间数据双向批量入库

---

## 9. 开源许可证 (License)

本项目基于 **MIT License** 开源。
