from django.shortcuts import render
from rentalapp.forms import PropertyForm
from rentalapp.models import Property
from rentalapp.forms import PaymentForm
from rentalapp.models import Payment
from rentalapp.forms import BookingForm
from rentalapp.models import Booking
from rentalapp.forms import LocationForm
from rentalapp.models import Location
from rentalapp.forms import landlordForm
from rentalapp.models import landlord
from rentalapp.forms import brokerForm
from rentalapp.models import broker
from rentalapp.forms import TenantForm
from rentalapp.models import Tenant
from rentalapp.forms import MaintenanceRequestForm
from rentalapp.models import MaintenanceRequest
from rentalapp.forms import ComplaintForm
from rentalapp.models import Complaint
from rentalapp.forms import UnitForm
from rentalapp.models import Unit
from rentalapp.forms import NotificationForm
from rentalapp.models import Notification

# Create your views here.
def login_view(request):
  return render(request,'index.html')

# def tentents_view(request):
#     return render(request,'tentents.html')

# def booking_view(request):
#     return render(request,'booking.html')  

# def location_view(request):
#     return render(request,'location.html')

# def payment_view(request):
#     return render(request,'payment.html') 

# def broker_view(request):
#     return render(request,'broker.html')  

# def landloard_view(request):
#     return render(request,'landloard.html')  



from django.shortcuts import get_object_or_404, render, redirect
from .forms import PropertyForm
from .models import Property

def add_property_view(request):
    if request.method == "POST":
        form = PropertyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_property_page')
    else:
        form = PropertyForm()

    property = Property.objects.all()

    context = {
        'form': form,
        'property': property,
    }

    return render(request, 'add_propertyform.html', context)

def edit_property_view(request,id):
    property = get_object_or_404(Property, pk=id)
    if request.method == "POST":
        form = PropertyForm(request.POST, instance=property)
        if form.is_valid():
            form.save()
            return redirect('add_property_page')
    else:
        form = PropertyForm(instance=property)

    context ={
        "form":form,
        "property":property
    }
    return render (request, 'edits/edit_property.html',context)

def delete_property_view(request, id):
    property = get_object_or_404(Property, pk=id)
    property.delete()
    return redirect('add_property_page') 






















def add_Payment_view(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            # return redirect('payment')   # Use your URL name here
    else:
        form = PaymentForm()
    payment = Payment.objects.all() 

    context ={
        'form':form,
        'payments':payment,
    }   

    return render(request, 'add_Paymentform.html',context)


   

def edit_Payment_view(request, id):
    payment = get_object_or_404(Payment, pk=id)

    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect('add_Payment_page')
    else:
        form = PaymentForm(instance=payment)

    context = {
        "form": form,
        "payment": payment,
    }
    return render(request, "edits/edit_Payment.html", context)

def delete_Payment_view(request, id):
    payment = get_object_or_404(Payment, pk=id)
    payment.delete()
    return redirect('add_Payment_page')   
   
def add_Booking_view(request):
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            # return redirect('booking')
         
    else:
        form = BookingForm()     # Create an empty form for GET requests

    booking = Booking.objects.all()

    context = {
        'form': form,
        'booking': booking,
    }

    return render(request, 'add_Bookingform.html', context)  

def edit_Booking_view(request, id):
    booking = get_object_or_404(Booking, pk=id)

    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return redirect('add_Booking_page')
    else:
        form = BookingForm(instance=booking)

    context = {
        "form": form,
        "booking": booking,
    }
    return render(request, "edits/edit_Booking.html", context) 

def delete_booking_view(request, id):
    booking = get_object_or_404(Booking, pk=id)
    booking.delete()
    return redirect('add_booking_page')       




def add_Location_view(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
           # return redirect('Location')   # Make sure this URL name exists
    else:
        form = LocationForm()
    locations =Location.objects.all()
    context ={'form':form,
         'locations':locations,
        }
    return render(request, 'add_Locationform.html', context)

def edit_Location_view(request, id):
    location = get_object_or_404(Location, pk=id)

    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect('add_Location_page')
    else:
        form = LocationForm(instance=location)

    context = {
        "form": form,
        "location": location,
    }
    return render(request, "edits/edit_Location.html", context)

def delete_location_view(request, id):
    location = get_object_or_404(Location, pk=id)
    location.delete()
    return redirect('add_Location_page')            


def add_broker_view(request):
    if request.method == "POST":
        form = brokerForm(request.POST)
        if form.is_valid():
            form.save()
           # return redirect('broker')   # Change to your booking list URL
    else:
        form = brokerForm()

    brokers = broker.objects.all()
    context ={'form':form,
            'brokers':brokers, 
            }

    return render(request, 'add_brokerform.html', context) 

def edit_broker_view(request, id):
    broker = get_object_or_404(broker, pk=id)

    if request.method == "POST":
        form = brokerForm(request.POST, instance=broker)
        if form.is_valid():
            form.save()
            return redirect('add_broker_page')
    else:
        form = brokerForm(instance=broker)

    context = {
        "form": form,
        "broker": broker_,
    }

    return render(request, "edits/edit_broker.html", context) 
def delete_broker_view(request, id):
    brokers = get_object_or_404(broker, pk=id)
    brokers.delete()
    return redirect('add_broker_page')       



def add_landlord_view(request):
    if request.method == "POST":
        form = landlordForm(request.POST)
        if form.is_valid():
            form.save()
           # return redirect('landlord')   # Ensure this URL name exists
    else:
        form = landlordForm()
    landlords =landlord.objects.all()
    context={'form':form,
        'landlords':landlords,

    }

    return render(request, 'add_landlordform.html', context)

def edit_landlord_view(request, id):
    landlords = get_object_or_404(landlord, pk=id)

    if request.method == "POST":
        form = landlordForm(request.POST, instance=landlord)

        if form.is_valid():
            form.save()
            return redirect('landlord_page')

    else:
        form = landlordForm(instance=landlord_record)

    context = {
        "form": form,
        "landlord": landlord_record,
    }

    return render(request, "edits/edit_landlord.html", context)

def delete_landlord_view(request, id):
    landlords = get_object_or_404(landlord, pk=id)
    landlords.delete()
    return redirect('add_landlord_page')


def add_Tenant_view(request):
    if request.method == "POST":
        form = TenantForm(request.POST)
        if form.is_valid():
            form.save()
            #return redirect('Tenant')   # Make sure this URL name exists
    else:
        form = TenantForm()
    tenant =Tenant.objects.all()

    context ={
        'form':form,
        'tenants':tenant,}

    return render(request, 'add_Tenantform.html', context) 

def edit_Tenant_view(request, id):
    tenant = get_object_or_404(Tenant, pk=id)

    if request.method == "POST":
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            return redirect('add_Tenant_page')
    else:
        form = TenantForm(instance=tenant)

    context = {
        "form": form,
        "tenant": tenant,
    }
    return render(request, "edits/edit_Tenant.html", context) 
def delete_tenant_view(request, id):
    tenant = get_object_or_404(Tenant, pk=id)
    tenant.delete()
    return redirect('add_Tenant')       




def add_MaintenanceRequest_view(request):
    if request.method == "POST":
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            form.save()
            #return redirect('MaintenanceRequest')   # Make sure this URL name exists
    else:
        form = MaintenanceRequestForm()

    maintenance_requests = MaintenanceRequest.objects.all()

    context = {
        "form": form,
        "maintenance_requests": maintenance_requests,
    }

    return render(request, 'add_MaintenanceRequestform.html', context)



def edit_MaintenanceRequest_view(request, id):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=id)

    if request.method == "POST":
        form = MaintenanceRequestForm(request.POST, instance=maintenance_request)

        if form.is_valid():
            form.save()
            return redirect('add_MaintenanceRequest_page')

    else:
        form = MaintenanceRequestForm(instance=maintenance_request)

    context = {
        "form": form,
        "maintenance_request": maintenance_request,
    }

    return render(request, 'edits/edit_MaintenanceRequest.html', context)
def delete_MaintenanceRequest_view(request, id):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=id)
    maintenance_request.delete()
    return redirect('add_maintenance_request_page')    
    


