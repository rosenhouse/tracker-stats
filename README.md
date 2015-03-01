**Get hours-worked vs. estimated points for your tracker stories.**




1. Get [your Tracker API token](https://www.pivotaltracker.com/profile)

2. Get a project ID, i.e. `https://www.pivotaltracker.com/n/projects/NUMBER`

3. Install dependencies
  ```bash
  pip install --upgrade pytz requests
  ```
  
4. Set env vars
  ```bash
  export TRACKER_API_TOKEN=0123456789abcdef
  export PROJECT_ID=0123456
  ```

5. Run it:
  ```bash
  ./stats.py
  ```
