import os.path

from osgeo import gdal, osr
import numpy as np
from PIL import Image, ImageQt
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QPointF, QRect
import imghdr


class GeoTiffItem(object):
    def __init__(self, fname):
        super().__init__()
        self.rgbRender = False
        self.bandNum = 0
        self.dataType = 0
        self.fileName = fname
        self.xSize = 0
        self.ySize = 0
        self.get_image_info()
        self.clipROI = QRect()

    def get_image_info(self):
        self.dataset = gdal.Open(self.fileName, gdal.GA_ReadOnly)
        self.bandNum = self.dataset.RasterCount
        self.xSize = self.dataset.RasterXSize
        self.ySize = self.dataset.RasterYSize
        self.geoTransform = self.dataset.GetGeoTransform()
        self.projection = self.dataset.GetProjection()
        if self.bandNum >= 3:
            self.rgbRender = True
        band1 = self.dataset.GetRasterBand(1)
        self.dataType = gdal.GetDataTypeName(band1.DataType)
        if self.dataType != 'Byte':
            self.convert_to_byte()

    def convert_to_byte(self):
        base_name = os.path.basename(self.fileName)
        output_file = base_name + '_8bit.tif'
        if len(output_file) and os.path.isfile(output_file) and imghdr.what(output_file) == 'tiff':
            self.fileName = output_file
            self.get_image_info()
            return
        band1 = self.dataset.GetRasterBand(1)
        band1.GetMetadata()
        if band1.GetMinimum() is None or band1.GetMaximum() is None:
            stats = band1.GetStatistics(True, True)
        max_val = band1.GetMaximum()
        min_val = band1.GetMinimum()
        options_str = {
            'format': 'GTiff',
            'outputType': gdal.GDT_Byte,
            'scaleParams': [min_val, max_val, 0, 255]
        }

        gdal.Translate(output_file, self.fileName, options=options_str)
        self.fileName = output_file
        self.get_image_info()
        return

    def get_image_byte(self, real_rect, show_rect):
        if self.rgbRender:
            band = [self.dataset.GetRasterBand(1), self.dataset.GetRasterBand(2), self.dataset.GetRasterBand(3)]
            list_band = []
            for index in range(len(band)):
                scanline = band[index].ReadRaster(xoff=real_rect.x(), yoff=real_rect.y(),
                                                  xsize=real_rect.width(), ysize=real_rect.height(),
                                                  buf_xsize=show_rect.width(), buf_ysize=show_rect.height(),
                                                  buf_type=gdal.GDT_Byte)
                img = Image.frombytes('L', (show_rect.width(), show_rect.height()), scanline, 'raw')
                list_band.append(img)
            img_rgb = Image.merge('RGB', list_band)
            img_rgba = img_rgb.convert("RGBA")
            pixmap = QPixmap.fromImage(ImageQt.ImageQt(img_rgba))
            return pixmap
        else:
            band1 = self.dataset.GetRasterBand(1)
            scanline = band1.ReadRaster(xoff=real_rect.x(), yoff=real_rect.y(),
                                        xsize=real_rect.width(), ysize=real_rect.height(),
                                        buf_xsize=show_rect.width(), buf_ysize=show_rect.height(),
                                        buf_type=gdal.GDT_Byte)
            img = Image.frombytes('L', (show_rect.width(), show_rect.height()), scanline, 'raw')
            pixmap = QPixmap.fromImage(ImageQt.ImageQt(img))
            return pixmap

    def getSRSPair(self):
        '''
        获得给定数据的投影参考系和地理参考系
        :param dataset: GDAL地理数据
        :return: 投影参考系和地理参考系
        '''
        prosrs = osr.SpatialReference()
        prosrs.ImportFromWkt(self.projection)
        geosrs = prosrs.CloneGeogCS()
        return prosrs, geosrs

    def geo2lonlat(self, point_geo):
        '''
        将投影坐标转为经纬度坐标（具体的投影坐标系由给定数据确定）
        :param dataset: GDAL地理数据
        :param x: 投影坐标x
        :param y: 投影坐标y
        :return: 投影坐标(x, y)对应的经纬度坐标(lon, lat)
        '''
        prosrs, geosrs = self.getSRSPair()
        ct = osr.CoordinateTransformation(prosrs, geosrs)
        x = point_geo.x()
        y = point_geo.y()
        coords = ct.TransformPoint(x, y)
        return coords[:2]

    def lonlat2geo(self, lon, lat):
        '''
        将经纬度坐标转为投影坐标（具体的投影坐标系由给定数据确定）
        :param dataset: GDAL地理数据
        :param lon: 地理坐标lon经度
        :param lat: 地理坐标lat纬度
        :return: 经纬度坐标(lon, lat)对应的投影坐标
        '''
        prosrs, geosrs = self.getSRSPair()
        ct = osr.CoordinateTransformation(geosrs, prosrs)
        coords = ct.TransformPoint(lon, lat)
        return coords[:2]

    def imagexy2geo(self, point_img):
        '''
        根据GDAL的六参数模型将影像图上坐标（行列号）转为投影坐标或地理坐标（根据具体数据的坐标系统转换）
        :param point_img:
        :param dataset: GDAL地理数据
        :param row: 像素的行号
        :param col: 像素的列号
        :return: 行列号(row, col)对应的投影坐标或地理坐标(x, y)
        '''
        trans = self.geoTransform
        point_geo = QPointF()
        point_geo.setX(trans[0] + point_img.x() * trans[1] + point_img.y() * trans[2])
        point_geo.setY(trans[3] + point_img.x() * trans[4] + point_img.y() * trans[5])
        return point_geo

    def geo2imagexy(self, x, y):
        '''
        根据GDAL的六 参数模型将给定的投影或地理坐标转为影像图上坐标（行列号）
        :param dataset: GDAL地理数据
        :param x: 投影或地理坐标x
        :param y: 投影或地理坐标y
        :return: 影坐标或地理坐标(x, y)对应的影像图上行列号(row, col)
        '''
        trans = self.dataset.GetGeoTransform()
        a = np.array([[trans[1], trans[2]], [trans[4], trans[5]]])
        b = np.array([x - trans[0], y - trans[3]])
        return np.linalg.solve(a, b)  # 使用numpy的linalg.solve进行二元一次方程的求解

    def captureROI(self, lon, lat, block_xsize=2000, block_ysize=2000):
        print('经纬度 -> 投影坐标：')
        coords = self.lonlat2geo(lon, lat)
        print('(%s, %s)->(%s, %s)' % (lon, lat, coords[0], coords[1]))

        x, y = coords[0], coords[1]

        print('投影坐标 -> 图上坐标：')
        coords = self.geo2imagexy(x, y)
        print('(%s, %s)->(%s, %s)' % (x, y, coords[0], coords[1]))

        offset_x, offset_y = coords[0] - block_xsize / 2, coords[1] - block_ysize / 2
        self.clipROI = QRect(offset_x, offset_y, block_xsize, block_ysize)

        print(offset_x, offset_y)

        in_band1 = self.dataset.GetRasterBand(1)
        in_band2 = self.dataset.GetRasterBand(2)
        in_band3 = self.dataset.GetRasterBand(3)

        # 从每个波段中切需要的矩形框内的数据(注意读取的矩形框不能超过原图大小)
        out_band1 = in_band1.ReadAsArray(offset_x, offset_y, block_xsize, block_ysize)
        out_band2 = in_band2.ReadAsArray(offset_x, offset_y, block_xsize, block_ysize)
        out_band3 = in_band3.ReadAsArray(offset_x, offset_y, block_xsize, block_ysize)

        # 获取Tif的驱动，为创建切出来的图文件做准备
        gtif_driver = gdal.GetDriverByName("GTiff")

        # 创建切出来的要存的文件（3代表3个不都按，最后一个参数为数据类型，跟原文件一致）
        out_ds = gtif_driver.Create('clip.tif', block_xsize, block_ysize, 3, in_band1.DataType)
        print("create new tif file succeed")

        # 获取原图的原点坐标信息
        ori_transform = self.dataset.GetGeoTransform()
        if ori_transform:
            print(ori_transform)
            print("Origin = ({}, {})".format(ori_transform[0], ori_transform[3]))
            print("Pixel Size = ({}, {})".format(ori_transform[1], ori_transform[5]))

        # 读取原图仿射变换参数值
        top_left_x = ori_transform[0]  # 左上角x坐标
        w_e_pixel_resolution = ori_transform[1]  # 东西方向像素分辨率
        top_left_y = ori_transform[3]  # 左上角y坐标
        n_s_pixel_resolution = ori_transform[5]  # 南北方向像素分辨率

        # 根据反射变换参数计算新图的原点坐标
        top_left_x = top_left_x + offset_x * w_e_pixel_resolution
        top_left_y = top_left_y + offset_y * n_s_pixel_resolution

        # 将计算后的值组装为一个元组，以方便设置
        dst_transform = (top_left_x, ori_transform[1], ori_transform[2], top_left_y, ori_transform[4], ori_transform[5])

        # 设置裁剪出来图的原点坐标
        out_ds.SetGeoTransform(dst_transform)

        # 设置SRS属性（投影信息）
        out_ds.SetProjection(self.dataset.GetProjection())

        # 写入目标文件
        out_ds.GetRasterBand(1).WriteArray(out_band1)
        out_ds.GetRasterBand(2).WriteArray(out_band2)
        out_ds.GetRasterBand(3).WriteArray(out_band3)

        print(type(out_ds))


