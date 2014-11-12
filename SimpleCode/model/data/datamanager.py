from base.backend.model.datamanager import *
from model.data.definition import *


class ManagerUserProfile(DataManagerBase):
    data_class = UserProfile

class ManagerUserType(DataManagerBase):
    data_class = UserType
    pass

class ManagerUser(DataManagerBase):
    data_class = User

    def get_by_id(self, id):
        return DataManagerBase.get_by_id(self, id, fields={"pending_transactions": False})

class ManagerTeam(DataManagerBase):
    data_class = Team

class ManagerUserVerificationType(DataManagerBase):
    data_class = UserVerificationType

class ManagerUserVerification(DataManagerBase):
    data_class = UserVerification

class ManagerAdvertStatus(DataManagerBase):
    data_class = AdvertStatus

class ManagerAppStatus(DataManagerBase):
    data_class = AppStatus

class ManagerPropertyGender(DataManagerBase):
    data_class = PropertyGender

class ManagerPropertyAge(DataManagerBase):
    data_class = PropertyAge

class ManagerPropertyCareer(DataManagerBase):
    data_class = PropertyCareer

class ManagerApp(DataManagerBase):
    data_class = App

class ManagerAdvert(DataManagerBase):
    data_class = Advert
    pass

class ManagerAdvertContent(DataManagerBase):
    data_class = AdvertContent
    pass

class ManagerAdvertTag(DataManagerBase):
    data_class = AdvertTag
    pass

class ManagerTimeRange(DataManagerBase):
    data_class = TimeRange

class ManagerBudgetType(DataManagerBase):
    data_class = BudgetType
    pass

class ManagerMediaType(DataManagerBase):
    data_class = MediaType
    pass

class ManagerPaymentType(DataManagerBase):
    data_class = PaymentType
    pass

class ManagerTrackLogType(DataManagerBase):
    data_class = TrackLogType
    pass

class ManagerTrackLog(DataManagerBase):
    data_class = TrackLog
    pass

class ManagerAdvertReportLog(DataManagerBase):
    data_class = ReportAdvertLog

class ManagerAppReportLog(DataManagerBase):
    data_class = ReportAppLog
class ManagerAppReportLogDownloadLog(DataManagerBase):
    data_class = ReportAppLogDownloadLog

class ManagerCategory(DataManagerBase):
    data_class = Category
    pass

class ManagerUserStatus(DataManagerBase):
    data_class = UserStatus

class ManagerRegionLaunch(DataManagerBase):
    data_class = RegionLaunch

class ManagerPlatform(DataManagerBase):
    data_class = Platform

class ManagerMediaType(DataManagerBase):
    data_class = MediaType

class ManagerTimeRange(DataManagerBase):
    data_class = TimeRange

class ManagerRegionLaunch(DataManagerBase):
    data_class = RegionLaunch

class ManagerBudget(DataManagerBase):
    data_class = Budget

class ManagerBudgetType(DataManagerBase):
    data_class = BudgetType

class ManagerApplicationLanguage(DataManagerBase):
    data_class = ApplicationLanguage

class ManagerApplicationType(DataManagerBase):
    data_class = ApplicationType

class ManagerBrandMobile(DataManagerBase):
    data_class = BrandMobile

class ManagerCarrier(DataManagerBase):
    data_class = Carrier

class ManagerShowType(DataManagerBase):
    data_class = ShowType

class ManagerAppUploadInfo(DataManagerBase):
    data_class = AppUploadInfo


class ManagerAdvertLevel(DataManagerBase):
    data_class = AdvertLevel

class ManagerAdvertLevelLog(DataManagerBase):
    data_class = AdvertLevelLog


class ManagerRegionDatabase(DataManagerBase):
    data_class = RegionDatabase

class ManagerIPDatabase(DataManagerBase):
    data_class = IPDatabase



class ManagerFinanceLogSource(DataManagerBase):
    data_class = FinanceLogSource

class ManagerFinanceLogStatus(DataManagerBase):
    data_class = FinanceLogStatus

class ManagerFinanceLogOperation(DataManagerBase):
    data_class = FinanceLogOperation

class ManagerFinanceLog(DataManagerBase):
    data_class = FinanceLog


class ManagerBusinessCircle(DataManagerBase):
    data_class = BusinessCircle

class ManagerVerificationMessage(DataManagerBase):
    data_class = VerificationMessage

class ManagerPrivilege(DataManagerBase):
    data_class = Privilege

class ManagerGroup(DataManagerBase):
    data_class = Group

class ManagerPropertyTradingArea(DataManagerBase):
    data_class = PropertyTradingArea

class ManagerReportPlatformLog(DataManagerBase):
    data_class = ReportPlatformLog

class ManagerPasswordReset(DataManagerBase):
    data_class = PasswordReset

class ManagerTransation(DataManagerBase):
    data_class = Transaction
