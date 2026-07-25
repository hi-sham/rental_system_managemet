from django.forms import ModelForm
from .models import Property
from .models import Payment
from .models import Booking
from .models import Location
from .models import Tenant
from .models import landlord
from .models import broker
from .models import MaintenanceRequest
from.models import Complaint 
from .models import Unit
from .models import Notification

class PropertyForm(ModelForm):
  class Meta:
    model = Property
    fields = '__all__'



class PaymentForm(ModelForm):
  class Meta:
    model =Payment
    fields ='__all__'   



class BookingForm(ModelForm):
  class Meta:
     model = Booking
     fields = '__all__'    


class LocationForm(ModelForm):
  class Meta:
     model = Location
     fields ='__all__'        


class landlordForm(ModelForm):
  class Meta:
      model = landlord
      fields ='__all__' 


class brokerForm(ModelForm):
  class Meta:
      model = broker
      fields ='__all__'  

class TenantForm(ModelForm):
  class Meta:
    model = Tenant
    fields ='__all__'


class MaintenanceRequestForm(ModelForm):
  class Meta:
    model = MaintenanceRequest 
    fields = '__all__'  


class ComplaintForm(ModelForm):
    class Meta:
        model = Complaint
        fields = '__all__'


class UnitForm(ModelForm):
  class Meta:
    model = Unit
    fields ='__all__'        

class NotificationForm(ModelForm):
  class Meta:
    model = Notification
    fields ='__all__'
  
