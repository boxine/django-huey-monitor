import logging
import os


logger = logging.getLogger(__name__)


def generate_filelist(path):
    logger.info('Scan filesystem "%s"...', path)

    def scan_filesystem(path):
        for entry in os.scandir(path):
            try:
                if entry.is_dir(follow_symlinks=False):
                    yield from scan_filesystem(entry)
                elif entry.is_file(follow_symlinks=False):
                    yield entry.path
            except OSError as err:
                logger.exception('Error with %s: %s', entry, err)
                continue

    file_list = list(scan_filesystem(path))
    return file_list
