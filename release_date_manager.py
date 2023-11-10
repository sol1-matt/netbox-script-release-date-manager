from dcim.models import Device
from virtualization.models import VirtualMachine
from extras.models import CustomField
from dcim.choices import DeviceStatusChoices
from extras.scripts import BooleanVar, ChoiceVar, ObjectVar, Script

from datetime import datetime


class ReleaseDateStatusManager(Script):
    """
    This script looks for a custom date field and changes the status on devices of vm's on that date

    """
    date_custom_field = ObjectVar(
        model=CustomField,
        description="Date Custom Field that contains the date to change the status",
        label='Date Field'
    )


    class Meta:
        name = "Release Date Manager"
        description = "Updates device/vm status at a future date"
        commit_default = False

    def run(self, data, commit):

        current_status=DeviceStatusChoices.STATUS_STAGED
        new_status=DeviceStatusChoices.STATUS_ACTIVE

        # Find all devices and virtual machines with a none active status and the date set
        devices = Device.objects.filter(status=current_status)
        vms = VirtualMachine.objects.filter(status=current_status)
        if not devices and not vms:
            self.log_success(f"No devices of virtual machines found with status {current_status}; ending.")
            return
        self.log_info(f"Found {devices.count()} devices and {vms.count()} virtual machines with status {current_status}.") 
        self.checkStatus(devices, new_status)
        self.checkStatus(vms, new_status)

    def checkStatus(self, things, new_status):
        for thing in things:
            self.log_info(thing)
            thing_date = thing.custom_fields.get(self.date_custom_field, None)
            if thing_date is not None:
                if datetime.strptime(thing_date, "%Y-%m-%d").date() <= datetime.today().date():
                    thing.status = new_status
                    thing.save()
                    self.log_success(f"Updated {thing.name} to status {new_status}")