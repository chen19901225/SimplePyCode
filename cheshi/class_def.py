#coding:utf-8
__author__ = 'Administrator'
import os

def class_path_join(one,two):
    l_one,l_two=one,two
    l_one,l_two=l_one.strip(),l_two.strip()
    if l_one[-1]=='.':
        l_one=l_one[:-1]
    if l_two[0]!='.':
        l_two='.'+l_two
    return l_one+l_two

BASE_DIR=os.path.dirname(__name__)
YW_Cheshi_Base='YW_Cheshi'
Login_YW_path=class_path_join(YW_Cheshi_Base,'model.Login_YW.Login_YW')
TB_User_Class_Name="UserService.UrlHelper.UserDataHelper.TB_User"

TB_MenuLabel_Name=class_path_join(YW_Cheshi_Base,'model.TB_MenuLabel.TB_MenuLabel')

Cls_Food_Name=class_path_join(YW_Cheshi_Base,'model.Food.Food')
Cls_DeliveryAddress=class_path_join(YW_Cheshi_Base,'model.DeliveryAddress.DeliveryAddress')#送餐地址


YW_URL_Base="http://localhost:36648"

base_deliveryaddress_url="""%s/YouWeiDeliveryAddress/DeliveryAddress.ashx"""%(YW_URL_Base)