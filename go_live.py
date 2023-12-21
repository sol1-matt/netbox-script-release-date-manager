from dcim.models import Device
from virtualization.models import VirtualMachine
from extras.models import CustomField
from dcim.choices import DeviceStatusChoices
from virtualization.choices import VirtualMachineStatusChoices
from extras.scripts import BooleanVar, ChoiceVar, ObjectVar, Script

from datetime import datetime


class GoLive(Script):
    """
    This script looks for a custom date field and changes the status on devices of vm's on that date

    """
    date_custom_field = ObjectVar(
        model=CustomField,
        description="Date Custom Field that contains the date to change the status",
        label='Date Field'
    )

    device_status_current = ChoiceVar(
        choices=[(choice[1], choice[1]) for choice in DeviceStatusChoices.CHOICES],
        description="Find Device Status",
        label='Find Device Status',
    )

    device_status_new = ChoiceVar(
        choices=[(choice[1], choice[1]) for choice in DeviceStatusChoices.CHOICES],
        description="New Device Status",
        label='New Device Status',
    )

    vm_status_current = ChoiceVar(
        choices=[(choice[1], choice[1]) for choice in VirtualMachineStatusChoices.CHOICES],
        description="Find Virtual Machine Status",
        label='Find Virtual Machine Status',
    )

    vm_status_new = ChoiceVar(
        choices=[(choice[1], choice[1]) for choice in VirtualMachineStatusChoices.CHOICES],
        description="New Virtual Machine Status",
        label='New Virtual Machine Status',
    )

    class Meta:
        name = "Go Live"
        description = "Updates device/vm status at a future date"
        commit_default = False

    def run(self, data, commit):

        # Find all devices and virtual machines with a none active status and the date set
        devices = Device.objects.filter(status=data['device_status_current'])
        vms = VirtualMachine.objects.filter(status=data['vm_status_current'])
        if not devices and not vms:
            self.log_success(f"No devices or virtual machines found with status {data['device_status_current']}/{data['vm_status_current']}; ending.")
            return
        self.log_info(f"Found {devices.count()} devices with status {data['device_status_current']}and {vms.count()} virtual machines with status {data['vm_status_current']}.") 
        self.checkStatus(devices, data['device_status_new'], str(data['date_custom_field']), commit)
        self.checkStatus(vms, data['vm_status_new'], str(data['date_custom_field']), commit)

    def checkStatus(self, things, new_status, date_custom_field, commit):
        for thing in things:
            thing_date = thing.custom_field_data.get(date_custom_field)
            self.log_info(f"{thing} - status: {thing.status}, release date: {thing_date}")
            if thing_date is not None:
                if datetime.strptime(thing_date, "%Y-%m-%d").date() <= datetime.today().date():
                    if commit and thing.pk and hasattr(thing, 'snapshot'):
                        thing.snapshot()
                    thing.status = new_status
                    thing.full_clean()
                    thing.save()
                    self.log_success(f"Updated {thing.name} to status {new_status}")