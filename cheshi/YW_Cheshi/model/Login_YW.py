from UserService.Login import Login

__author__ = 'Administrator'

class Login_YW(Login):
    YW_MerchantType=0

    def isavailable_return_YW(self):
        success=super(Login_YW,self).isavailable_return()
        if not success:
            return success
        else:
            return self.YW_MerchantType!=0


