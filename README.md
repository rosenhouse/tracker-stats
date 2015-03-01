**Get hours-worked vs. estimated points for your tracker stories.**




1. Get [your Tracker API token](https://www.pivotaltracker.com/profile)

2. Get a project ID, the number at the end of your project page URL

3. Install dependencies
  ```bash
  pip install pytz requests
  ```

4. Run it
  ```
$ ./stats.py -h
usage: stats.py [-h] [--timezone TIMEZONE] token project

collect some stats for a Tracker Project

positional arguments:
  token                API token for Pivotal Tracker
  project              Project ID to collect stats on

optional arguments:
  -h, --help           show this help message and exit
  --timezone TIMEZONE  Timezone, e.g. US/Pacific
  ```
