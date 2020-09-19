from cassiatidemo import cassia_api
import shutil
import os
import warnings

DATA_FILE_SIZE_LIMIT = 524288000  # 524288000 Bytes or 500 MB.
MAX_USED_STORAGE_RATIO = 0.7

total, used, free = shutil.disk_usage("/")
data_file_num = 1
data_dir_path = '../../data'

#try:
#    os.mkdir(data_dir_path)
#except FileExistsError as e:

while os.path.isfile(data_dir_path + '/data{count}.txt'.format(count=data_file_num)):
    data_file_num += 1

data_file_num -= 1

if used < total * MAX_USED_STORAGE_RATIO:
    if data_file_num == 0:
        data_file_num += 1
        file_str = (
            '{path}/data{count}.txt'.format(path=data_dir_path, 
                                            count=data_file_num))        
        with open(file_str,'x'):
                print('Created data file: {}'.format(file_str))

    elif (os.path.getsize('{path}/data{count}.txt'
                          .format(path=data_dir_path,
                                  count=data_file_num)) > DATA_FILE_SIZE_LIMIT):
        data_file_num += 1
        file_str = (
            '{path}/data{count}.txt'.format(path=data_dir_path, 
                                            count=data_file_num))
        with open(file_str,'x'):
            print('Created data file: {}'.format(file_str))

    file_str = (
        '{path}/data{count}.txt'.format(path=data_dir_path, 
                                        count=data_file_num))
    with open(file_str, 'a') as data_file:
        data_file.write('TEST')
else:
    warnings.warn(('Storage is {}"%" used! Data files cannot be created until' 
                   'space is freed.').format(MAX_USED_STORAGE_RATIO * 100),
                                             ResourceWarning)
    
#if used < total * 0.7:  # Make sure we still have at 30% usable storage.
#    with open('data/data{count}.txt'.format(count=data_file_num), 'a'):
