import os
import ssl
import sys
import time
import shutil
import threading
from queue import Queue
import certifi


from moodle_dl.utils.logger import Log
from moodle_dl.state_recorder.course import Course, File
from moodle_dl.download_service.path_tools import PathTools
from moodle_dl.download_service.url_target import URLTarget
from moodle_dl.download_service.downloader import Downloader
from moodle_dl.moodle_connector.moodle_service import MoodleService


class DownloadService:
    """
    DownloadService manages the queue of files to be downloaded and starts
    the Downloader threads which download all URLTargets.
    Furthermore DownloadService is responsible for logging live information
    and errors.
    """

    def __init__(
        self, courses: [Course], moodle_service: MoodleService, storage_path: str, skip_cert_verify: bool = False
    ):
        """
        Initiates the DownloadService with all files that
        need to be downloaded. A URLTarget is created for each file.
        @param courses: A list of courses that contains all modified files.
        @param moodle_service: A reference to the moodle_service, currently
                               only to get to the state_recorder and the token.
        @param storage_path: The location where the files will be saved.
        """

        # How much threads should be created
        DownloadService.thread_count = 5
        if 'pydevd' in sys.modules:
            # if debugging only one thread should be started
            DownloadService.thread_count = 1

        self.courses = courses
        self.state_recorder = moodle_service.recorder
        self.token = moodle_service.config_helper.get_token()
        self.storage_path = storage_path

        # The wait queue for all URL targets to be downloaded.
        self.queue = Queue(0)
        # A list of the created threads
        self.threads = []
        # A lock to stabilize thread insecure resources.
        # writing in DB
        self.db_lock = threading.Lock()
        # reading file system
        self.fs_lock = threading.Lock()

        # Sets the download options
        self.options = moodle_service.config_helper.get_download_options()

        # report is used to collect successful and failed downloads
        self.report = {'success': [], 'failure': []}
        # thread_report is used to get live reports from the threads
        self.thread_report = [
            {'total': 0, 'percentage': 0, 'old_extra_totalsize': None, 'extra_totalsize': None, 'current_url': ''}
            for i in range(self.thread_count)
        ]
        # Collects the total size of the files that needs to be downloaded.
        self.total_to_download = 0
        self.total_files = 0

        # delete files, that should be deleted
        self.state_recorder.batch_delete_files(self.courses)

        if skip_cert_verify:
            self.ssl_context = ssl._create_unverified_context()
        else:
            self.ssl_context = ssl.create_default_context(cafile=certifi.where())

        # Prepopulate queue with any files that were given
        for course in self.courses:
            for file in course.files:
                if file.deleted is False:
                    self.total_to_download += file.content_filesize

                    save_destination = self.gen_path(self.storage_path, course, file)

                    self.queue.put(
                        URLTarget(
                            file,
                            course,
                            save_destination,
                            self.token,
                            self.thread_report,
                            self.fs_lock,
                            self.ssl_context,
                            self.options,
                        )
                    )

                    self.total_files += 1

    @staticmethod
    def gen_path(storage_path: str, course: Course, file: File):
        """
        Generates the directory path where a file should be stored
        """
        course_name = course.fullname
        if course.overwrite_name_with is not None:
            course_name = course.overwrite_name_with

        # if a flat path is requested
        if not course.create_directory_structure:
            return PathTools.flat_path_of_file(storage_path, course_name, file.content_filepath)

        # If the file is located in a folder or in an assignment,
        # it should be saved in a sub-folder
        # (with the name of the module).
        if file.module_modname in ['assign', 'folder', 'data']:
            file_path = file.content_filepath
            if file.content_type == 'submission_file':
                file_path = os.path.join('/submissions/', file_path.strip('/'))

            return PathTools.path_of_file_in_module(
                storage_path, course_name, file.section_name, file.module_name, file_path
            )
        else:
            return PathTools.path_of_file(storage_path, course_name, file.section_name, file.content_filepath)

    def run(self):
        """
        Starts all threads to download the files and
        issues status messages at regular intervals.
        """
        self._create_downloader_threads()

        print('\n' * (len(self.threads)), end='')
        old_status_message = ''
        while not self._downloader_complete():
            time.sleep(0.1)

            new_status_message = self._get_status_message()
            if old_status_message != new_status_message:
                print(new_status_message, end='')
                old_status_message = new_status_message

        self._clear_status_message()
        self._log_failures()

    def _create_downloader_threads(self):
        """
        Creates all downloader threads, initiates them
        with the queue and starts them.
        """
        for i in range(self.thread_count):
            thread = Downloader(self.queue, self.report, self.state_recorder, i, self.db_lock)
            thread.start()
            self.threads.append(thread)

    def _downloader_complete(self) -> bool:
        """
        Checks if a thread is still running, if so then the downloaders
        are not finished yet.
        @return: status of the downloaders
        """
        fininshed_downlaoding = True
        for thread in self.threads:
            if thread.is_alive():
                fininshed_downlaoding = False
                break
        return fininshed_downlaoding

    def _get_status_message(self) -> str:
        """
        Creates a string that combines the status messages of all threads.
        The current download progress of a file is displayed in percent
        per Thread.
        A total display is also created, showing the total amount downloaded
        in relation to what still needs to be downloaded.
        @return: A status message string
        """

        # to limit the output to one line
        limits = shutil.get_terminal_size()

        # Starting with a carriage return to overwrite the last message
        progressmessage = f'\033[{len(self.threads)}A\r'

        threads_status_message = ''
        threads_total_downloaded = 0
        add_empty_line = 0
        for thread in self.threads:
            if not thread.is_alive():
                add_empty_line += 1
                continue

            i = thread.thread_id
            # A thread status contains it id and the progress
            # of the current file
            thread_percentage = self.thread_report[i]['percentage']
            thread_current_url = self.thread_report[i]['current_url']
            if len(thread_current_url) + 13 > limits.columns:
                thread_current_url = thread_current_url[0 : limits.columns - 15] + '..'

            threads_status_message += '\033[KT%2i: %3i%% - %s\n' % (i, thread_percentage, thread_current_url)

            threads_total_downloaded += self.thread_report[i]['total']

            extra_totalsize = self.thread_report[i]['extra_totalsize']
            if extra_totalsize is not None and extra_totalsize != -1:
                self.total_to_download += extra_totalsize
                self.thread_report[i]['extra_totalsize'] = -1

        for i in range(add_empty_line):
            threads_status_message += '\033[K\n'

        progressmessage += threads_status_message

        percentage = 100
        if self.total_to_download != 0:
            percentage = int(threads_total_downloaded * 100 / self.total_to_download)

        # The overall progress also includes the total size that needs to be
        # downloaded and the size that has already been downloaded.
        progressmessage_line = 'Total: %3s%% %12s/%12skb' % (
            percentage,
            int(threads_total_downloaded / 1000.0),
            int(self.total_to_download / 1000.0),
        )

        progressmessage_line += ' | Files: %5s/%5s' % (len(self.report['success']), self.total_files)

        if len(progressmessage_line) > limits.columns:
            progressmessage_line = progressmessage_line[0 : limits.columns]
        progressmessage_line = '\033[K' + progressmessage_line

        progressmessage += progressmessage_line

        return progressmessage

    def _clear_status_message(self):
        print(f'\033[{len(self.threads)}A', end='')

        print('\033[K\n' * (len(self.threads)), end='')
        print('\033[K', end='')

        print(f'\033[{len(self.threads)}A', end='')

    def _log_failures(self):
        """
        Logs errors if any have occurred.
        """
        print('')
        if len(self.report['failure']) > 0:
            Log.warning('Error while trying to download files, look at the log for more details.')

        for url_target in self.report['failure']:
            Log.error('%s\t%s' % (url_target.file.content_filename, url_target.error))
