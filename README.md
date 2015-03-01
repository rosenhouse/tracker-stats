**Compare hours-worked vs. estimated points for your tracker stories.**

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

compare hours worked to points estimated

positional arguments:
  token                API token for Pivotal Tracker
  project              Project ID to collect stats on

optional arguments:
  -h, --help           show this help message and exit
  --timezone TIMEZONE  Timezone, e.g. US/Pacific
  ```
  
  ```bash
  $ ./stats.py $API_TOKEN $PROJECT_ID
  story_id	estimate	duration
  78141812	1	2.67
  78157350	2	11.50
  78115996	1	7.67
  78139714	1	2.00
  78139766	1	0.17
  79213260	1	0.33
  79133164	1	3.67
  ...
  ```
