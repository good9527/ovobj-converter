# -*- coding: utf-8 -*-
"""
pyovobj.core.transform
----------------------
2D 4-Parameter Helmert Similarity Transformation Engine.
Provides least-squares parameter estimation, residual analysis, standard error of unit weight (RMSE),
and forward/inverse coordinate and geometry transformations between local construction grids and
projected coordinate systems (e.g., local mine/engineering grids to CGCS2000 Gauss-Kruger).
"""

import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform as shapely_transform

class Helmert2DTransform:
    """
    2D 4-Parameter Helmert Similarity Transformation model:
    [X]   [dX]               [cos(theta)  -sin(theta)] [x]
    [ ] = [  ] + (1 + m) *   [                       ] [ ]
    [Y]   [dY]               [sin(theta)   cos(theta)] [y]
    """

    def __init__(
        self,
        dx: float = 0.0,
        dy: float = 0.0,
        scale_k: float = 1.0,
        rotation_deg: float = 0.0,
        rmse: float = 0.0
    ):
        self.dx = float(dx)
        self.dy = float(dy)
        self.scale_k = float(scale_k)
        self.scale_m = float(scale_k - 1.0)
        self.rotation_deg = float(rotation_deg)
        self.rotation_rad = math.radians(self.rotation_deg)
        self.rmse = float(rmse)

        # Precompute transformation matrix elements
        self._a = self.scale_k * math.cos(self.rotation_rad)
        self._b = self.scale_k * math.sin(self.rotation_rad)

    @classmethod
    def fit(
        cls,
        source_points: Union[np.ndarray, List[Tuple[float, float]]],
        target_points: Union[np.ndarray, List[Tuple[float, float]]]
    ) -> "Helmert2DTransform":
        """
        Estimates the 4 transformation parameters from 2 or more control point pairs
        using Gauss-Markov linear least squares.

        :param source_points: Nx2 array of (x, y) coordinates in source system.
        :param target_points: Nx2 array of (X, Y) coordinates in target system.
        :return: Fitted Helmert2DTransform instance.
        """
        src = np.asarray(source_points, dtype=np.float64)
        dst = np.asarray(target_points, dtype=np.float64)

        if len(src) != len(dst):
            raise ValueError(f"Point count mismatch: {len(src)} source vs {len(dst)} target.")
        n = len(src)
        if n < 2:
            raise ValueError(f"At least 2 control point pairs are required (got {n}).")

        # Construct design matrix A and observation vector L
        A = np.zeros((2 * n, 4), dtype=np.float64)
        L = np.zeros(2 * n, dtype=np.float64)

        for i in range(n):
            x, y = src[i]
            X, Y = dst[i]
            A[2 * i]     = [1.0, 0.0, x, -y]
            A[2 * i + 1] = [0.0, 1.0, y,  x]
            L[2 * i]     = X
            L[2 * i + 1] = Y

        # Solve normal equations: (A^T A) x = A^T L
        params, residuals, rank, s = np.linalg.lstsq(A, L, rcond=None)
        dx, dy, a, b = params

        scale_k = math.hypot(a, b)
        rot_rad = math.atan2(b, a)
        rot_deg = math.degrees(rot_rad)

        # Compute residuals and standard error of unit weight
        V = A @ params - L
        dof = 2 * n - 4
        rmse = float(np.sqrt(np.sum(V ** 2) / dof)) if dof > 0 else 0.0

        inst = cls(dx=dx, dy=dy, scale_k=scale_k, rotation_deg=rot_deg, rmse=rmse)
        inst.residuals = V
        return inst

    def transform_coords(self, coords: Union[np.ndarray, List[Tuple[float, float]]]) -> np.ndarray:
        """
        Transforms coordinates from source system to target system.

        :param coords: Nx2 array of (x, y) coordinates.
        :return: Nx2 array of transformed (X, Y) coordinates.
        """
        arr = np.asarray(coords, dtype=np.float64)
        if arr.ndim == 1:
            arr = arr.reshape(1, 2)
        x = arr[:, 0]
        y = arr[:, 1]
        X = self.dx + self._a * x - self._b * y
        Y = self.dy + self._b * x + self._a * y
        return np.column_stack([X, Y])

    def inverse_coords(self, coords: Union[np.ndarray, List[Tuple[float, float]]]) -> np.ndarray:
        """
        Performs exact inverse transformation from target system back to source system.

        :param coords: Nx2 array of (X, Y) coordinates.
        :return: Nx2 array of (x, y) coordinates in source system.
        """
        arr = np.asarray(coords, dtype=np.float64)
        if arr.ndim == 1:
            arr = arr.reshape(1, 2)
        X = arr[:, 0] - self.dx
        Y = arr[:, 1] - self.dy
        denom = self._a * self._a + self._b * self._b
        if denom == 0.0:
            raise ZeroDivisionError("Degenerate transformation with zero scale.")
        x = (self._a * X + self._b * Y) / denom
        y = (-self._b * X + self._a * Y) / denom
        return np.column_stack([x, y])

    def transform_geometry(self, geom: BaseGeometry) -> BaseGeometry:
        """
        Transforms any Shapely geometry from source system to target system.
        """
        if geom is None or geom.is_empty:
            return geom

        def _forward_fn(x, y, z=None):
            x_arr = np.asarray(x, dtype=np.float64)
            y_arr = np.asarray(y, dtype=np.float64)
            X = self.dx + self._a * x_arr - self._b * y_arr
            Y = self.dy + self._b * x_arr + self._a * y_arr
            if z is not None:
                return X, Y, z
            return X, Y

        return shapely_transform(_forward_fn, geom)

    def inverse_geometry(self, geom: BaseGeometry) -> BaseGeometry:
        """
        Inverse-transforms any Shapely geometry from target system back to source system.
        """
        if geom is None or geom.is_empty:
            return geom

        denom = self._a * self._a + self._b * self._b
        if denom == 0.0:
            raise ZeroDivisionError("Degenerate transformation with zero scale.")

        def _inverse_fn(X, Y, z=None):
            X_arr = np.asarray(X, dtype=np.float64) - self.dx
            Y_arr = np.asarray(Y, dtype=np.float64) - self.dy
            x = (self._a * X_arr + self._b * Y_arr) / denom
            y = (-self._b * X_arr + self._a * Y_arr) / denom
            if z is not None:
                return x, y, z
            return x, y

        return shapely_transform(_inverse_fn, geom)

    def transform_geodataframe(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Transforms all geometries in a GeoDataFrame from source system to target system.
        """
        if gdf.empty:
            return gdf
        df_out = gdf.copy()
        df_out['geometry'] = [self.transform_geometry(g) for g in df_out.geometry]
        return df_out

    def to_dict(self) -> Dict[str, float]:
        """Returns transformation parameter summary dictionary."""
        return {
            'dx': self.dx,
            'dy': self.dy,
            'scale_k': self.scale_k,
            'scale_m': self.scale_m,
            'rotation_deg': self.rotation_deg,
            'rmse': self.rmse
        }
