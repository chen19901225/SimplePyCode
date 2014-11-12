#!/usr/bin/env python
# encoding: utf-8

"""
    商圈投放
"""

from __future__ import division
from functools import partial
import math

from wtforms import (
    StringField, SelectMultipleField,
    validators as V
)

from base.frontend.common import Form
from base.utils import bulk_up, object_id, safe_str, true_or_raise
from model.data.definition import PropertyTradingArea, BusinessCircle


def transform_formdata_trading_area_by_request(forms):
    d = {}
    d["name"] = forms.get("name").strip()
    coords = forms.get("coordinate", "").strip()[1:-1].split("],[")
    fn_split = lambda x: tuple(map(float, x.split(",")))
    d["coordinates"] = map(fn_split, coords)
    d["province"] = safe_str(forms.get("province"))
    d["city"] = safe_str(forms.get("city"))
    return d


def create_trading_area(name, coordinates, province=None, city=None, **kwargs):
    d = PropertyTradingArea()
    d["name"] = name
    d["coordinates"] = coordinates
    d["province"] = province
    d["city"] = city
    if kwargs.get("persist", True):
        d.save()
    clean_cache()
    return d

def update_trading_area_by_id(_id, name, coordinates, province=None, city=None, **kwargs):
    d = {}
    d["name"] = name
    d["coordinates"] = coordinates
    d["province"] = province
    d["city"] = city
    if kwargs.get("persist", True):
        PropertyTradingArea().update({"_id":object_id(_id)}, {"$set": d})
    clean_cache()
    return d


RUNTIME_CACHE=[]
AREAS_CITY_CACHE=[]

def fill_cache():
    if not globals()["RUNTIME_CACHE"]:
        globals()["RUNTIME_CACHE"] = list(PropertyTradingArea.query(fields={"coordinates": 1, "name": 1, "province": 1, "city": 1,}))

def areas_city_cache():
    if not globals()["AREAS_CITY_CACHE"]:
        areas = find_all_trading_areas()
        provinces = []
        provinces_and_citys = []
        for area in areas:
            if "province" in area:
                if area["province"] not in provinces: 
                    provinces.append(area["province"])
                    provinces_and_citys.append([area["province"],[]])
            if "city" in area:
                for i in provinces_and_citys:
                    if area["province"] == i[0]:
                        if area["city"] not in i[1]:
                            i[1].append(area["city"])  
                        break
        provinces_and_citys.sort(key=lambda x: len(x[0]))
        for i in provinces_and_citys:
            i[1].sort(key=len)
        globals()["AREAS_CITY_CACHE"] =  provinces_and_citys

def clean_cache():
    globals()["RUNTIME_CACHE"] = []
    globals()["AREAS_CITY_CACHE"] = []

def find_trading_areas_province_and_city_group():
    areas_city_cache()
    return AREAS_CITY_CACHE

def find_all_trading_areas():
    fill_cache()
    return RUNTIME_CACHE

def find_all_trading_areas_by_query(query=None):
    return list(PropertyTradingArea.query(query,fields={"coordinates": 1, "name": 1, "province": 1, "city": 1,}))

def remove_trading_area_by_id(_id):
    PropertyTradingArea.remove(_id=object_id(_id))
    clean_cache()


@bulk_up
def trading_area_transform_compat(lst):
    nlst = []
    for d in lst:
        if "coordinates" in d:
            coord = map(lambda x: "[%s,%s]" % (x[0], x[1]), d["coordinates"])
            d["coordinate"] = ",".join(coord)
        nlst.append(d)
    return nlst

def get_trading_area_by_id(_id):
    return find_all_trading_areas_by_query({"_id":object_id(_id)});

def get_trading_areas_by_point(point):
    """ `point` must in (longitude, latitude)
    """
    fill_cache()
    return filter(lambda r: point_inside_polygon(point, r["coordinates"]),
                  RUNTIME_CACHE)



class TradingAreaForm(Form):
    id = StringField()
    province = StringField()
    city = StringField()
    name = StringField(u"商圈名称", [
        V.InputRequired(u"商圈名称不能为空。"),
        V.Length(2, 50, u"商圈名称应该在 2 - 50 个字符之间。"),
        lambda __, f: true_or_raise(not has_name_the_only(**__.populate_dict()),
                                    partial(V.ValidationError, u"商圈名称名称已被使用。"))
    ])

def has_name_the_only(name, id=None, province=None, city=None, **kwargs):
    print "has_name_the_only"
    query = {"name": name}
    if id:
        query["_id"] = {"$ne": object_id(id)}
    if province:
        query["province"] = province
    if city:
        query["city"] = city
    print query

    return PropertyTradingArea.exists(query)


# @see http://www.ariel.com.au/a/python-point-int-poly.html
def point_inside_polygon(point, poly, intersect=True):
    point = map(float, point)
    poly = map(lambda x: (float(x[0]), float(x[1])), poly)
    if type(point) is not tuple:
        point = tuple(point)
    if intersect and point in poly:
        return True
    n, inside, (x, y) = len(poly), 0, point
    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if p1x == p2x or x <= xinters:
                inside ^= 1
        p1x, p1y = p2x, p2y
    return (inside == 1)


def migrate_business_circle():
    lst = []
    circle = list(BusinessCircle.query())
    for rec in circle:
        d = transform_formdata_trading_area_by_request({"name": rec["name"], "coordinate": rec["coordinate"]})
        d["persist"] = False
        lst.append(create_trading_area(**d))
    PropertyTradingArea().collection.insert(lst)
