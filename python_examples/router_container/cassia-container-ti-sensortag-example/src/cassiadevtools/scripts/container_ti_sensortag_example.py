from cassiadevtools import cassia_api
import shutil
import os
import warnings
import click
import sys


# Data file size limits are in bytes.
SIZE_100KB = 100000
SIZE_500KB = 500000
SIZE_1MB = 1000000
SIZE_10MB = 10000000
SIZE_100MB = 100000000
SIZE_500MB = 500000000

DATA_FILE_SIZE_LIMIT = SIZE_10MB
MAX_USED_STORAGE_RATIO = 0.7


@click.command()
@click.option('--data-file-count', default=1, 
              help='Number of data files to generate.')
def main(data_file_count):
    total, used, free = shutil.disk_usage("/")
    data_file_num = 1
    data_dir_path = '../data'
    cur_data_file_count = 0

    try:
        os.mkdir(data_dir_path)
    except FileExistsError as e:
        pass
    except Exception as e:
        print(e)
        exit()

    while (os.path.isfile(data_dir_path + 
           '/data{count}.txt'.format(count=data_file_num))):
        data_file_num += 1

    if data_file_num == 1:
        file_str = (
            '{path}/data{count}.txt'.format(path=data_dir_path, 
                                            count=data_file_num))        
        with open(file_str,'x'):
                print('Created data file: {}'.format(file_str))
    else:
        data_file_num -= 1

    while cur_data_file_count < data_file_count:
        if used < total * MAX_USED_STORAGE_RATIO:
            data = 'hiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii'

            if (sys.getsizeof(data) + os.path.getsize(
                '{path}/data{count}.txt'.format(
                    path=data_dir_path,
                    count=data_file_num)) >= DATA_FILE_SIZE_LIMIT):

                data_file_num += 1
                file_str = (
                    '{path}/data{count}.txt'.format(path=data_dir_path, 
                                                    count=data_file_num))
                with open(file_str,'x'):
                    print('Created data file: {}'.format(file_str))

                cur_data_file_count += 1

            file_str = (
                '{path}/data{count}.txt'.format(path=data_dir_path, 
                                                count=data_file_num))

            with open(file_str, 'a') as data_file:
                data_file.write(data)
        else:
            warnings.warn(
                ('Storage is {}"%" used! Data files cannot be created until '
                 'space is freed.').format(MAX_USED_STORAGE_RATIO * 100),
                ResourceWarning)


if __name__ == '__main__':
    main()
