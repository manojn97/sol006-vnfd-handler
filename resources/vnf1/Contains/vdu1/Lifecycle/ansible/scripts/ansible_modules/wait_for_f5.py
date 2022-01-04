#!/usr/bin/python


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'jochenkappel'
}

DOCUMENTATION = '''
---
to be done
---
'''

EXAMPLES = '''
#to be done
'''

RETURN = '''
to be done
'''

from ansible.module_utils.basic import AnsibleModule
import requests
import time

def run_module():
    module_args = dict(
        device_ip=dict(type='str', required=True),
        sleep=dict(type='str', default=10),
        timeout=dict(type='str', default=300)
    )

    result = dict(
        changed=False,
        access_ok=False
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    timeout = int(module.params['timeout'])
    waittime = int(module.params['sleep'])
    # poll device page until we get 200 OK
    while timeout > 0:
        r = requests.get('https://' + module.params['device_ip'] + '/tmui/login.jsp',
            verify=False )

        if r.status_code == 200:
            result['access_ok'] = True
            result['changed'] = True
            break

        timeout = timeout - waittime
        time.sleep( waittime )


    if result['access_ok']:
        module.exit_json(**result)
    else:
        module.fail_json(msg='Device page does not respond', **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
