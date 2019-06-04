import time
import json
import logging
from ats import aetest
from genie.utils.timeout import Timeout

### Code replaced by using Verification!
#from genie.utils.diff import Diff
###
from genie.harness.base import Trigger

log = logging.getLogger()

def _get_all_device_info(device):
    response = device.rest.get('/api/v1/network-device')
    all_device_info = response.json()
    return all_device_info['response']

def _get_device_id_name(device, name):
    for device in _get_all_device_info(device):
        if device['hostname'] == name:
            device_id = device['id']
            break
    else:
        raise Exception('Could not find {n}'.format(n=name))
    return device_id

class TriggerUnconfigConfigDescriptionInterface(Trigger):
    '''Config and Unconfig interface description'''

    @aetest.setup
    def prerequisites(self, testbed, uut, steps, interface=None):
        '''Pick one interface and save description'''

        # find one up interface
        with steps.start('Find an interface') as step:
            output = uut.parse('show interfaces')

            if interface:
                self.interface = interface
                self.description = output[interface]['description'].strip()
            else:
                # Pick first interface
                for interface in output:
                    if 'description' in output[interface]:
                        self.description = output[interface]
                        self.interface = interface
                        break
                else:
                    step.failed('Could not find an interface')
            step.passed("Found interface '{i}'".format(i=self.interface))

        with steps.start("Verify '{i}' is also in DNAC".format(i=self.interface)) as step:
            # Make sure it is also in DNAC
            testbed.devices['dnac'].connect(via='rest', alias='rest')
            output = testbed.devices['dnac'].parse('/dna/intent/api/v1/interface', alias='rest')

            # Find the interface
            if output[self.interface]['description'].strip() != self.description:
                step.failed("With cli interface '{i}' is description is '{dc}', "
                            "but with DNAC rest api it is "
                            "'{dd}'".format(i=interface,
                                            dc=self.description,
                                            dd=output[self.interface]['description']))

            step.passed("'{i}' is also in DNAC and have same description "
                        "'{d}'".format(i=self.interface, d=self.description))

    @aetest.test
    def config(self, testbed, uut, steps, description):
        '''Shut interface'''
        with steps.start("Change description of interface '{i}'".format(i=self.interface)) as step:
            uut.configure('''\
interface {i}
description {d}'''.format(i=self.interface, d=description))

            device_id = _get_device_id_name(testbed.devices['dnac'], uut.name)
            testbed.devices['dnac'].rest.put('/dna/intent/api/v1/network-device/sync?forceSync=true',
                                             data=json.dumps([device_id]))

    @aetest.test
    def verify(self, testbed, uut, steps, description, dnac_timeout):
        '''Verify if the change description worked'''
        with steps.start("Verify '{i}' description is now '{d}' via "
                         "cli".format(i=self.interface, d=description)) as step:

            # find one up interface
            output = uut.parse('show interfaces {i}'.format(i=self.interface))

            if output[self.interface]['description'] != description:
                step.failed("'{i}' is expected to be '{d}' but instead is "
                            "'{dc}'".format(i=self.interface,
                                            d=description,
                                            dc=output[self.interface]['description']))
            step.passed("'{i}' description is '{d}' as expected via "
                        "cli".format(i=self.interface,
                                     d=description))


        with steps.start("Verify '{i}' description is now '{d}' via "
                         "DNAC".format(i=self.interface, d=description)) as step:

            # Add timeout as it can take time to update, even though the sync was sent
            timeout = Timeout(max_time = dnac_timeout['max_time'],
                              interval = dnac_timeout['interval'])

            while timeout.iterate():
                # Make sure it is also up in DNAC
                output = testbed.devices['dnac'].parse('/dna/intent/api/v1/interface', alias='rest')

                if output[self.interface]['description'].strip() != description:
                    log.info("DNAC description is '{d}' instead of "
                             "'{dc}".format(d=output[self.interface]['description'].strip(), dc=description))
                    timeout.sleep()
                    continue
                break
            else:
                step.failed("'{i}' is expected to be '{d}' but instead is "
                            "'{dd}'".format(i=self.interface,
                                            d=description,
                                            dd=output[self.interface]['description']))
            step.passed("'{i}' description is '{d}' as expected via "
                        "DNAC".format(i=self.interface,
                                     d=description))

    @aetest.test
    def unconfig(self, testbed, uut, steps):
        '''Revert description'''
        with steps.start("Revert description of interface '{i}'".format(i=self.interface)) as step:
            uut.configure('''\
interface {i}
description {d}'''.format(i=self.interface,
                          d=self.description))
            device_id = _get_device_id_name(testbed.devices['dnac'], uut.name)
            testbed.devices['dnac'].rest.put('/dna/intent/api/v1/network-device/sync?forceSync=true',
                                             data=json.dumps([device_id]))

    @aetest.test
    def verify_recover(self, testbed, uut, steps, dnac_timeout):
        '''Figure out if interface description is reverted'''
        with steps.start("Verify '{i}' description is now '{d}' via "
                         "cli".format(i=self.interface, d=self.description)) as step:

            # find one up interface
            output = uut.parse('show interfaces {i}'.format(i=self.interface))

            if output[self.interface]['description'] != self.description:
                step.failed("'{i}' is expected to be '{d}' but instead is "
                            "'{dc}'".format(i=self.interface,
                                            d=self.description,
                                            dc=output[self.interface]['description']))
            step.passed("'{i}' description is '{d}' as expected via "
                        "cli".format(i=self.interface,
                                     d=self.description))


        with steps.start("Verify '{i}' description is now '{d}' via "
                         "DNAC".format(i=self.interface, d=self.description)) as step:

            # Add timeout as it can take time to update, even though the sync was sent
            timeout = Timeout(max_time = dnac_timeout['max_time'],
                              interval = dnac_timeout['interval'])

            while timeout.iterate():
                # Make sure it is also up in DNAC
                output = testbed.devices['dnac'].parse('/dna/intent/api/v1/interface', alias='rest')

                if output[self.interface]['description'].strip() != self.description:
                    timeout.sleep()
                    continue
                break
            else:
                step.failed("'{i}' is expected to be '{d}' but instead is "
                            "'{dd}'".format(i=self.interface,
                                            d=self.description,
                                            dd=output[self.interface]['description']))
            step.passed("'{i}' description is '{d}' as expected via "
                        "DNAC".format(i=self.interface,
                                     d=self.description))


