# Moodle Downloader 2

> Because manually downloading all the course files every few days is just ~~way too easy~~ inefficient.


### Features
- Watch your Moodle account for any added or changed files in your enrolled courses.
- Optionally get notified via mail or [Telegram](https://telegram.org/apps) about these changes.
- Save yourself precious time through all these nice features.
- Do not miss any files, if files are deleted online, they are still available offline.


### Setup
1. Install [Python](https://www.python.org/) >=3.7
2. Install [ffmpeg](http://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/)
3. Run `pip install moodle-dl`  
    <sup>(To upgrade from an older Version use `pip install -U moodle-dl` instead)</sup>
4. Run `moodle-dl --init` in the desired download directory.


If you run the program on **Windows**, please use [Powershell or CMD](https://www.isunshare.com/windows-10/5-ways-to-open-windows-powershell-in-windows-10.html). Please do not use a mintty like MINGW or similar.

<sup>[Click here for an alternative setup with Docker](https://github.com/C0D3D3V/Moodle-Downloader-2/wiki/Run-with-Docker)</sup>



### Usage
- `moodle-dl`
    - Fetches the current state of your Moodle Account, saves it and detects any changes.
    - If configured, it also sends out a mail-notification.
    - It prints the current status into the console 
	- It writes a more detailed log into `MoodleDownloader.log` for debug purpose.
- `moodle-dl --init`
    - Guides you trough the configuration of the software, including the activation of notifications and obtainment of a login-token for your Moodle-Account.
    - After the necessary configuration, further additional configurations can be made. 
	- It does not fetch the current state of your Moodle-Account.
    - If you have to log in with Single Sign On (SSO), you can set the option `--sso` additionally.
- `moodle-dl --config`
    - Guides you through the additional configuration of the software.
    - This includes the selection of the courses to be downloaded and various configuration options for these courses.
    - You can rename each course individually and decide if a folder structure should be created.
    - You can set whether submissions (files uploaded to Assignments by yourself or a teacher) should be downloaded.
    - You can choose to download descriptions of Moodle courses. 
    - You can choose to download databases of Moodle courses. 
    - You can set if external linked files should be downloaded (files like youtube videos).
    - It does not fetch the current state of your Moodle-Account.
- `moodle-dl --new-token`
    - Overrides the login-token with a newly obtained one.
    - It does not fetch the current state of your Moodle-Account.
    - Use it if at any point in time, for whatever reason, the saved token gets rejected by Moodle.
    - It does not affect the rest of the config.
    - It prints all information into the console.
- `moodle-dl --change-notification-mail`
    - Activate/deactivate/change the settings for receiving notifications via e-mail.
    - It does not affect the rest of the config.
    - It prints all information into the console.
- `moodle-dl --change-notification-telegram`
    - Activate/deactivate/change the settings for receiving notifications via Telegram.
    - It does not affect the rest of the config.
    - It prints all information into the console.
    - Help with setting up Notifications via Telegram will be here soon
- `moodle-dl --manage-database`
    - To manage the offline database.
    - It allows you to delete entries from the database that are no longer available locally so that they can be downloaded again.
- `moodle-dl --version`
    - Print program version and exit

### Options
Options can be combined with all the actions mentioned above.
- `--path PATH`
    - This option can be useful if you want to save the downloaded files in a directory other than the current working directory (the directory where you run the script). 
    - Sets the location of the configuration, logs and downloaded files. 
    - `PATH` must be an existing directory in which you have read and write access.
    - Default: current working directory

- `--verbose`
    - Print various debugging information
  
- `--skip-cert-verify`
    - This flag is used to skip the certification verification while sending requests to Moodle.
    - Warning: This might lead to security flaws and should only be used in non-production environments.
    - Default: False

- `--without-downloading-files`
    - This flag is used to skip the downloading of files.
    - This allows the local database to be updated to the latest version of Moodle without having to download all files.

- `--sso`
    - This flag is used to indicate that a Single Sign On (SSO) login to your Moodle is required. 
    - Can be combined with `--init` and `--new-token`.

- `--log-responses`
    - If this flag is set, a `responses.log` file is created in which all JSON responses from Moodles are logged along with the requested URL
    - This is for development and debugging purposes only. The log file may contain private data.




### Notes
- Use a separate E-Mail - Account for sending out the notifications, as its login data is saved in cleartext.
- The Login-Information for your Moodle-Account is secure, it isn't saved in any way. Only a Login-Token is saved.
- Your Moodle token is stored in the configuration file (`config.json`). Be careful that no unauthorized person reads this file, especially the token must not be given to an unauthorized person, this can cause a lot of trouble.
- The `privatetoken` can be used to create a cookie for your Moodle account. A Cookie is what is used to tell Moodle that you are logged in. The `cookie.txt` always keeps a valid cookie for you, take great care of this file, if it falls into the wrong hands someone can take over your entire Moodle account. This feature is only important for Moodles with plugins installed that are not supported by the Moodle app. If you do not want to generate cookies, remove the `privatetoken` from the `config.json`.

---


### Contributing
I'm open for all forks, feedback and Pull Requests ;)

I am happy about every contribution to the project. 
Because my studies are slowly coming to an end, I am looking for a new Contributor/Maintainer for this project. So if someone is interested in continuing the project or adding a lot new features, please feel free to contact me by mail. 

### License
This project is licensed under the terms of the *GNU General Public License v3.0*. For further information, please look [here](http://choosealicense.com/licenses/gpl-3.0/) or [here<sup>(DE)</sup>](http://www.gnu.org/licenses/gpl-3.0.de.html).

To mention here is, that this project is based on a project from [LucaVazz](https://github.com/LucaVazz/DualisWatcher). He did a very great job creating a "DualisWatcher".  
