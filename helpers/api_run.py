#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import argparse
import requests

# Demo info
demo_id = 77777000125

def run_demo_with_uploaded_image(demo_id, blobs):
    """
    Run demo with a given image input
    """

    params = {'demo_id': demo_id,
                'origin': 'upload',
                'params': {},
                }

    # Blob/s to use on execution
    files = {'file_0': blobs[0], 'file_1': blobs[1]}
    response = post('core', 'run', data={"clientData": json.dumps(params)}, files=files)
    return response.json()

# Post helper
def post(module, service, params=None, data=None, files=None, servicejson=None):
    '''
    HTTP Post helper
    '''
    url = f'https://ipolcore.ipol.im/api/{module}/{service}'
    return requests.post(url, params=params, data=data, files=files, json=servicejson)


# Help explanation
parser=argparse.ArgumentParser(
    description='''This script runs demo 77777000125 which has no parameters 
    and  requires the path to two images as inputs. These paths should be given 
    as parameters.
    IE: ./demo_run.py input1.jpe input2.jpe
    ''')
parser.add_argument('image_1', help='First input for the demo')
parser.add_argument('image_2', help='Second input for the demo')
# parser.print_help()
args = parser.parse_args()


with open(args.image_1, 'rb') as blob1, open(args.image_2, 'rb') as blob2:
    # Run demo code
    run_response = run_demo_with_uploaded_image(demo_id, [blob1, blob2])

# Status OK or KO will indicate if execution finished succesfully or not
assert run_response['status'] == 'OK', "Execution failure. Please check stderr.txt"

# Resulting paths for images and txt file
print(f'First input: https://ipolcore.ipol.im/{run_response["work_url"]}input_0.png')
print(f'Second input: https://ipolcore.ipol.im/{run_response["work_url"]}input_1.png')
print(f'First registered: https://ipolcore.ipol.im/{run_response["work_url"]}output_0.png')
print(f'Second registered: https://ipolcore.ipol.im/{run_response["work_url"]}output_1.png')
print(f'Panorama: https://ipolcore.ipol.im/{run_response["work_url"]}pano.jpg')
print(f'Output: https://ipolcore.ipol.im/{run_response["work_url"]}stdout.txt')