class TriggerShutNoShutInterface(Trigger):
    '''Shut and unshut bgp'''

    @aetest.setup
    def prerequisites(self, testbed, uut, steps, interface=None):
        '''Figure out if bgp is configured and up'''

        # find one up interface
        with steps.start('Find an up interface') as step:
            output = uut.parse('show interfaces')

            if interface:
                self.interface = interface
            else:
                for interface in output:
                    if output[interface]['oper_status'] == 'up':
                        # found one
                        self.interface = interface
                        break
                else:
                    step.failed('Could not find an up interface')
            step.passed("Found interface '{i}'".format(i=self.interface))

        with steps.start("Verify '{i}' is also up in DNAC".format(i=self.interface)) as step:
            # Make sure it is also up in DNAC
            testbed.devices['dnac'].connect(via='rest', alias='rest')
            output = testbed.devices['dnac'].parse('/dna/intent/api/v1/interface', alias='rest')

            # Find the interface
            if output[self.interface]['status'] != 'up':
                step.failed("With cli interface '{i}' is up, "
                            "but with DNAC rest api it is of "
                            "state '{s}'".format(i=interface,
                                                 s=output[self.interface]['status']))
            step.passed("'{i}' is also up in DNAC".format(i=self.interface))

    @aetest.test
    def shut(self, uut, steps):
        '''Shut interface'''
        with steps.start("Shut '{i}'".format(i=self.interface)) as step:
            uut.configure('''\
interface {i}
shutdown'''.format(i=self.interface))

    @aetest.test
    def verify(self, testbed, uut, steps):
        '''Verify if the shut worked'''
        with steps.start("Verify '{i}' is down via "
                         "cli".format(i=self.interface)) as step:

            # find one up interface
            output = uut.parse('show interfaces {i}'.format(i=self.interface))

            if output[self.interface]['oper_status'] != 'down':
                step.failed("'{i}' is expected to be down but instead is "
                            "'{s}'".format(i=self.interface,
                                           s=output[interface]['oper_status']))
            step.passed("'{i}' is down as expected via cli".format(i=self.interface))


        with steps.start("Verify '{i}' is also down in DNAC".format(i=self.interface)) as step:
            # Make sure it is also up in DNAC
            output = testbed.devices['dnac'].parse('/dna/intent/api/v1/interface', alias='rest')

            # Find the interface
            if output[interface]['status'] != 'down':
                    step.failed("'{i}' is expected to be down but instead is "
                                "'{s}'".format(i=self.interface,
                                               s=output[interface]['status']))
            step.passed("'{i}' is down as expected via DNAC".format(i=self.interface))

    @aetest.test
    def unshut(self, uut, steps):
        '''Shut bgp'''
        with steps.start("Unshut '{i}'".format(i=self.interface)) as step:
            uut.configure('''\
interface {i}
no shutdown'''.format(i=self.interface))

    @aetest.test
    def verify_recover(self, testbed, uut, steps, wait_time=20):
        '''Figure out if interface is configured and up'''
        with steps.start("Verify '{i}' is up via "
                         "cli".format(i=self.interface)) as step:

            # find one up interface
            output = uut.parse('show interfaces {i}'.format(i=self.interface))

            if output[self.interface]['oper_status'] != 'up':
                step.failed("'{i}' is expected to be up but instead is "
                            "'{s}'".format(i=self.interface,
                                           s=output[interface]['oper_status']))
            step.passed("'{i}' is up as expected via cli".format(i=self.interface))


        with steps.start("Verify '{i}' is also up in DNAC".format(i=self.interface)) as step:
            # Make sure it is also up in DNAC
            output = testbed.devices['dnac'].parse('/dna/intent/api/v1/interface', alias='rest')

            # Find the interface
            if output[self.interface]['status'] != 'up':
                    step.failed("'{i}' is expected to be up but instead is "
                                "'{s}'".format(i=self.interface,
                                               s=output[interface]['status']))
            step.passed("'{i}' is up as expected via DNAC".format(i=self.interface))