def add_complaint_view(request):

    if request.method == "POST":
        form = ComplaintForm(request.POST)

        if form.is_valid():
            form.save()

    else:
        form = ComplaintForm()

    complaints = Complaint.objects.all()

    context = {
        'form': form,
        'complaints': complaints,
    }

    return render(request, 'add_Complaintform.html', context)


def edit_Complaint_view(request, id):
    complaint = get_object_or_404(Complaint, pk=id)

    if request.method == "POST":
        form = ComplaintForm(request.POST, instance=complaint)
        if form.is_valid():
            form.save()
            return redirect('add_Complaint_page')
    else:
        form =ComplaintForm(instance=complaint)

    context = {
        "form": form,
        "complaint": complaint,
    }
    return render(request, "edits/edit_Complaint.html", context)

def delete_complaint_view(request, id):
    complaint = get_object_or_404(Complaint, pk=id)
    complaint.delete()
    return redirect('add_complaint_page')     
    


def add_Unit_view(request):
    if request.method == "POST":
        form = UnitForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = UnitForm()

    units = Unit.objects.all()

    context = {
        'form': form,
        'units': units,
    }

    return render(request, 'add_Unitform.html', context) 




def edit_Unit_view(request, id):
    unit = get_object_or_404(Unit, pk=id)

    if request.method == "POST":
        form = UnitForm(request.POST, instance=unit)

        if form.is_valid():
            form.save()
            return redirect('add_Unit_page')

    else:
        form = UnitForm(instance=unit)

    context = {
        'form': form,
        'unit': unit,
    }

    return render(request, 'edits/edit_Unit.html', context)
def delete_unit_view(request, id):
    unit = get_object_or_404(Unit, pk=id)
    unit.delete()
    return redirect('add_Unit_page')







def add_Notification_view(request):
    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_Notification_page')
    else:
        form = NotificationForm()

    notifications = Notification.objects.all()

    context = {
        'form': form,
        'notifications': notifications,
    }

    return render(request, 'add_Notificationform.html', context)       


def edit_Notification_view(request, id):
    notification = get_object_or_404(Notification, pk=id)

    if request.method == "POST":
        form = NotificationForm(request.POST, instance=notification)
        if form.is_valid():
            form.save()
            return redirect('add_Notification_page')
    else:
        form = NotificationForm(instance=notification)

    context = {
        "form": form,
        "notification": notification,
    }
    return render(request, "edits/edit_Notification.html", context)   


def delete_Notifications_view(request, id):
    notification = get_object_or_404(Notification, pk=id)
    notification.delete()
    return redirect('add_Notification_page')